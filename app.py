import json
import logging
import os
import traceback
import zlib

import erlpack
import requests
from flask import Flask, request
from base64 import b64decode
from discord_webhook import DiscordWebhook, DiscordEmbed

app = Flask(__name__)
handler = logging.FileHandler('stream.log')
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
buffers = {}
decompressors = {}

REPOST_MAP = {
    '1184256142310908206': 'https://discord.com/api/webhooks/1281227178406711368/-il3fqvexrOuv9Ws3JpobG3kblIiEEIu_wB_10avlHE46IJ76y5-4TZTD-1vzFpujuCl',
    # penny
    '1238564371115020298': 'https://discord.com/api/webhooks/1281227356551385098/yhlNXNIYmSc_0RlvHH5-V2qQH9VT45OPhzZpFAUjRVOMtQpu4fKg1QVsLcf7egOkEJfq',
    # aiden
    '1121583569941315634': 'https://discord.com/api/webhooks/1308168354917388420/C57YbWzjF4_Axf9sUP18GswmjT5qmaadJoKzdmAlyKpEAfjuMHlmnlgwfjA4-RSEYhY6',
    # jv
    # '1181808200358580225': 'https://discord.com/api/webhooks/1281227785553186816/jcbLyG21MakQowAT1ql9XWLi0T6gH3WRqJkhbb-mxvI2q3SnfiKGqTFppUqijwY3MuoW',
    # mike
    '969226339766927410': 'https://discord.com/api/webhooks/1308168660422234162/omTXY9WjjKszUZ-3JcaG9fuzz94_LJP-NXS4J8QGl7avEgVAjI4pjURz_HFJepLqoyq6',
    # UW
    '1266488368452206746': 'https://discord.com/api/webhooks/1281575646576775210/qwLKhUj-Z5B0HLQyJ2onCL4Zxo0Zc8Eys5cB732krR0tFJlJfSFQzwNzIKKPMJCEjqPn',
    # cobra
    '1289681365373157416': 'https://discord.com/api/webhooks/1281575975326453913/aQrO9578YZHwwcNHL71N-U0kyaJUY1XFSHXfr3L0C7f-9iZAI4BW4RhLjmB4RWMNzEDj',
    # wick
    '1230679377700716594': 'https://discord.com/api/webhooks/1308168536581079110/e3PYNrhXDGZAmg-IWlqW0w5xSloKQVPh3S2xt0_PmUAuFwwpzW7A_zcjASB9A0LglGOE',
    # wick
    '1113626703491776562': 'https://discord.com/api/webhooks/1281576484749836309/GF1MYLJ0aRHoNg3uF86df0hjE6wqiLkc_ZF31VNquA2swEaNRHrbKImUWFk0OLwHWgsB',
    # eagle
    '1050275586968395798': 'https://discord.com/api/webhooks/1308168438421655563/acJMaEIUtlm-SlH0PIw58EoKaON2Wk85c2pgda05WWGVLfh9AsCJYCoyd0ftocVXmlqq',
    # fib
    '1275290247109935128': 'https://discord.com/api/webhooks/1283033259638263849/A_lrcgE1X2KaqN24B3a4GORD6HPlvYHjXWNor2oGqvZ2XfVxtLUVKYNAsK53ugYzIv1Y',
    # dev
    '1275291198310842481': 'https://discord.com/api/webhooks/1308168239863566346/kQUrf_Fz218X2b6GfYAx8cqQUhJMiN3rCEPyfyA-gLCUCsVHmghQcvZVj0XD_pjzT1Ex',
    # elom
    '1255965493903233166': 'https://discord.com/api/webhooks/1308168006836162560/Ol_ROoUyux85jZ0Q7BdLve15NY7C3QD5atyNlBNTSX9q-MJiUHCCncKW4Jy-Ca4BuhBp',
    # wolf
    '1244040902582865937': 'https://discord.com/api/webhooks/1308167923390742598/U2e2DEYGTgPW-LsCIhGVMEB7QMN0DMqy2EalMkM0Nv4cRRQsL_vY6TXpfq3gbTmoOKIU',
    # cblast
    # '860503584721076224' : 'https://discord.com/api/webhooks/1284110967478812672/m7dXnYn4Ud0YQxQbcqP49HEDVFst_TWC-aRinIsY8Acv8vH7LKkn52tmzx5Y2cfe0YLN', # trendspider
    '1258356916133036043': 'https://discord.com/api/webhooks/1308168951443882115/lgV4jmQ1rUygVUeNzZ3HxyZfpaAV6x8aroxwLs2P-TC4yWmaloxADiJRDzb6SqGPA7a5',
    # unusual flow
    '935627450099069008' : 'https://discord.com/api/webhooks/1308168804379132005/IGXcGnR11ikFtpMKPQCRio3bZv_T8Rtc1xvEWMUkxS_0u0Tjb7QoJmNf1rHmxTthTl4R',
    '935618770150518855' : 'https://discord.com/api/webhooks/1308168804379132005/IGXcGnR11ikFtpMKPQCRio3bZv_T8Rtc1xvEWMUkxS_0u0Tjb7QoJmNf1rHmxTthTl4R',
    # openbb
    '1062441525059002388': 'https://discord.com/api/webhooks/1308167823473770557/nlN_Auq_lpfOTNN8nrQ4Z8lglBvkWQIOoRxD-kd2KUUFYAgZJA9KTvBvi9PnlPYP6qwI',
    # remz
    '1279816198808404069': 'https://discord.com/api/webhooks/1308167823473770557/nlN_Auq_lpfOTNN8nrQ4Z8lglBvkWQIOoRxD-kd2KUUFYAgZJA9KTvBvi9PnlPYP6qwI',
    # test
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
        return 'no', 400

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
    elif message.get('d').get('channel_id') == '994362479830384650' and len(message.get('d').get('attachments', [])) > 0 \
            and ('net_market_1__999' in message.get('d').get('attachments')[0].get('url')
                 or 'algo_market_1__999' in message.get('d').get('attachments')[0].get('url')
                 or 'net_spy_1__999' in message.get('d').get('attachments')[0].get('url')
                 or 'net_qqq_1__999' in message.get('d').get('attachments')[0].get('url')
                 or 'algo_spy_1__999' in message.get('d').get('attachments')[0].get('url')
                 or 'algo_qqq_1__999' in message.get('d').get('attachments')[0].get('url')):
        url = 'https://discord.com/api/webhooks/1283034978669563945/s6D2y9EBTM7MPEVZ5DKc5IAocF8YyCbTj6G0CGPWlNeEnkn2n87PIjBIsK9i0-fdYSFt'  # tr-mnf
    elif (message.get('d').get('channel_id') == '994362479830384650' or message.get('d').get(
            'channel_id') == '742187231342755911') and len(message.get('d').get('attachments', [])) > 0 \
            and ('gexz_spx_s' in message.get('d').get('attachments')[0].get('url')
                 or 'gexz_spy_s' in message.get('d').get('attachments')[0].get('url')
                 or 'gexz_qqq_s' in message.get('d').get('attachments')[0].get('url')):
        url = 'https://discord.com/api/webhooks/1283136528134045706/NzdVbgpUsBbXJstXggvjKRVDU68WLK-KIja3B2l6nV3iovn_Zi33HFoVWzBO7srIgX3z'  # tr-gex
    elif (message.get('d').get('channel_id') == '1014626943922077856') and message.get('d').get('author').get('bot') and len(message.get('d').get('attachments')) > 0: # gex1
        url = 'https://discord.com/api/webhooks/1301948918225047655/EGWy1_kUqC1ln8Qx_lrXI__17-iQHKHsXzgkBbMvfI_02IXkFT1MKax_y1F-bwK32jOr'
        app.logger.info(message)
        # push_image_bot(message, url)
    elif message.get('d').get('channel_id') == '1027647733219209227' and len(
            message.get('d').get('attachments', [])) > 0:
        app.logger.info(message)
        push_gex_bot(message)
        return
    elif message.get('d').get('channel_id') in ['1253107508449509457']:  # '860503584721076224' not free
        app.logger.info(message)
        push_x_bot(message)
        return
    else:
        return
    app.logger.info(message)
    webhook = DiscordWebhook(url=url, content=message.get('d').get('content'),
                             username=message.get('d').get('username'))
    # msg = {
    #     'content': message.get('d').get('content'),
    #     'username': message.get('d').get('author').get('username')
    # }

    if len(message.get('d').get('attachments')) > 0:
        for attachment in message.get('d').get('attachments'):
            embed = DiscordEmbed()
            embed.set_image(url=attachment.get('url'))
            webhook.add_embed(embed)
    if len(message.get('d').get('embeds')) > 0:
        for embed in message.get('d').get('embeds'):
            webhook.add_embed(embed)
    # requests.post(url, msg)
    response = webhook.execute()


def push_x_bot(message):
    url = 'https://discord.com/api/webhooks/1284110967478812672/m7dXnYn4Ud0YQxQbcqP49HEDVFst_TWC-aRinIsY8Acv8vH7LKkn52tmzx5Y2cfe0YLN'
    image_url = message.get('d').get('embeds')[0].get('image').get('url')
    app.logger.info(image_url)
    wget_cmd = "wget '%s' -O ts.jpg" % image_url
    os.system(wget_cmd)
    webhook = DiscordWebhook(url=url, content=message.get('d').get('content'),
                             username=message.get('d').get('username'))
    embed = DiscordEmbed()
    embed.set_image(url=image_url)
    webhook.add_embed(embed)
    response = webhook.execute()

def push_image_bot(message, url):
    image_url = message.get('d').get('attachments')[0].get('url')
    app.logger.info(image_url)
    wget_cmd = "wget '%s' -O temp.jpg" % image_url
    os.system(wget_cmd)
    webhook = DiscordWebhook(url=url, content=message.get('d').get('content'),
                             username=message.get('d').get('username'))
    embed = DiscordEmbed()
    embed.set_image(url=image_url)
    webhook.add_embed(embed)
    response = webhook.execute()

def push_gex_bot(message):
    url = 'https://discord.com/api/webhooks/1283802750072655892/gVsvhRq_DGJhciSAlDOki7zGqAjjudlrs1XcCDhAyBoYGBgUzLcI0UmuEcJ5EWMXc08E'
    image_url = message.get('d').get('attachments')[0].get('url')
    wget_cmd = "wget '%s' -O gex_origin.png" % image_url
    os.system(wget_cmd)
    ffmpeg_cmd = 'ffmpeg -i gex_origin.png -filter:v "crop=650:405:1420:1100" gex_crop.png -y'
    os.system(ffmpeg_cmd)
    webhook = DiscordWebhook(url=url, content=message.get('d').get('content'),
                             username=message.get('d').get('username'))
    with open('gex_crop.png', 'rb') as f:
        webhook.add_file(file=f.read(), filename='gex_crop.png')
    embed = DiscordEmbed()
    embed.set_image(url='attachment://gex_crop.png')
    webhook.add_embed(embed)
    response = webhook.execute()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
