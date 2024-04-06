import os

import cv2
import numpy as np
import onnxruntime as ort


def load():
    global session

    # Load the model
    session = ort.InferenceSession(
        os.path.join(os.path.dirname(__file__), "mnist-12.onnx"),
        providers=['CPUExecutionProvider'],
    )


def preprocess(argument_path: str) -> list[np.ndarray]:
    filepath = argument_path
    img = cv2.imread(filepath)
    img = np.dot(img[..., :3], [0.299, 0.587, 0.114])  # Convert to grayscale
    img = cv2.resize(img, dsize=(28, 28), interpolation=cv2.INTER_AREA)
    img.resize((1, 1, 28, 28))
    img = img.astype(np.float32)
    return [img]


def inference(inputs: [np.ndarray]) -> list[np.ndarray]:
    global session

    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    pred_onx = session.run([output_name], {input_name: inputs[0]})

    return pred_onx


def postprocess(outputs: list[np.ndarray], result_path: str):
    # Get highest probability label
    pred_onx = np.argmax(outputs[0])
    print(pred_onx)
    with open(result_path, 'w') as f:
        f.write(str(pred_onx))
