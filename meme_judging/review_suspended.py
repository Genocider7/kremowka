import sys
from paramiko import SSHClient, AutoAddPolicy
from dotenv import dotenv_values
from json import dumps
from os import mkdir, chdir
from os.path import join as path_join, isdir, dirname, realpath
from shutil import rmtree
from webbrowser import open as web_open
from run_check import execute_mysql_select

temp_dir = 'sus_temp'
statuses = [
    'suspended',
    'banned'
]

def establish_ssh_connection(server_ip, server_username, server_password=None, rsa_key_location=None, rsa_key_password=None):
    global client
    use_password = server_password!=None and server_password!=''
    use_rsa_key = rsa_key_location!=None and rsa_key_location!='' and not use_password
    if use_password:
        client.connect(server_ip, username=server_username, password=server_password)
    elif use_rsa_key:
        client.connect(server_ip, username=server_username, key_filename=rsa_key_location, passphrase=rsa_key_password)
    else:
        client.connect(server_ip, username=server_username, password='')

def main():
    global client
    global config
    if getattr(sys, 'frozen', False):
        app_path = dirname(sys.executable)
    else:
        app_path = realpath(__file__)
    chdir(app_path)
    client = SSHClient()
    config = dotenv_values('.env')
    memes_dir = path_join(config['project_dir'], 'memes')
    client.set_missing_host_key_policy(AutoAddPolicy)
    establish_ssh_connection(config['server_ip'], config['server_user'], config['user_password'], config['rsa_key_directory'], config['rsa_key_passcode'])
    if isdir(temp_dir):
        rmtree(temp_dir)
    mkdir(temp_dir)
    query_fields = {
        'id': '`images`.`id`',
        'filename': 'CONCAT(`images`.`basename`, ".", `images`.`extension`)',
        'status': '`images`.`status`',
        'author_name': '`images`.`submitted_by`',
        'author_id': '`images`.`submitted_by_id`' 
    }
    query = 'SELECT '
    first = True
    for alias, field in query_fields.items():
        if first:
            first = False
        else:
            query += ', '
        query += field + ' AS ' + alias
    first = True
    query += ' FROM images WHERE `images`.`status` IN ('
    for status in statuses:
        if first:
            first = False
        else:
            query += ', '
        query += f'\"{status}\"'
    query += ')'
    records = execute_mysql_select(client, query, config['mysql_database'], config['mysql_username'], config['mysql_password'])
    sftp = client.open_sftp()
    for record in records:
        meme_dir = path_join(memes_dir, record['filename']).replace('\\', '/')
        target_path = path_join(temp_dir, record['filename'])
        print('Getting file {}...'.format(record['filename']), end='\t')
        sftp.get(meme_dir, target_path)
        print('OK')
    with open('suspended_data.json', 'w') as json_file:
        json_file.write('var images = ' + dumps(records))
    web_open('suspended_memes_view.html')
    
if __name__ == '__main__':
    main()