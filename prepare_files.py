import requests, base64, mysql.connector, sys, os
from dotenv import dotenv_values
from pathlib import Path

approved = 'memes/approved/'
ready = 'memes/ready/'

def main():
    global config
    config = dotenv_values('.env')
    db_handler = mysql.connector.connect(
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
            print(filename + ' not found', file=sys.stderr)
            continue
        with open(approved + filename, 'rb') as image_file:
            image_string = base64.b64encode(image_file.read())
        params = {
            'key': config['api_key'],
            'action': 'upload',
            'source': image_string,
            'format': 'txt'
        }
        response = requests.post(config['image_host'], data=params)
        url = response.text
        os.rename(approved + filename, ready + filename)
        db_cursor.execute('UPDATE images SET status=\'ready\', url=\'' + url + '\' WHERE id=' + str(id))
        print(filename + ' succesfully uploaded. url: ' + url)
    db_handler.commit()

if __name__ == '__main__':
    main()
