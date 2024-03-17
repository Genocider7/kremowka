from os import chdir, listdir
from os.path import dirname, realpath, join as path_join, basename as get_basename
from dotenv import dotenv_values
from mysql.connector import connect as connect_mysql
from requests import post as req_post
from base64 import b64encode
from json import loads as json_loads

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
    for meme in memes_filenames:
        extension = meme[-3:]
        basename = get_basename(meme)[:-4]
        print('{}...'.format(meme), end='\t')
        with open(meme, 'rb') as image_file:
            image_string = b64encode(image_file.read())
        params = {
            'key': config['api_key'],
            'action': 'upload',
            'image': image_string,
            'format': 'txt'
        }
        response = req_post(config['image_host'], data=params)
        url = json_loads(response.text)['data']['image']['url']
        db_cursor.execute('UPDATE images SET url=\"{}\" WHERE basename=\"{}\" AND extension=\"{}\"'.format(url, basename, extension))
        print(url)

if __name__ == '__main__':
    main()