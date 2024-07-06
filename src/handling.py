from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    Message,
    FutureProofMessage,
    InteractiveMessage,
    MessageContextInfo,
    DeviceListMetadata
)
import os, ffmpeg

from . import tiktok


class rebuild:
	def mp3(path):
	    try:
	        ffmpeg.input(path).output("data/media/download_rebuild.mp3").run()
	        return "succes"

	    except ffmpeg.Error as e:
	        return "failled"


class send_message:
    def interactive_message(client, chat, body, rows):
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
	                        body=InteractiveMessage.Body(text=body),
	                        footer=InteractiveMessage.Footer(text="@brutalx-04"),
	                        header=InteractiveMessage.Header(
	                            title="Message url detected",
	                            hasMediaAttachment=False,
	                        ),
	                        nativeFlowMessage=InteractiveMessage.NativeFlowMessage(
	                            buttons=[
	                                InteractiveMessage.NativeFlowMessage.NativeFlowButton(
	                                    name="single_select",
	                                    buttonParamsJSON='{"title":"List Buttons","sections":[{"title":"convert url to media","rows":%s}]}}'%(rows),
	                                ),
	                            ]
	                        ),
	                    ),
	                )
	            )
	        )
	    )


class media:
	def download_mp4(client, chat, message, params_id):
		typ, url = params_id.split(" ")
		if typ == ".mp4_tik":
			response = tiktok.download(url, "mp4")
			if response["status"] == "succes":
				client.send_video(
					chat,
					"data/media/download.mp4",
					caption="done",
					quoted=message
					)
				os.remove("data/media/download.mp4")
			else:
				client.reply_message("failled: %s"%(response["message"]), message)

	def download_mp3(client, chat, message, params_id):
		typ, url = params_id.split(" ")
		if typ == ".audio_tik" or typ == ".ptt_tik":
			response = tiktok.download(url, "mp3")
			if response["status"] == "succes":
				if typ == ".audio_tik":
					client.send_audio(
		                chat,
		                "data/media/download.mp3",
		                quoted=message,
		            )
				else:
					rebuild_mp3 = rebuild.mp3("data/media/download.mp3")
					if rebuild_mp3 == "succes":
						client.send_audio(
			                chat,
			                "data/media/download_rebuild.mp3",
			                ptt=True,
			                quoted=message,
			            )
						os.remove("data/media/download_rebuild.mp3")
					else:
						client.reply_message("failled rebuild mp3", message)

				os.remove("data/media/download.mp3")

			else:
				client.reply_message("failled: %s"%(response["message"]), message)