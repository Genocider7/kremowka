from mysql.connector import connect as connect_mysql
from dotenv import dotenv_values
from imagehash import average_hash
from PIL import Image
from os import chdir
from os.path import dirname, realpath, join as path_join, exists as file_exists

memes_directory = 'memes'
where_duplicates = {
    'approved' : True,
    'banned': True,
    'checked': True,
    'duplicate': False,
    'ready': True,
    'suspended': True,
    'waiting': False
}

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

def get_all_waiting():
    query = 'SELECT CONCAT(images.basename, \".\", images.extension) AS filename, images.id AS id FROM images WHERE images.status=\"waiting\"'
    db_cursor.execute(query)
    raw_ret = db_cursor.fetchall()
    ret = {}
    for record in raw_ret:
        if not file_exists(path_join(memes_directory, record[0])):
            remove_from_database(record[1])
            continue
        ret[record[1]] = record[0]
    return ret

def get_all_others():
    query = 'SELECT CONCAT(images.basename, \".\", images.extension) AS filename, images.id AS id FROM images WHERE images.status IN (NULL'
    for key in where_duplicates.keys():
        if not where_duplicates[key]:
            continue
        query += ', \"' + key + '\"'
    query += ')'
    db_cursor.execute(query)
    raw_ret = db_cursor.fetchall()
    ret = {}
    for record in raw_ret:
        meme_path = path_join(memes_directory, record[0])
        if not file_exists(meme_path):
            remove_from_database(record[1])
            continue
        ret[record[1]] = path_join(memes_directory, record[0])
    return ret

def remove_from_database(key_id):
    query = 'DELETE FROM images WHERE images.id=\"{}\"'.format(key_id)
    db_cursor.execute(query)
    db_handler.commit()

def load_hashes(image_filenames):
    ret = {}
    for key, filename in image_filenames.items():
        with Image.open(filename) as img:
            ret[key] = average_hash(img, 16)
    return ret

def main():
    global config
    chdir(dirname(realpath(__file__)))
    config = dotenv_values('.env')
    connect_db()
    waiting = get_all_waiting()
    other_memes = get_all_others()
    hashes = load_hashes(other_memes)
    duplicates = {}
    for id in waiting.keys():
        filepath = path_join(memes_directory, waiting[id])
        with Image.open(filepath) as waiting_image:
            waiting_hash = average_hash(waiting_image, 16)
        check = True
        target = ''
        for key, value in hashes.items():
            if waiting_hash == value:
                check = False
                target = 'duplicate'
                duplicates[id] = key
                break
        if check:
            target = 'checked'
        query = 'UPDATE images SET status=\"{target}\" WHERE id={id}'.format(target=target, id=id)
        db_cursor.execute(query)
        db_handler.commit()
        hashes[id] = waiting_hash

    for key, value in duplicates.items():
        query = 'INSERT INTO duplicates (checked_image, duplicate) VALUES ({checked_image}, {duplicate})'.format(checked_image=key, duplicate=value)
        db_cursor.execute(query)
        db_handler.commit()

if __name__ == '__main__':
    main()