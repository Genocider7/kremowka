from mysql.connector import connect as connect_mysql
from dotenv import dotenv_values
from os import chdir, rename as move
from os.path import dirname, realpath, join as join_path

meme_directory = 'memes'

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

def main():
    global config
    chdir(dirname(realpath(__file__)))
    config = dotenv_values('.env')
    connect_db()

    query = 'SELECT CONCAT(images.basename, \".\", images.extension) AS filename, images.status AS directory, images.id AS id FROM images'
    db_cursor.execute(query)
    result = []
    for record in db_cursor.fetchall():
        temp_dict = {
            'filename': record[0],
            'directory': record[1],
            'id': record[2],
            'path': join_path(meme_directory, record[1], record[0])
        }
        result.append(temp_dict)

if __name__ == '__main__':
    main()

