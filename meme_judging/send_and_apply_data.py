import sys
from dotenv import dotenv_values
from os import chdir
from paramiko import SSHClient, AutoAddPolicy
from os.path import exists, realpath, dirname
from shutil import rmtree
from os import remove
from run_check import execute_mysql_query_on_server

default_file = 'data_to_send.env'
temp_dir = 'temp'
sus_temp_dir = 'sus_temp'
data_file = 'data.json'

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


def main(args):
    global client
    if getattr(sys, 'frozen', False):
        app_path = sys.executable
    else:
        app_path = realpath(__file__)
    chdir(dirname(app_path))
    if len(args) == 0:
        filename = default_file
    else:
        filename = args[0]
    if not exists(filename):
        print('file {} not found'.format(filename))
        return
    config = dotenv_values('.env')
    images_status = dotenv_values(filename)
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy)
    print('connecting to {}...'.format(config['server_ip']))
    establish_ssh_connection(config['server_ip'], config['server_user'], config['user_password'], config['rsa_key_directory'], config['rsa_key_passcode'])
    print('connected!')
    print('updating memes status...')
    query = 'UPDATE images SET status=\"{}\" WHERE id={}'
    for key, value in images_status.items():
        sub_query = query.format(value, key)
        execute_mysql_query_on_server(client, sub_query, config['mysql_database'], config['mysql_username'], config['mysql_password'])
        print(sub_query)
    client.close()
    if exists(temp_dir):
        rmtree(temp_dir)
    if exists(sus_temp_dir):
        rmtree(sus_temp_dir)
    if exists(filename):
        remove(filename)
    if exists(data_file):
        remove(data_file)

if __name__ == '__main__':
    main(sys.argv[1:])