from requests import post as req_post
from base64 import b64encode
from mysql.connector import connect as connect_mysql
from sys import stderr
from os import chdir, rename as move
from os.path import dirname, realpath
from dotenv import dotenv_values
from pathlib import Path

approved = 'memes/approved/'
ready = 'memes/ready/'

def main():
    global config
    chdir(dirname(realpath(__file__)))
    config = dotenv_values('.env')
    db_handler = connect_mysql(
        host='localhost',
        user=config['db_username'],
        password=config['db_password'],
        database=config['database']
    )
    db_cursor = db_handler.cursor()
    db_cursor.execute('SELECT images.id AS id, CONCAT(images.basename, \'.\', images.extension) AS name FROM images WHERE images.status=\'approved\'')
    files = db_cursor.fetchall()
    for (id, filename) in files:
        path = Path(approved + filename)
        if not path.is_file():
            print(filename + ' not found', file=stderr)
            continue
        with open(approved + filename, 'rb') as image_file:
            image_string = b64encode(image_file.read())
        params = {
            'key': config['api_key'],
            'action': 'upload',
            'source': image_string,
            'format': 'txt'
        }
        response = req_post(config['image_host'], data=params)
        url = response.text
        move(approved + filename, ready + filename)
        db_cursor.execute('UPDATE images SET status=\'ready\', url=\'' + url + '\' WHERE id=' + str(id))
        print(filename + ' succesfully uploaded. url: ' + url)
    db_handler.commit()

if __name__ == '__main__':
    main()
