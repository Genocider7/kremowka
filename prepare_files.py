from mysql.connector import connect as connect_mysql
from sys import stderr
from os import chdir, rename as move
from os.path import dirname, realpath, join as join_path
from dotenv import dotenv_values
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

memes_dir = 'memes'
approved = 'approved'
ready = 'ready'

approved = join_path(memes_dir, approved)
ready = join_path(memes_dir, ready)

def connect_gdrive():
    return GoogleDrive(GoogleAuth())

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
    drive_handler = connect_gdrive()
    db_cursor.execute('SELECT images.id AS id, CONCAT(images.basename, \'.\', images.extension) AS name FROM images WHERE images.status=\'approved\'')
    files = db_cursor.fetchall()
    for (id, filename) in files:
        meme_path = join_path(approved, filename)
        basename = filename[:-4]
        if not meme_path.is_file():
            print(filename + ' not found', file=stderr)
            continue
        parent_list = []
        if config['parent_drive'] != '':
            parent_list.append({'id': config['parent_drive']})
        drive_file = drive_handler.CreateFile({'parents': parent_list})
        drive_file.SetContentFile(meme_path)
        drive_file['title'] = basename
        drive_file.Upload()
        url = config['new_file_url'].format(id=drive_file.metadata['id'])
        move(approved + filename, ready + filename)
        db_cursor.execute('UPDATE images SET status=\'ready\', url=\'' + url + '\' WHERE id=' + str(id))
        print(filename + ' succesfully uploaded. url: ' + url)
    db_handler.commit()

if __name__ == '__main__':
    main()
