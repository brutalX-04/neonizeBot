from . import config
from neonize.utils.message import get_message_type
import requests, random, os

apikey = random.choice(config.rembg_apikey)


# --> Remove Bg + Send Image
def remove(client, message, chat, url):
    try:
        client.download_any(url, path="data/media/download.jpg")

        response = requests.post(
            'https://api.remove.bg/v1.0/removebg',
            files={'image_file': open('data/media/download.jpg', 'rb')},
            data={'size': 'auto'},
            headers={'X-Api-Key': apikey},
        )

        if response.status_code == requests.codes.ok:
            path = 'data/media/no-bg.png'
            with open(path, 'wb') as out:
                out.write(response.content)

            client.send_image(chat, path, quoted=message)

        else:
            client.reply_message("failled: %s"%(response.text), message)

        os.remove("data/media/download.jpg")
        os.remove(path)

    except Exception as e:
        client.reply_message("failled: %s"%(e.__str__()), message)