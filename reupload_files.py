from os import chdir, listdir
from os.path import dirname, realpath, join as path_join, basename as get_basename
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
    memes_directory = path_join('memes', 'ready')
    memes_filenames = [path_join(memes_directory, file) for file in listdir(memes_directory) if file.endswith('.png') or file.endswith('.jpg')]
    for meme in memes_filenames:
        extension = meme[-3:]
        basename = get_basename(meme)[:-4]
        print('{}...'.format(meme), end='\t')
        stdout.flush()
        parent_list = []
        if config['parent_drive'] != '':
            parent_list.append({'id': config['parent_drive']})
        drive_file = drive_handler.CreateFile({'parents': parent_list})
        drive_file.SetContentFile(meme)
        drive_file.Upload()
        url = config['new_file_url'].format(id=drive_file.metadata['id'])
        db_cursor.execute('UPDATE images SET url=\"{}\" WHERE basename=\"{}\" AND extension=\"{}\"'.format(url, basename, extension))
        print(url)

if __name__ == '__main__':
    main()