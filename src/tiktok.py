from . import config, handling
import requests, re, json, os



headers = {
	'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
	'accept-language': 'en-US,en;q=0.9,id;q=0.8',
	'cache-control': 'max-age=0',
	'priority': 'u=0, i',
	'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
	'sec-ch-ua-mobile': '?0',
	'sec-ch-ua-platform': '"Linux"',
	'sec-fetch-dest': 'document',
	'sec-fetch-mode': 'navigate',
	'sec-fetch-site': 'same-origin',
	'sec-fetch-user': '?1',
	'upgrade-insecure-requests': '1',
	'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
}


def fetch(url):
	try:
		get  = requests.get(url, headers=headers)

		# -> Data parsing to json
		details  = re.search('"webapp.video-detail":{(.*?)},"webapp.a-b"', get.text).group(1)
		json_data = json.loads("{"+details+"}")
		items = json_data["itemInfo"]["itemStruct"]
		response_json = { "status": "succes", "author": {}, "media": { "video": None, "music": None}, "info": {} }

		# -> Post Info
		post_id = items["id"]
		response_json["info"] = { "post_id": post_id }

		# -> Author Information
		data_author = items["author"]
		nickname = data_author["nickname"]
		username = data_author["uniqueId"]
		response_json["author"] = { "username": username, "nickname": nickname }

		# -> Video download handler
		data_video = items["video"]
		url_video = data_video["playAddr"]
		if url_video:
			response_json["media"]["video"] = url_video

		# -> Audio download handler
		try:
			data_music = items["music"]
			url_music = data_music["playUrl"]
			if url_music:
				response_json["media"]["music"] = url_music
		except:
			response_json["media"]["music"] = None

		return response_json

	except Exception as e:
		return { "status": "failled", "message": str(e) }


def download(client, chat, message, url, typ):
	try:
		with requests.Session() as session:

			get  = session.get(url, headers=headers)

			# -> Data parsing to json
			details  = re.search('"webapp.video-detail":{(.*?)},"webapp.a-b"', get.text).group(1)
			json_data = json.loads("{"+details+"}")
			items = json_data["itemInfo"]["itemStruct"]

			# -> Video download handler
			if typ == "video":
				data_video = items["video"]
				url_video = data_video["playAddr"]

				if url_video:
					get_media = session.get(url_video)
					with open("data/media/download.mp4", "wb") as file:
						file.write(get_media.content)
					client.send_video(
						chat,
						"data/media/download.mp4",
						quoted=message
						)
					os.remove("data/media/download.mp4")



			# -> Audio download handler
			if typ == "audio" or typ == "ptt":
				data_music = items["music"]
				url_music = data_music["playUrl"]

				if url_music:
					get_media = session.get(url_music)
					with open("data/media/download.mp3", "wb") as file:
						file.write(get_media.content)

					if typ == "audio":
						client.send_audio(
			                chat,
			                "data/media/download.mp3",
			                quoted=message,
			            )
					else:
						rebuild_mp3 = handling.rebuild.mp3("data/media/download.mp3")
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


	except Exception as e:
		client.reply_message("failled: %s"%(e.__str__()), message)