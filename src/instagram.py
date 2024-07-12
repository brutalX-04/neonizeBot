from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    Message,
    FutureProofMessage,
    InteractiveMessage,
    MessageContextInfo,
    DeviceListMetadata
)

from . import config, handling
import requests, json, os

cookies = config.instagram_cookies


def fetch(ids):
	try:
		response_json = { "status": {},"author": {}, "post_info": {}, "media": {} }

		data = requests.get("https://www.instagram.com/p/%s/?__a=1&__d=dis"%(ids), cookies={ "cookie": cookies }).json()

		product_type = data["items"][0]["product_type"]
		response_json["product_type"] = product_type

		owner = data["items"][0]["owner"]
		username = owner["username"]
		fullname = owner["full_name"]
		response_json["author"] = { "username": username, "fullname": fullname }

		post_info = data["items"][0]
		like_count = post_info["like_count"]
		comment_count = post_info["comment_count"]
		response_json["post_info"] = { "like": like_count, "comment": comment_count }

		list_url_image = []
		list_url_video = []

		if product_type == "feed":
			image_url = data["items"][0]["image_versions2"]["candidates"][0]["url"]

			list_url_image.append(image_url)

		# fetch url carousel
		elif product_type == "carousel_container":
			carousel_media = data["items"][0]["carousel_media"]
			for x in carousel_media:
				try:
					video_url = x["video_versions"][0]["url"]
					list_url_video.append(video_url)
				except:
					image_url = x["image_versions2"]["candidates"][0]["url"]
					list_url_image.append(image_url)

		# fetch url clips
		elif product_type == "clips":
			video_url = data["items"][0]["video_versions"][0]["url"]
			list_url_video.append(video_url)

		response_json["media"]["image"] = { "url": list_url_image }
		response_json["media"]["video"] = { "url": list_url_video }

		# find url music
		try:
			music_metadata = data["items"][0]["music_metadata"]

			if music_metadata is None:
				music_url = data["items"][0]["clips_metadata"]["original_sound_info"]["progressive_download_url"]
				if music_url: pass
				else:
					musik_url = None

			else:
				music_url = music_metadata["music_info"]["music_asset_info"]["progressive_download_url"]
				if music_url: pass
				else:
					musik_url = None

			response_json["media"]["music"] = { "url": music_url }

		except:
			response_json["media"]["music"] = { "url": None }

		response_json["status"] = "succes"
		return response_json


	except Exception as e:
		return { "status": "failled", "message": e.__str__() }


def download(client, chat, message, url, typ):
	ids = url.split("/")[4]
	data = fetch(ids)

	if data["status"] == "succes":
		if typ == "image":
			path = "data/media/download.jpg"
			url_image = data["media"]["image"]["url"]

			if len(url_image)>0:
				count = 1
				cards = []
				list_filepath = []
				body = "Done !"
				footer = "source: instagram \npost_id: %s"%(ids)
				for url in url_image:
					filepath = "data/media/download" + count.__str__() + ".jpg"
					get_media = requests.get(url, cookies={"cookie": cookies})
					with open(filepath, "wb") as file:
						file.write(get_media.content)

					cards.append({
						"header": InteractiveMessage.Header(hasMediaAttachment=True, imageMessage=client.build_image_message(filepath).imageMessage),
                        'footer': InteractiveMessage.Footer(text="media " + count.__str__()),
                        'nativeFlowMessage': InteractiveMessage.NativeFlowMessage(
                            buttons=[
                                InteractiveMessage.NativeFlowMessage.NativeFlowButton(name="index")
                            ]
                        )
					})
					list_filepath.append(filepath)
					count+=1

				handling.send_message.carousel(client, chat, body, footer, cards)
				for x in list_filepath:
					os.remove(x)

			else:
				client.reply_message("failled: no image content", message)

		elif typ == "video":
			path = "data/media/download.mp4"
			url_video = data["media"]["video"]["url"]

			if len(url_video)>0:
				count = 1
				cards = []
				list_filepath = []
				body = "Done !"
				footer = "source: instagram \npost_id: %s"%(ids)
				for url in url_video:
					filepath = "data/media/download" + count.__str__() + ".mp4"
					get_media = requests.get(url, cookies={"cookie": cookies})
					with open(filepath, "wb") as file:
						file.write(get_media.content)

					cards.append({
						"header": InteractiveMessage.Header(hasMediaAttachment=True, videoMessage=client.build_video_message(filepath).videoMessage),
                        'footer': InteractiveMessage.Footer(text="media " + count.__str__()),
                        'nativeFlowMessage': InteractiveMessage.NativeFlowMessage(
                            buttons=[
                                InteractiveMessage.NativeFlowMessage.NativeFlowButton(name="index")
                            ]
                        )
					})
					list_filepath.append(filepath)
					count+=1

				handling.send_message.carousel(client, chat, body, footer, cards)
				for x in list_filepath:
					os.remove(x)

			else:
				client.reply_message("failled: no video content", message)

		elif typ == "audio" or typ == "ptt":
			path = "data/media/download.mp3"
			url_audio = data["media"]["music"]["url"]

			if url_audio != None:
				get_media = requests.get(url_audio, cookies={"cookie": cookies})
				with open(path, "wb") as file:
					file.write(get_media.content)
				rebuild_mp3 = handling.rebuild.mp3("data/media/download.mp3")

				if typ == "audio":
					client.send_audio(
		                chat,
		                "data/media/download_rebuild.mp3",
		                quoted=message,
		            )
				else:
					if rebuild_mp3 == "succes":
						client.send_audio(
					        chat,
					        "data/media/download_rebuild.mp3",
					        ptt=True,
					        quoted=message,
					    )
					else:
						client.reply_message("failled rebuild mp3", message)

				os.remove("data/media/download_rebuild.mp3")
				os.remove("data/media/download.mp3")

			else:
				client.reply_message("failled: no audio content", message)

	else:
		client.reply_message("failled fetching data", message)