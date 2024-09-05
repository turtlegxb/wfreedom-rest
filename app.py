import json
import logging
import traceback
import zlib

import erlpack
import requests
from flask import Flask, request
from base64 import b64decode

app = Flask(__name__)
buffers = {}
decompressors = {}

REPOST_MAP = {
    '1184256142310908206' : 'https://discord.com/api/webhooks/1281227178406711368/-il3fqvexrOuv9Ws3JpobG3kblIiEEIu_wB_10avlHE46IJ76y5-4TZTD-1vzFpujuCl', # penny
    '1238564371115020298' : 'https://discord.com/api/webhooks/1281227356551385098/yhlNXNIYmSc_0RlvHH5-V2qQH9VT45OPhzZpFAUjRVOMtQpu4fKg1QVsLcf7egOkEJfq', # aiden
    '1121583569941315634' : 'https://discord.com/api/webhooks/1281227521534333020/wv1eZm0pu-2KTylUPRr-go_omLguJqlLy9wM1hc10Gn1bu1pZUFx0P6y68xzdDbH_UUM', # jv
    '1181808200358580225' : 'https://discord.com/api/webhooks/1281227785553186816/jcbLyG21MakQowAT1ql9XWLi0T6gH3WRqJkhbb-mxvI2q3SnfiKGqTFppUqijwY3MuoW', # mike
    '969226339766927410' : 'https://discord.com/api/webhooks/1281228125908500530/yFRi7p6EMg2arZGittSnK3xC9H_oTvAV2ylp0IpusrdDozM4Q7_PyJjjv0w8NWNWsuV0', # UW
}


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
        decompressors[path] = zlib.decompressobj()
        app.logger.info('creating new path:' + path)
    decompressor = decompressors[path]
    buffer = buffers[path]
    chunk = b64decode(data)
    buffer.extend(chunk)
    if not buffer.endswith(b'\x00\x00\xff\xff'):
        return 'ok'
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
    deal_with_messsage(payload)
    return 'ok'

def deal_with_messsage(message):
    url = 'https://discord.com/api/webhooks/1280947188096176180/lLHcxuE6mNkykxViCIbOnUYEwiSWvUs36_MIYZ-a6ViubUfnst8t3eaDP_uJDwPi_KW_'
    if message.get('t', None) != 'MESSAGE_CREATE' or message.get('d').get('channel_id') == '1280220293759238238':
        return
    if message.get('d').get('channel_id') in REPOST_MAP:
        url = REPOST_MAP[message.get('d').get('channel_id')]
    else:
        return
    app.logger.info(message)
    msg = {
        'content': message.get('d').get('content'),
        'username': message.get('d').get('author').get('username')
    }
    requests.post(url, msg)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
