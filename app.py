import logging
import os
import signal
import sys
from datetime import timedelta
from neonize.client import NewClient
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
    DeviceListMetadata
)
from neonize.types import MessageServerID
from neonize.utils import log
from neonize.utils.enum import ReceiptType, MediaType
from neonize.utils.message import get_message_type
from neonize.utils.iofile import get_bytes_from_name_or_url


from src import tiktok, config
from src.handling import media, send_message
import json


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
    print(msg_type)

    match text:
        case "debug":
            client.send_message(chat, message.__str__())

        case "test":
           client.send_audio(
                chat,
                "src/sample-12s.mp3",
                quoted=message,
            )

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
                                            buttonParamsJSON='{"display_text":"Profile","url":"https://profile.brutalx.my.id","merchant_url":"https://profile.brutalx.my.id"}',
                                        )
                                    ]
                                ),
                            ),
                        )
                    )
                ),
            )


    if "extendedTextMessage" in msg_type.__str__():
        url = msg_type.extendedTextMessage.matchedText
        if url:
            if "tiktok" in url:
                data = tiktok.fetch(url)
                button_rows = []
                author = "\n\nauthor:\n  username: %s \n  nickname: %s"%(data["author"]["username"], data["author"]["nickname"])
                body = url + author
                music = data["media"]["music"]
                video = data["media"]["video"]
                if video != None:
                    button_rows.append({"title":"MP4","description":"convert url to mp4","id":".mp4_tik "+url})
                if music != None:
                    button_rows.append({"title":"AUDIO","description":"convert url to audio","id":".audio_tik "+url})
                    button_rows.append({"title":"PTT","description":"convert url to ptt","id":".ptt_tik "+url})

                send_message.interactive_message(client, chat, body, button_rows)

    elif "interactiveResponseMessage" in msg_type.__str__():
        paramsJSON = msg_type.interactiveResponseMessage.nativeFlowResponseMessage.paramsJSON
        params_id = json.loads(paramsJSON)["id"]

        if ".mp4_" in params_id:
            media.download_mp4(client, chat, message, params_id)

        elif ".audio_" in params_id or ".ptt_" in params_id:
            media.download_mp3(client, chat, message, params_id)



@client.event(PairStatusEv)
def PairStatusMessage(_: NewClient, message: PairStatusEv):
    log.info(f"logged as {message.ID.User}")


client.connect()