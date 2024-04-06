import os
import socket
import tempfile
import traceback

from typing import TYPE_CHECKING

from common import bytes_to_ndarraylist, ndarraylist_to_bytes
from common import CMD_INFERENCE, CMD_POSTPROCESS, CMD_PREPROCESS
from common import RESP_ERR, RESP_OK
from common import SEPARATOR, SOCK_NAME

if TYPE_CHECKING:
    import numpy as np


# Open unix socket to communicate with the parent process
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
if os.path.exists(SOCK_NAME):
    os.unlink(SOCK_NAME)
sock.bind(SOCK_NAME)
sock.listen(1)

# Load & Initialise model
try:
    from model.main import inference, load, postprocess, preprocess
    load()
except Exception as e:
    # Write the error to file
    with open('error.txt', 'w') as f:
        tb = traceback.format_exc()
        f.write(tb)
    raise e


# Change working directory because the model expects to be in the model directory
os.chdir('model')


def do_preprocess(arg: bytes) -> bytes:
    argument_paths = arg.decode()
    argument_paths_list = argument_paths.split(SEPARATOR.decode())
    inputs: list[np.ndarray] = preprocess(*argument_paths_list)
    return ndarraylist_to_bytes(inputs)


def do_inference(arg: bytes) -> bytes:
    inputs = bytes_to_ndarraylist(arg)
    outputs: list[np.ndarray] = inference(inputs)
    return ndarraylist_to_bytes(outputs)


def do_postprocess(arg: bytes) -> bytes:
    outputs = bytes_to_ndarraylist(arg)
    result_path = tempfile.mktemp(prefix='ais_')
    postprocess(outputs, result_path)
    return result_path.encode()


handlers = {
    CMD_PREPROCESS: do_preprocess,
    CMD_INFERENCE: do_inference,
    CMD_POSTPROCESS: do_postprocess,
}

while True:
    conn, addr = sock.accept()  # TODO: Can be async and parallel?
    command, arg = conn.recv(100000).split(SEPARATOR, 1)  # TODO: Handle large files

    try:
        if command not in handlers:
            raise Exception(f'Unknown command: {command}')
        result = handlers[command](arg)
    except Exception:
        tb = traceback.format_exc()
        conn.sendall(RESP_ERR + SEPARATOR + tb.encode())
    else:
        print(f'result size: {len(result)}')
        conn.sendall(RESP_OK + SEPARATOR + result)
    finally:
        conn.close()
