# Baseline Solution - Track 2: Open-Vocabulary Segmentation with Text-Prompt (LPCVC 2025)

## :fire: News
- [2025.02.01] Sample solution of Track2: OVSeg is released
- [2025.01.10] LPCVC 2025 is accepted as CVPR 2025 Workshop
- [2024.12.10] LPCVC 2025 is announced on NeurIPS 2024

### 1. Model Training and Evaluation
***\*Please refer to [[XDecoder]]() instructions for more details about model training evaluation.***
- Training data: COCO and RefCOCO
- Evaluation data: RefCOCOg
- Finetuned model weights for LPCVC Track2: [[Google Drive]](https://drive.google.com/file/d/1zTaVW_I4fe6MSBq5GAg284TuQfLcB0Yd/view?usp=drive_link)

### 2. Compiling and Profiling on Qualcomm Chips via AI Hub
***\* Please refer to [[AI Hub]]() documents for more details regarding model compiling, profiling, and inference.***


### 3. Inference and Evaluation
***\* Please check the scripts [[.evaluate_model.py]]() more details of inference the on AIHub***
- **Device**: Snapdragon X Elite QRD
- **Test Details**: During inference and evaluate all submitted solutions on AIHub, we prepare all input data and ground-truth to the same format and size to make it fair to all participants. Specifically,
  - **Input**: 
    - Image: RGB, shape=3x1024x1024 # resize the longest edge to 1024, then padded to 1024x1024 square
    - Text: embedding, shape=1x77 # output of openai-clip tokenizer
  - **Output**: 
    - Mask prediction: binary matrix, shape=1x1024x1024 # used to calculate the IoU with ground-truth mask
- **Evaluation Metric**
  - mIoU: IoU of all test samples
    ```python
    def computeIoU(pred_seg, gd_seg):
        I = (pred_seg & gd_seg)
        U = (pred_seg | gd_seg)
        return I, U
    # compute mIoU over all test image-text pairs
    pred = output['grounding_mask'].sigmoid() > 0.5
    gt = input['groundings']['masks'].bool()
    bsi = len(pred)
    I, U = self.computeIoU(pred, gt)
    IoU = I.reshape(bsi,-1).sum(-1)*1.0 / (U.reshape(bsi,-1).sum(-1) + 1e-6)
    self.mIoU += IoU.sum().cpu()
    ```
- **Test Data Format**:
  Every image and a text description will be input to the model after the following preparation operations to make the input format fixed. The corresponding mask of the text description is the ground-truth. 
  - **Image**: We have 1000 images from around 200 categories, and each image is annotated with 3~5 masks of objects/stuff with various sizes and classes. We tried our best to make the test dataset balanced across mask sizes, categories, and more.
    ```python
    image = utils.read_image(img_path, format='RGB')
    transform = []
    transform.extend([T.ResizeShortestEdge(1024, max_size=1024),])    
    image, _ = T.apply_transform_gens(transform, image)
    pad_image = numpy.zeros((1024, 1024, 3), numpy.uint8)
    pad_image[:image.shape[0], :image.shape[1]] = image
    pad_image = torch.as_tensor(numpy.ascontiguousarray(pad_image.transpose(2, 0, 1))).cuda()
    input_iamge = torch.unsqueeze(pad_image, 0)
    ```
  - **Text**: Each annotated mask is assigned 3~5 text descriptions. The textual descriptions include keywords, short phrases, long sentences describing the appearance, location, spatial relationships, or semantic knowledge of the target objects/stuff.
  - *Text tokenization*: QNN library does not support tokneization of text input yet. In order to reduce the influence of different text tokenzer used to the final performance, accuracy and latency, we pre-fixed the text tokenzier as below:
    ```python
    # prefixed text tokenizer
    from transformers import CLIPTokenizer
    os.environ['TOKENIZERS_PARALLELISM'] = 'true'
    pretrained_tokenizer = 'openai/clip-vit-base-patch32'
    tokenizer = CLIPTokenizer.from_pretrained(pretrained_tokenizer)
    tokenizer.add_special_tokens({'cls_token': tokenizer.eos_token})

    # example tokenized text embedding input to the model
    tokens = tokenizer(text, padding='max_length', truncation=True, max_length=max_token_num, return_tensors='pt')
    text_emb = tokens['input_ids'].cuda()
    text_attn_mask = tokens['attention_mask'].cuda()
    input_text = [text_emb, text_attn_mask]
    ```

## Acknowledgement
* The baseline is built on top of [XDecoder]()

## Contact
LPCVC 2025 Organizers: [[Homepage]](lpcv.ai)