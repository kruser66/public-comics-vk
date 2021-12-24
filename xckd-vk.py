import os
import requests
import logging
from dotenv import load_dotenv
from random import randint
from urllib.parse import unquote, urlsplit

VK_API_VERSION = '5.131'

logger = logging.getLogger('vk_logger')


def check_response_vk(response):
    if 'error' in response.keys():
        error_msg = response['error']['error_msg']
        logger.error(f'Ошибка вызова API VK: {error_msg}')
        raise Exception(error_msg)


def download_image(image_url):
    url = unquote(image_url)
    filename = os.path.split(urlsplit(url).path)[1]

    response = requests.get(image_url)
    response.raise_for_status()

    with open(filename, 'wb') as file:
        file.write(response.content)

    return filename


def fetch_last_comics_xkcd():
    comics_url = f'https://xkcd.com/info.0.json'

    response = requests.get(comics_url)
    response.raise_for_status()

    last_comics_number = response.json()['num']

    return last_comics_number


def fetch_random_comics_xkcd():
    comics_number = randint(1, fetch_last_comics_xkcd())
    comics_url = f'https://xkcd.com/{comics_number}/info.0.json'

    response = requests.get(comics_url)
    response.raise_for_status()

    comics = response.json()
    download_image(comics['img'])

    return comics


def call_get_vk_api(access_token, api_version, api_metod, params={}):
    api_url = f'https://api.vk.com/method/{api_metod}'

    params['access_token'] = access_token
    params['v'] = api_version

    response = requests.get(api_url, params=params)
    response.raise_for_status()

    response_vk_api = response.json()
    check_response_vk(response_vk_api)

    return response_vk_api['response']


def upload_photo(filename, album_id, upload_url, user_id):
    with open(filename, 'rb') as file:
        files = {
            'file': file,
        }
        response = requests.post(upload_url, files=files)

    response.raise_for_status()
    uploaded_photo = response.json()

    check_response_vk(uploaded_photo)

    return uploaded_photo


def get_wall_upload_server(access_token, api_version, group_id):
    params = {
        'group_id': group_id,
    }
    upload_server = call_get_vk_api(
        access_token, api_version, 'photos.getWallUploadServer', params
    )

    return upload_server


def save_wall_photo(access_token, api_version, group_id, server, photo, hash):
    api_url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {
        'access_token': access_token,
        'v': api_version,
        'group_id': group_id,
        'photo': photo,
        'hash': hash,
        'server': server
    }
    response = requests.post(api_url, params=params)
    response.raise_for_status()
    check_response_vk(response.json())

    saved_photo = response.json()['response']

    return saved_photo


def publish_wall_post(
        access_token,
        api_version,
        group_id,
        message,
        attachments):

    attach = 'photo{}_{}'.format(
        str(attachments['owner_id']), str(attachments['id'])
    )
    params = {
        'owner_id': -group_id,
        'from_group': 1,
        'message': message,
        'attachments': attach,
    }

    post = call_get_vk_api(
        access_token, api_version, 'wall.post', params
    )

    return post


def publish_random_comics_post(access_token, api_version, group_id):
    comics = fetch_random_comics_xkcd()
    comics_filename = os.path.split(comics['img'])[1]
    comics_comment = comics['alt']

    upload_server = get_wall_upload_server(access_token, api_version, group_id)
    uploaded_photo = upload_photo(comics_filename, **upload_server)
    photo = save_wall_photo(
        access_token,
        api_version,
        group_id,
        **uploaded_photo
    )
    publish_wall_post(
        access_token,
        api_version,
        group_id,
        comics_comment,
        photo[0]
    )
    logger.info('Пост опубликован!')


if __name__ == '__main__':

    load_dotenv()
    access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = int(os.getenv('VK_PUBLIC_ID'))

    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    try:
        publish_random_comics_post(access_token, VK_API_VERSION, group_id)

    except Exception:
        logger.exception('Ошибка')

    finally:
        for file in os.listdir():
            if file.endswith('.png'):
                os.remove(file)
