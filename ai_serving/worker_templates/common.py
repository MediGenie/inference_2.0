import io

import numpy as np

SOCK_NAME = 'ais.sock'
SEPARATOR = b'|'

CMD_PREPROCESS = b'1'
CMD_INFERENCE = b'2'
CMD_POSTPROCESS = b'3'

RESP_OK = b'0'
RESP_ERR = b'1'


def bytes_to_ndarraylist(arg: bytes) -> list[np.ndarray]:
    f = io.BytesIO(arg)
    npz = np.load(f)
    return [
        npz[key]
        for key in npz.files
    ]


def ndarraylist_to_bytes(arg: list[np.ndarray]) -> bytes:
    f = io.BytesIO()
    np.savez_compressed(f, *arg)
    return f.getvalue()
