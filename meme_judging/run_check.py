import sys

from paramiko import SSHClient, AutoAddPolicy
from dotenv import dotenv_values
from os import mkdir, chdir
from os.path import dirname, realpath, isdir, join as path_join
from shutil import rmtree
from json import dumps
from webbrowser import open as web_open

temp_dir = 'temp'

def execute_mysql_query_on_server(ssh_connection, query, mysql_database, mysql_username, mysql_password):
    query = query.replace('\"', '\\\"').replace('`', '\\`')
    return ssh_connection.exec_command('mysql {} -u\"{}\" -p\"{}\" -e\"{}\"'.format(mysql_database, mysql_username, mysql_password, query))

def execute_mysql_select(ssh_connection, query, mysql_database, mysql_username, mysql_password):
    (_, stdout, _) = execute_mysql_query_on_server(ssh_connection, query, mysql_database, mysql_username, mysql_password)
    lines = stdout.readlines()
    fields = None
    ret = []
    for line in lines:
        output = line.rstrip().split("\t")
        if fields == None:
            fields = output
            continue
        temp_dict = {}
        for i in range(len(output)):
            temp_dict[fields[i]] = output[i]
        ret.append(temp_dict)
    return ret

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
    global config
    global client
    global memes_dir
    if getattr(sys, 'frozen', False):
        app_path = sys.executable
    else:
        app_path = realpath(__file__)
    chdir(dirname(app_path))
    client = SSHClient()
    config = dotenv_values('.env')
    memes_dir = path_join(config['project_dir'], 'memes')
    client.set_missing_host_key_policy(AutoAddPolicy)
    establish_ssh_connection(config['server_ip'], config['server_user'], config['user_password'], config['rsa_key_directory'], config['rsa_key_passcode'])
    if isdir(temp_dir):
        rmtree(temp_dir)
    mkdir(temp_dir)
    sftp = client.open_sftp()
    query = 'SELECT CONCAT(images.basename, \".\", images.extension) AS filename, CONCAT(images.id, \".\", images.extension) AS target_filename, images.id AS id FROM images WHERE images.status=\"checked\"'
    files = execute_mysql_select(client, query, config['mysql_database'], config['mysql_username'], config['mysql_password'])
    if len(files) == 0:
        print("No images found.")
        return
    print("Found {} memes".format(len(files)))
    for file in files:
        sftp.get(path_join(memes_dir, file['filename']).replace("\\", "/"), path_join(temp_dir, file['target_filename']))
    sftp.close()
    array_for_json = [path_join(temp_dir, file['target_filename']) for file in files]
    with open('data.json', 'w', encoding='utf8') as file:
        file.write('var images = ' + dumps(array_for_json))
    web_open('view.html')
    client.close()

if __name__ == '__main__':
    main()
    