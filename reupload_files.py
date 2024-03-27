from os import chdir
from os.path import dirname, realpath, join as path_join
from dotenv import dotenv_values
from mysql.connector import connect as connect_mysql
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from sys import stdout

def connect_gdrive():
    return GoogleDrive(GoogleAuth())

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
    drive_handler = connect_gdrive()
    memes_directory = 'memes'
    db_cursor.execute('SELECT images.id AS id, images.basename as basename, images.extension AS extension FROM images')
    db_ready_files = {}
    for entry in db_cursor.fetchall():
        db_ready_files[entry[0]] = (entry[1], entry[2])
    for meme_id, filename in db_ready_files.items():
        basename = filename[0]
        extension = filename[1]
        meme = path_join(memes_directory, basename + '.' + extension)
        print('{}...'.format(meme), end='\t')
        stdout.flush()
        parent_list = []
        if config['parent_drive'] != '':
            parent_list.append({'id': config['parent_drive']})
        drive_file = drive_handler.CreateFile({'parents': parent_list})
        drive_file.SetContentFile(meme)
        drive_file['title'] = basename
        drive_file.Upload()
        url = config['new_file_url'].format(id=drive_file.metadata['id'])
        db_cursor.execute('UPDATE images SET url=\"{}\" WHERE id={}'.format(url, meme_id))
        print(url)
    db_handler.commit()

if __name__ == '__main__':
    main()