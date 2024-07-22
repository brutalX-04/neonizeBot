import logging
import os
import signal
import sys
from datetime import timedelta
from neonize.client import NewClient, ExtendedTextMessage
from neonize.events import (
    ConnectedEv,
    MessageEv,
    PairStatusEv,
    event,
    ReceiptEv,
    CallOfferEv,
)
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    Message,
    FutureProofMessage,
    InteractiveMessage,
    MessageContextInfo,
    DeviceListMetadata,
    ContextInfo
)
from neonize.types import MessageServerID
from neonize.utils import log, extract_text
from neonize.utils.enum import ReceiptType, MediaType
from neonize.utils.message import get_message_type
from neonize.utils.iofile import get_bytes_from_name_or_url


from src import tiktok, config, instagram, groq, rmbg
from src.handling import media, send_message, scraper
import json, os, sys

# --> Set
try:
    sys.path.append("/home/ubuntu/nenonizeBot/")
    os.chdir("/home/ubuntu/neonizeBot/")
    sys.path.insert(0, "/home/ubuntu/neonizeBot/")
except Exception as e:
    pass



sys.path.insert(0, os.getcwd())


def interrupted(*_):
    event.set()


log.setLevel(logging.DEBUG)
signal.signal(signal.SIGINT, interrupted)


client = NewClient("db.sqlite3")


@client.event(ConnectedEv)
def on_connected(_: NewClient, __: ConnectedEv):
    log.info("⚡ Connected")


@client.event(ReceiptEv)
def on_receipt(_: NewClient, receipt: ReceiptEv):
    log.debug(receipt)


@client.event(CallOfferEv)
def on_call(_: NewClient, call: CallOfferEv):
    log.debug(call)


@client.event(MessageEv)
def on_message(client: NewClient, message: MessageEv):
    handler(client, message)

from PIL import Image
from io import BytesIO
import json


def handler(client: NewClient, message: MessageEv):
    text = message.Message.conversation or message.Message.extendedTextMessage.text
    chat = message.Info.MessageSource.Chat
    msg_type = get_message_type(message)

    match text:
        case "debug":
            client.send_message(chat, message.__str__())
            return

        case ".menu":
            client.send_message(
                chat,
                Message(
                    viewOnceMessage=FutureProofMessage(
                        message=Message(
                            messageContextInfo=MessageContextInfo(
                                deviceListMetadata=DeviceListMetadata(),
                                deviceListMetadataVersion=2,
                            ),
                            interactiveMessage=InteractiveMessage(
                                body=InteractiveMessage.Body(text=config.menu),
                                footer=InteractiveMessage.Footer(text="@brutalx-04"),
                                header=InteractiveMessage.Header(
                                    hasMediaAttachment=True,
                                    imageMessage=client.build_image_message("src/image/bg.jpg").imageMessage
                                ),
                                nativeFlowMessage=InteractiveMessage.NativeFlowMessage(
                                    buttons=[
                                        InteractiveMessage.NativeFlowMessage.NativeFlowButton(
                                            name="cta_url",
                                            buttonParamsJSON='{"display_text":"Profile","url":"https://github.com/brutalX-04","merchant_url":"https://github.com/brutalX-04"}',
                                        )
                                    ]
                                ),
                            ),
                        )
                    )
                ),
            )
            return

        case ".rmbg":
            quoted = msg_type.extendedTextMessage.contextInfo.quotedMessage
            if "imageMessage" in quoted.__str__():
                rmbg.remove(client, message, chat, quoted)

    if ".ai " in text:
        ai_text = groq.chat(text.split(" ")[1])
        client.reply_message(ai_text, message)

    elif ".mp4_tik " in text or ".mp4_ig " in text:
        media.download_mp4(client, chat, message, text)
        return

    elif ".audio_tik " in text or ".ptt_tik " in text or ".audio_ig " in text or ".ptt_ig " in text:
        media.download_mp3(client, chat, message, text)
        return

    elif ".img_ig " in text or ".ss_web " in text:
        media.download_image(client, chat, message, text)
        return

    elif ".pins " in text:
        keywords = text.split(".pins ")[1]
        scraper.pinterest(client, chat, message, keywords)
        return

    elif ".bing_img " in text:
        keywords = text.split(".bing_img ")[1]
        scraper.bing(client, chat, message, keywords)
        return


    if "extendedTextMessage" in msg_type.__str__():
        url = msg_type.extendedTextMessage.matchedText
        if url:
            if "tiktok" in url:
                data = tiktok.fetch(url)
                if data["status"] == "succes":
                    post_id = data["info"]["post_id"]
                    button_rows = []
                    author = "\n\ninfo:\n  username: %s \n  nickname: %s"%(data["author"]["username"], data["author"]["nickname"])
                    body = "source: tiktok \npost_id: " + post_id + author
                    music = data["media"]["music"]
                    video = data["media"]["video"]
                    button_rows.append({"title":"MP4","description":"convert url to mp4","id":".mp4_tik "+url})
                    if music != None:
                        button_rows.append({"title":"AUDIO","description":"convert url to audio","id":".audio_tik "+url})
                        button_rows.append({"title":"PTT","description":"convert url to ptt","id":".ptt_tik "+url})

                    send_message.interactive_message(client, chat, body, button_rows)

            elif "instagram" in url:
                ids = url.split("/")[4]
                data = instagram.fetch(ids)
                if data["status"] == "succes":
                    button_rows = []
                    author = "\n\ninfo:\n  username: %s\n  fullname: %s\n  like: %s\n  comment: %s"%(data["author"]["username"], data["author"]["fullname"], data["post_info"]["like"], data["post_info"]["comment"])
                    body = "source: instagram \npost_id: " + ids + author
                    music = data["media"]["music"]["url"]
                    video = data["media"]["video"]["url"]
                    image = data["media"]["image"]["url"]
                    if len(image)>0:
                        button_rows.append({"title":"IMG","description":"convert url to image","id":".img_ig "+url})
                    if len(video)>0:
                        button_rows.append({"title":"MP4","description":"convert url to mp4","id":".mp4_ig "+url})
                    if music != None:
                        button_rows.append({"title":"AUDIO","description":"convert url to audio","id":".audio_ig "+url})
                        button_rows.append({"title":"PTT","description":"convert url to ptt","id":".ptt_ig "+url})

                    send_message.interactive_message(client, chat, body, button_rows)

        return

    elif "interactiveResponseMessage" in msg_type.__str__():
        paramsJSON = msg_type.interactiveResponseMessage.nativeFlowResponseMessage.paramsJSON
        params_id = json.loads(paramsJSON)["id"]

        if ".mp4_" in params_id:
            media.download_mp4(client, chat, message, params_id)

        elif ".audio_" in params_id or ".ptt_" in params_id:
            media.download_mp3(client, chat, message, params_id)

        elif ".img_" in params_id:
            media.download_image(client, chat, message, params_id)

        return

    elif "imageMessage" in msg_type.__str__():
        caption = msg_type.imageMessage.caption
        if caption == ".rmbg":
            rmbg.remove(client, message, chat, msg_type)



@client.event(PairStatusEv)
def PairStatusMessage(_: NewClient, message: PairStatusEv):
    log.info(f"logged as {message.ID.User}")


client.connect()