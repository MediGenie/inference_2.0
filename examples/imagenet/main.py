import timm
import torch
from PIL import Image
from timm.data import resolve_data_config
from timm.data.transforms_factory import create_transform


def load():
    global model, transform, labels, top_k

    # Load from Hub 🔥
    model = timm.create_model(
        'hf-hub:nateraw/resnet50-oxford-iiit-pet',
        pretrained=True
    )

    # Set model to eval mode for inference
    model.eval()

    # Create Transform
    transform = create_transform(**resolve_data_config(model.pretrained_cfg, model=model))

    # Get the labels from the model config
    labels = model.pretrained_cfg['label_names']
    top_k = min(len(labels), 5)


def preprocess(argument_path: str):
    # Use your own image file here...
    image = Image.open(argument_path).convert('RGB')

    # Process PIL image with transforms and add a batch dimension
    x = transform(image).unsqueeze(0).detach().numpy()

    return [x]


def inference(inputs):
    x = torch.from_numpy(inputs[0])
    # Pass inputs to model forward function to get outputs
    out = model(x).detach().numpy()

    return [out]


def postprocess(outputs, result_path):
    out = torch.from_numpy(outputs[0])

    # Apply softmax to get predicted probabilities for each class
    probabilities = torch.nn.functional.softmax(out[0], dim=0)

    # Grab the values and indices of top 5 predicted classes
    values, indices = torch.topk(probabilities, top_k)

    # Prepare a nice dict of top k predictions
    predictions = [
        {"label": labels[i], "score": v.item()}
        for i, v in zip(indices, values)
    ]
    with open(result_path, 'w') as f:
        f.write(str(predictions))
