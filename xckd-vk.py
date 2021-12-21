import os
import requests
from dotenv import load_dotenv
from random import randint
from pprint import pprint


IMAGES_DIR = 'files'
VK_API_VERSION = '5.131'


def download_image(image_url, params={}):
    filename = os.path.split(image_url)[1]
    response = requests.get(image_url, params=params)
    if response.ok:
        with open(os.path.join(IMAGES_DIR, filename), 'wb') as file:
            file.write(response.content)
        return filename


def fetch_last_comics_xkcd():
    comics_url = f'https://xkcd.com/info.0.json'

    response = requests.get(comics_url)
    response.raise_for_status()

    return response.json()['num']


def fetch_random_comics_xkcd():
    comics_number = randint(1, fetch_last_comics_xkcd())
    comics_url = f'https://xkcd.com/{str(comics_number)}/info.0.json'

    response = requests.get(comics_url)
    response.raise_for_status()
    comics = response.json()
    download_image(comics['img'])

    return comics


def requests_get_vk_api(access_token, api_metod, params={}):
    api_url = f'https://api.vk.com/method/{api_metod}'

    params['access_token'] = access_token
    params['v'] = VK_API_VERSION

    response = requests.get(api_url, params=params)
    response.raise_for_status()

    return response.json()['response']


def upload_photo(upload_server, filename):
    upload_image = os.path.join(IMAGES_DIR, filename)

    with open(upload_image, 'rb') as file:
        api_url = upload_server['upload_url']
        files = {
            'file': file,
        }

        response = requests.post(api_url, files=files)
        response.raise_for_status()

    return response.json()


def get_groups(access_token, extended=False, count=0):
    params = {
        'extended': extended,
        'count': count,
    }
    response = requests_get_vk_api(access_token, 'groups.get', params)

    return response


def get_wall_upload_server(access_token, group_id):
    params = {
        'group_id': group_id,
    }
    response = requests_get_vk_api(
        access_token, 'photos.getWallUploadServer', params
    )

    return response


def save_wall_photo(access_token, group_id, upload_photo_params):
    api_url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {
        'access_token': access_token,
        'v': VK_API_VERSION,
        'group_id': group_id,
        'photo': upload_photo_params['photo'],
        'hash': upload_photo_params['hash'],
        'server': upload_photo_params['server']
    }
    response = requests.post(api_url, params=params)
    response.raise_for_status()

    return response.json()['response']


def wall_post(access_token, group_id, message, attachments):
    attach = 'photo{}_{}'.format(
        str(attachments['owner_id']), str(attachments['id'])
    )
    pprint(attach)
    params = {
        'owner_id': -group_id,
        'from_group': 1,
        'message': message,
        'attachments': attach,
    }

    response = requests_get_vk_api(
        access_token, 'wall.post', params
    )

    return response


if __name__ == '__main__':

    os.makedirs(IMAGES_DIR, exist_ok=True)

    load_dotenv()
    access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = int(os.getenv('VK_PUBLIC_ID'))

    comics = fetch_random_comics_xkcd()
    comics_filename = os.path.split(comics['img'])[1]
    comics_comment = comics['alt']

    upload_server = get_wall_upload_server(access_token, group_id)
    upload_photo_params = upload_photo(upload_server, comics_filename)
    upload_photo = save_wall_photo(access_token, group_id, upload_photo_params)
    pprint(wall_post(
        access_token,
        group_id,
        comics_comment,
        upload_photo[0])
    )
