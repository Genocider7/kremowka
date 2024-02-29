from mysql.connector import connect as connect_mysql
from dotenv import dotenv_values
from os import chdir, rename as move, listdir
from os.path import dirname, realpath, join as join_path, isdir, isfile

meme_directory = 'memes'
deleted_directory = 'deleted'
image_extensions = ['.jpg', '.png']

def connect_db():
    global db_handler
    global db_cursor
    db_handler = connect_mysql(
        host='localhost',
        user=config['db_username'],
        password=config['db_password'],
        database=config['database']
    )
    db_cursor = db_handler.cursor()

def delete_file(filepath, directory):
    move(join_path(meme_directory, directory, filepath), join_path(meme_directory, deleted_directory, filepath))

def main():
    global config
    chdir(dirname(realpath(__file__)))
    config = dotenv_values('.env')
    connect_db()
    
    dirs = [directory for directory in listdir(meme_directory) if directory != deleted_directory and isdir(join_path(meme_directory, directory))]
    query = 'SELECT CONCAT(images.basename, \".\", images.extension) AS filename, images.status AS directory FROM images'
    db_cursor.execute(query)
    db_memes = {}
    for directory in dirs:
        db_memes[directory] = []
    for record in db_cursor.fetchall():
        db_memes[record[1]].append(record[0])
    for directory in dirs:
        files = [file for file in listdir(join_path(meme_directory, directory)) if isfile(join_path(meme_directory, directory, file))]
        for file in files:
            file_ok = False
            for ext in image_extensions:
                if file.endswith(ext):
                    file_ok = True
                    break
            if not file_ok:
                continue
            if file not in db_memes[directory]:
                delete_file(file, directory)

if __name__ == '__main__':
    main()

