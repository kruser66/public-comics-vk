import os
import requests
import logging
from dotenv import load_dotenv
from random import randint
from urllib.parse import unquote, urlsplit
from requests import (
    ReadTimeout,
    ConnectTimeout,
    HTTPError,
    Timeout,
    ConnectionError
)


VK_API_VERSION = '5.131'

logger = logging.getLogger('vk_logger')


def check_by_error_response(response):
    if 'error' in response.keys():
        error_msg = response['error']['error_msg']
        logger.error(f'Ошибка вызова API VK: {error_msg}')
        raise requests.HTTPError(error_msg)


def download_image(image_url):
    url = unquote(image_url)
    filename = os.path.split(urlsplit(url).path)[1]

    response = requests.get(image_url)
    response.raise_for_status()

    with open(filename, 'wb') as file:
        file.write(response.content)

    return filename


def fetch_last_comics():
    comics_url = f'https://xkcd.com/info.0.json'

    response = requests.get(comics_url)
    response.raise_for_status()

    last_comics_number = response.json()['num']

    return last_comics_number


def fetch_random_comics():
    comics_number = randint(1, fetch_last_comics())
    comics_url = f'https://xkcd.com/{comics_number}/info.0.json'

    response = requests.get(comics_url)
    response.raise_for_status()

    comics = response.json()
    filename = download_image(comics['img'])
    comics['filename'] = filename

    return comics


def requests_vk_api_metod(access_token, api_version, api_metod, params={}):
    api_url = f'https://api.vk.com/method/{api_metod}'

    api_params = params
    api_params['access_token'] = access_token
    api_params['v'] = api_version

    response = requests.get(api_url, params=api_params)
    response.raise_for_status()

    response_vk_api = response.json()
    check_by_error_response(response_vk_api)

    return response_vk_api['response']


def upload_photo(filename, upload_url):
    with open(filename, 'rb') as file:
        files = {
            'file': file,
        }
        response = requests.post(upload_url, files=files)
        response.raise_for_status()

    uploaded_photo = response.json()

    check_by_error_response(uploaded_photo)

    return uploaded_photo.values()


def get_wall_upload_url(access_token, api_version, group_id):
    params = {
        'group_id': group_id,
    }
    response = requests_vk_api_metod(
        access_token, api_version, 'photos.getWallUploadServer', params
    )

    return response['upload_url']


def save_wall_photo(
    access_token, api_version, group_id, server, photo, photo_hash
):
    api_url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {
        'access_token': access_token,
        'v': api_version,
        'group_id': group_id,
        'photo': photo,
        'hash': photo_hash,
        'server': server
    }
    response = requests.post(api_url, params=params)
    response.raise_for_status()
    saved_photo = response.json()
    check_by_error_response(saved_photo)

    return saved_photo['response']


def publish_wall_post(
        access_token, api_version, group_id, message,
        owner_id, photo_id):

    params = {
        'owner_id': -group_id,
        'from_group': 1,
        'message': message,
        'attachments': f'photo{owner_id}_{photo_id}',
    }

    post = requests_vk_api_metod(
        access_token, api_version, 'wall.post', params
    )

    return post


def upload_photo_on_server(
        access_token, api_version, group_id, filename):

    url = get_wall_upload_url(
        access_token=access_token,
        api_version=api_version,
        group_id=group_id)

    server, photo, photo_hash = upload_photo(filename, url)
    photo = save_wall_photo(
        access_token, api_version, group_id,
        server, photo, photo_hash
    )

    return photo[0]


def publish_random_comics_post(access_token, api_version, group_id):
    comics = fetch_random_comics()
    comics_filename = comics['filename']
    comics_comment = comics['alt']

    photo = upload_photo_on_server(
        access_token=access_token,
        api_version=api_version,
        group_id=group_id,
        filename=comics_filename
    )
    owner_id = photo['owner_id']
    photo_id = photo['id']
    publish_wall_post(
        access_token=access_token,
        api_version=api_version,
        group_id=group_id,
        message=comics_comment,
        owner_id=owner_id,
        photo_id=photo_id
    )
    logger.info('Пост опубликован!')
    os.remove(comics_filename)


if __name__ == '__main__':

    load_dotenv()
    access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = int(os.getenv('VK_PUBLIC_ID'))

    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    try:
        publish_random_comics_post(access_token, VK_API_VERSION, group_id)
    except (
        ReadTimeout,
        ConnectTimeout,
        HTTPError,
        Timeout,
        ConnectionError
    ):
        logger.exception('Ошибка requests')

    finally:
        for file in os.listdir():
            if file.endswith('.png') or file.endswith('.jpg'):
                os.remove(file)
