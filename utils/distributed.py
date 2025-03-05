import os
import time
import torch
import pickle
import subprocess

import torch.distributed as dist


def apply_distributed(opt):
    if opt['rank'] == 0:
        hostname_cmd = ["hostname -I"]
        result = subprocess.check_output(hostname_cmd, shell=True)
        master_address = result.decode('utf-8').split()[0]
        master_port = opt['PORT']
    else:
        master_address = None
        master_port = None

    master_address = dist.broadcast(master_address, 0)
    master_port = dist.broadcast(master_port, 0)

    if torch.distributed.is_available() and opt['world_size'] > 1:
        init_method_url = 'tcp://{}:{}'.format(master_address, master_port)
        backend = 'nccl'
        world_size = opt['world_size']
        rank = opt['rank']
        torch.distributed.init_process_group(backend=backend,
                                             init_method=init_method_url,
                                             world_size=world_size,
                                             rank=rank)

def init_distributed(opt):
    opt['CUDA'] = opt.get('CUDA', True) and torch.cuda.is_available()
    if 'OMPI_COMM_WORLD_SIZE' not in os.environ:
        # application was started without MPI
        # default to single node with single process
        opt['env_info'] = 'no MPI'
        opt['world_size'] = 1
        opt['local_size'] = 1
        opt['rank'] = 0
        opt['local_rank'] = 0
        opt['master_address'] = '127.0.0.1'
        opt['master_port'] = '8673'
    else:
        # application was started with MPI
        # get MPI parameters
        opt['world_size'] = int(os.environ['OMPI_COMM_WORLD_SIZE'])
        opt['local_size'] = int(os.environ['OMPI_COMM_WORLD_LOCAL_SIZE'])
        opt['rank'] = int(os.environ['OMPI_COMM_WORLD_RANK'])
        opt['local_rank'] = int(os.environ['OMPI_COMM_WORLD_LOCAL_RANK'])

    # set up device
    if not opt['CUDA']:
        assert opt['world_size'] == 1, 'multi-GPU training without CUDA is not supported since we use NCCL as communication backend'
        opt['device'] = torch.device("cpu")
    else:
        torch.cuda.set_device(opt['local_rank'])
        opt['device'] = torch.device("cuda", opt['local_rank'])

    apply_distributed(opt)
    return opt

def is_dist_avail_and_initialized():
    if not dist.is_available():
        return False
    if not dist.is_initialized():
        return False
    return True

def get_world_size():
    if not is_dist_avail_and_initialized():
        return 1
    return dist.get_world_size()

def get_rank():
    if not is_dist_avail_and_initialized():
        return 0
    return dist.get_rank()

def is_main_process():
    return get_rank() == 0

def synchronize():
    """
    Helper function to synchronize between processes when using distributed training
    """
    if not is_dist_avail_and_initialized():
        return
    world_size = dist.get_world_size()
    if world_size == 1:
        return
    dist.barrier()