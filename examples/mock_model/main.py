import time

import numpy as np

from .aiserving import Status, update_progress


def load():
    global time_step
    time_step = 1

    update_progress(Status.LOADING, 0, 1)
    time.sleep(1)
    update_progress(Status.LOADING, 1, 1)


def preprocess(str1_path: str, str2_path: str, file_path: str) -> list[np.ndarray]:
    global time_step

    for i in range(10):
        update_progress(Status.PREPROCESSING, i, 10)
        time.sleep(time_step)

    return [np.array([np.random.rand(10)])]


def inference(input: list[np.ndarray]) -> list[np.ndarray]:
    global time_step

    for i in range(10):
        update_progress(Status.INFERENCING, i, 10)
        time.sleep(time_step)

    return input


def postprocess(output: list[np.ndarray], result_path: str):
    global time_step

    for i in range(10):
        update_progress(Status.POSTPROCESSING, i, 10)
        time.sleep(time_step)

    with open(result_path, 'w') as f:
        f.write(str(time_step))
