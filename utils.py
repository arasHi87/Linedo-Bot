from config.config import *
from imgurpython import ImgurClient

def upload_to_imgur(url):
    client_id = IMGUR_CLIENT_ID
    client_secret = IMGUR_CLIENT_SECRET
    access_token = IMGUR_ACCESS_TOKEN
    refresh_token = IMGUR_REFRESH_TOKEN
    client = ImgurClient(client_id, client_secret, access_token, refresh_token)
    return client.upload_from_url(url)['link']

if __name__ == '__main__':
    upload_to_imgur('http://img.wenku8.com/image/1/1587/1587s.jpg')