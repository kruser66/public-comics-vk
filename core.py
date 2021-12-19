import requests
import os
from urllib.parse import unquote, urlsplit

IMAGES_DIR = 'files'


def extarct_filename(url):
    url = unquote(url)
    return os.path.split(url)[1]


def download_image(image_url, params={}):
    filename = extarct_filename(image_url)
    print(filename)
    response = requests.get(image_url, params=params)
    if response.ok:
        with open(os.path.join(IMAGES_DIR, filename), 'wb') as file:
            file.write(response.content)


def main():
    url = 'https://upload.wikimedia.org/wikipedia/commons/3/3f/HST-SM4.jpeg'
    os.makedirs(IMAGES_DIR, exist_ok=True)
    download_image(url, 'habble')


if __name__ == '__main__':
    main()
