# from requests import post as req_post
# from base64 import b64encode

# api_key = '6d207e02198a847aa98d0a2a901485a5'
# filename = 'file.jpg'
# url = 'https://freeimage.host/api/1/upload'

# with open(filename, 'rb') as image_file:
#     image_string = b64encode(image_file.read())
# params = {
#     'key': api_key,
#     'action': 'upload',
#     'source': image_string,
#     'format': 'txt'
# }
# response = req_post(url, data = params)
# print(response.text)

from os import chdir, listdir
from os.path import dirname, realpath, join as path_join, basename as get_basename
from dotenv import dotenv_values
from mysql.connector import connect as connect_mysql
from requests import post as req_post
from base64 import b64encode

def main():
    chdir(dirname(realpath(__file__)))
    config = dotenv_values('.env')
    db_handler = connect_mysql(
        host='localhost',
        user=config['db_username'],
        password=config['db_password'],
        database=config['database']
    )
    db_cursor = db_handler.cursor()
    memes_directory = path_join('memes', 'ready')
    memes_filenames = [path_join(memes_directory, file) for file in listdir(memes_directory) if file.endswith('.png') or file.endswith('.jpg')]
    update_list = {}
    for meme in memes_filenames:
        extension = meme[-3:]
        basename = get_basename(meme)[:-4]
        print('{}...'.format(meme), end='\t')
        with open(meme, 'rb') as image_file:
            image_string = b64encode(image_file.read())
        params = {
            'key': config['api_key'],
            'action': 'upload',
            'source': image_string,
            'format': 'txt'
        }
        response = req_post(config['image_host'], data=params)
        url = response.text
        db_cursor.execute('UPDATE images SET url=\"{}\" WHERE basename=\"{}\" AND extension=\"{}\"'.format(url, basename, extension))
        print(url)

if __name__ == '__main__':
    main()