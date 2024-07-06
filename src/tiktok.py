from . import config
import requests, re, json



cookies = config.tiktok_cookies
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
		get  = requests.get(url, cookies={"cookie": cookies}, headers=headers)

		# -> Data parsing to json
		details  = re.search('"webapp.video-detail":{(.*?)},"webapp.a-b"', get.text).group(1)
		json_data = json.loads("{"+details+"}")
		items = json_data["itemInfo"]["itemStruct"]
		response_json = { "status": "succes", "author": {}, "media": { "video": None, "music": None} }

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
		data_music = items["music"]
		url_music = data_music["playUrl"]
		if url_video:
			response_json["media"]["music"] = url_music

		return response_json

	except Exception as e:
		return { "status": "failled", "message": str(e) }


def download(url, typ):
	try:
		with requests.Session() as session:

			get  = session.get(url, cookies={"cookie": cookies}, headers=headers)

			# -> Data parsing to json
			details  = re.search('"webapp.video-detail":{(.*?)},"webapp.a-b"', get.text).group(1)
			json_data = json.loads("{"+details+"}")
			items = json_data["itemInfo"]["itemStruct"]

			# -> Video download handler
			if typ == "mp4":
				data_video = items["video"]
				url_video = data_video["playAddr"]
				if url_video:
					get_media = session.get(url_video, cookies={"cookie": cookies})
					with open("data/media/download.mp4", "wb") as file:
						file.write(get_media.content)
				else:
					return { "status": "failled", "message": "Url not found" }


			# -> Audio download handler
			if typ == "mp3":
				data_music = items["music"]
				url_music = data_music["playUrl"]
				if url_music:
					get_media = session.get(url_music, cookies={"cookie": cookies})
					with open("data/media/download.mp3", "wb") as file:
						file.write(get_media.content)
				else:
					return { "status": "failled", "message": "Url not found" }

			return { "status": "succes" }

	except Exception as e:
		return { "status": "failled", "message": str(e) }