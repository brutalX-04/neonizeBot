from bs4 import BeautifulSoup
from urllib.parse import quote as encode_url
import requests, os


def search(keywords):
	try:
		url = "https://www.bing.com/search?q=" + encode_url(keywords + " pinterest") + "&first=1&FORM=PERE"
		headers = { "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36" }
		search = requests.get(url, headers=headers)

		soup = BeautifulSoup(search.text, "html.parser")
		results = soup.select("#b_results cite")

		url_pins = []
		for url in results:
			url = url.text
			if "pinterest.com" in url:
				url_pins.append(url)

		return {"status":"succes","url": url_pins[0]}

	except Exception as e:
		return {"status":"failled"}


def get_first_image(client, chat, message, keywords):
	try:
		data_search = search(keywords)
		if data_search["status"] == "succes":
			pin_url = data_search["url"]

			fetch = requests.get(pin_url)
			soup = BeautifulSoup(fetch.text, "html.parser")
			
			deeplink = soup.find(attrs={"data-test-id":"deeplink-wrapper"})
			image = deeplink.img.get("src")
			img_url = image.replace("236x", "736x")

			get_media = requests.get(img_url)
			with open("data/media/download.jpg", "wb") as file:
				file.write(get_media.content)
			client.send_image(
				chat,
				"data/media/download.jpg",
				caption="done",
				quoted=message
				)
			os.remove("data/media/download.jpg")

		else:
			client.reply_message("failled", message)

	except Exception as e:
		client.reply_message("failled: %s"%(e.__str__()), message)