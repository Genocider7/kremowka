from mysql.connector import connect as connect_mysql
from dotenv import dotenv_values
from os import chdir, rename as move, listdir
from os.path import dirname, realpath, join as join_path

meme_directory = 'memes'
deleted_directory = 'deleted_memes'
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

def delete_file(filepath):
    move(join_path(meme_directory, filepath), join_path(deleted_directory, filepath))

def has_correct_extension(filename):
    for ext in image_extensions:
        if filename.endswith(ext):
            return True
    return False

def main():
    global config
    chdir(dirname(realpath(__file__)))
    config = dotenv_values('.env')
    connect_db()
    
    query = 'SELECT CONCAT(images.basename, \".\", images.extension) AS filename FROM images'
    db_cursor.execute(query)
    db_memes = [ret[0] for ret in db_cursor.fetchall()]
    for file in listdir(meme_directory):
        if not has_correct_extension(file):
            continue
        if file not in db_memes:
            delete_file(file)

if __name__ == '__main__':
    main()

