import json
import logging
import traceback
import zlib

import erlpack
from flask import Flask, request
from base64 import b64decode

app = Flask(__name__)
buffers = {}
decompressors = {}


def deserialize_erlpackage(payload):
    if isinstance(payload, bytes):
        return payload.decode()
    elif isinstance(payload, erlpack.Atom):
        return str(payload)
    elif isinstance(payload, list):
        return [deserialize_erlpackage(i) for i in payload]
    elif isinstance(payload, dict):
        deserialized = {}
        for k, v in payload.items():
            deserialized[deserialize_erlpackage(k)] = deserialize_erlpackage(v)
        return deserialized
    else:
        return payload


@app.route('/')
def hello_world():
    return "hello"


@app.route('/printer', methods=['POST'])
def printer():
    path = request.form.get('path')
    data = request.form.get('content')
    if path not in buffers:
        buffers[path] = bytearray()
        decompressors[path] = zlib.decompress()
    decompressor = decompressors[path]
    buffer = buffers[path]
    chunk = b64decode(data)
    buffer.extend(chunk)
    if not buffer.endswith(b'\x00\x00\xff\xff'):
        return 'ok'
    print(buffer)
    try:
        payload = decompressor.decompress(buffer)
    except BaseException as e:
        print(
            "Error decompressing message for Gateway "
        )
        buffers[path] = bytearray()
        return 'no'

    buffers[path] = bytearray()
    payload = json.loads(payload)
    app.logger.info(payload)
    return 'ok'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
