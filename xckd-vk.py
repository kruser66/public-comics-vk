import os
import requests
from core import IMAGES_DIR, download_image
from dotenv import load_dotenv
from random import randint
from pprint import pprint


if __name__ == '__main__':

    os.makedirs(IMAGES_DIR, exist_ok=True)

    # load_dotenv()
    # login = os.getenv('INSTAGRAM_LOGIN')
    # password = os.getenv('INSTAGRAM_PASSWORD')
    comics_number = randint(1, 2556)

    comics_url = f'https://xkcd.com/{str(comics_number)}/info.0.json'

    response = requests.get(comics_url)
    response.raise_for_status()

    comics = response.json()

    download_image(comics['img'])


