import logging
from discord import Intents, Client, Embed, Game, Status, DMChannel, TextChannel
from discord.errors import Forbidden as disc_Forbidden, NotFound as disc_not_found
from requests import get as request_get
from mysql.connector import connect as connect_mysql
from validators import url as validate_url
from dotenv import dotenv_values
from datetime import datetime, timedelta
from random import choice
from pytz import timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from hashlib import md5
from traceback import format_exc as exception_traceback
from os import rename as move, mkdir
from os.path import exists as path_exists, join as path_join

intents = Intents.default()
intents.guilds = True
intents.message_content = True
client = Client(intents=intents)
pope_embed = None
channels = {}
logger = None

def set_logger():
    global logger
    global log_handler
    logger = logging.getLogger()
    logger.setLevel(logging.OUTPUT)
    log_handler = logging.FileHandler(config['log_file'], 'a', 'utf8')
    formatter = logging.Formatter(fmt = '%(levelname)s :: %(asctime)s - %(message)s')
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

def log(message):
    logger.log(msg = message, level = logger.level)
    print(message)

def connect_db(main_connect = True):
    global db_handler
    global db_cursor
    db_handler = connect_mysql(
        host='localhost',
        user=config['db_username'],
        password=config['db_password'],
        database=config['database']
    )
    db_cursor = db_handler.cursor()
    if main_connect:
        log('Connected to mysql database!')
    else:
        log('Refreshed msql connection')

def get_channels_from_db():
    global channels
    db_cursor.execute('SELECT channels.guild_id AS guild, channels.channel_id AS channel FROM channels')
    result = db_cursor.fetchall()
    if not result:
        return
    for (guild, channel_id) in result:
        channel = client.get_channel(int(channel_id))
        channels[guild] = channel

def check_for_channel_id(channel_string):
    channel_string = channel_string.strip()
    if len(channel_string) > 22:
        return False
    if not channel_string.startswith('<#') or not channel_string.endswith('>'):
        return False
    channel_string = channel_string[2:-1]
    for i in range(len(channel_string)):
        if ord(channel_string[i]) < ord('0') or ord(channel_string[i]) > ord('9'):
            return False
    return channel_string

def get_random_image():
    db_cursor.execute('SELECT count(*) FROM images')
    count = db_cursor.fetchone()
    count = count[0]
    limit = max(1, (int)(count/10))
    db_cursor.execute('SELECT images.id AS id, images.url AS url, images.submitted_by AS author FROM images WHERE images.   status=\"ready\" ORDER BY images.last_used, RAND() LIMIT ' + str(limit))
    pick = choice(db_cursor.fetchall())
    db_cursor.execute('UPDATE images SET images.last_used=\'' + datetime.now().strftime('%Y-%m-%d') + '\' WHERE id=' + str(pick[0]))
    db_handler.commit()
    return (pick[1], pick[2])

def get_image_embed(image):
    global pope_embed
    (url, author) = image
    pope_embed = Embed(description=dictionary['embed_description'].format(url=url))
    pope_embed.set_image(url=url)
    pope_embed.set_footer(text=dictionary['embed_footer'].format(author_name=author))

async def prepare_embed():
    image = get_random_image()
    get_image_embed(image)

async def send_pope_memes():
    results = {}
    for server, channel in channels.copy().items():
        if channel == None:
            remove_server_channel(server)
            continue
        try:
            await channel.send(embed=pope_embed)
            result_code = 0
        except disc_Forbidden:
            guild = await client.fetch_guild(server)
            owner = await client.fetch_user(guild.owner_id)
            try:
                await owner.send(dictionary['missing_perms'].format(guild_name=guild.name))
                result_code = 1
            except:
                result_code = 33
        except disc_not_found:
            guild = await client.fetch_guild(server)
            owner = await client.fetch_user(guild.owner_id)
            try:
                await owner.send(dictionary['channel_not_found'].format(guild_name=guild.name, prefix=config['prefix']))
                result_code = 2
            except:
                result_code = 34
        except:
            result_code = 64
        finally:
            results[server] = result_code
    
    log('Sending memes results:')
    for server_id, result in results.items():
        log('Server {}: {}'.format(server_id, result))    

async def stop_receiving_memes():
    global memes_ok 
    memes_ok = False
    game = Game(config['maintanance'])
    await client.change_presence(status = Status.dnd, activity = game)

async def start_receiving_memes():
    global memes_ok 
    memes_ok = True
    game = Game('{}help'.format(config['prefix']))
    await client.change_presence(activity = game)

def configure_channel(channel_id, server_id):
    global channels
    channel_id = str(channel_id)
    server_id = str(server_id)
    if server_id in channels.keys():
        cmd = 'UPDATE channels SET channel_id=\"' +  channel_id + '\" WHERE guild_id=\"' + server_id + '\"'
    else:
        cmd = 'INSERT INTO channels (guild_id, channel_id) VALUES (\"' + server_id + '\", \"' + channel_id + '\")'
    channel = client.get_channel(int(channel_id))
    if channel == None:
        return False
    channels[server_id] = channel
    db_cursor.execute(cmd)
    db_handler.commit()
    return True

async def receive_file(url, author_name, author_id, where_to_send):
    extension = url.split('?')[0][-3:]
    basename = md5((str(author_id) + str(datetime.now())).encode()).hexdigest()
    with open(path_join(config['save_directory'], basename + '.' + extension), 'wb') as file:
        file.write(request_get(url).content)
    db_cursor.execute('INSERT INTO images (basename, extension, submitted_by, submitted_by_id) VALUES (\"' + basename + '\", \"' + extension + '\", \"' + author_name + '\", \"' + str(author_id) + '\")')
    db_handler.commit()
    db_cursor.execute('SELECT images.id AS id FROM images WHERE images.basename=\"' + basename + '\" ORDER BY images.id DESC LIMIT 1')
    result = db_cursor.fetchone()
    id = result[0]
    await where_to_send.send(dictionary['meme_sent'].format(meme_id=id))
    add_user_timeout(author_id)

def correct_hour(hour):
    hour -= config['time_offset']
    while hour < 0:
        hour += 24
    while hour >= 24:
        hour -= 24
    return hour

@client.event
async def on_ready():
    global scheduler
    global timeout_users
    timeout_users = []
    get_channels_from_db()
    log('Connected to discord servers!')
    log('logged in as ' + client.user.name)
    log('id ' + str(client.user.id))
    activity = Game('{prefix}help'.format(prefix=config['prefix']))
    await client.change_presence(activity=activity)
    scheduler = AsyncIOScheduler(timezone='Europe/Warsaw')
    scheduler.add_job(stop_receiving_memes, CronTrigger(hour=correct_hour(21), minute=34))
    scheduler.add_job(start_receiving_memes, CronTrigger(hour=correct_hour(21), minute=38))
    scheduler.add_job(prepare_embed, CronTrigger(hour=correct_hour(21), minute=36))
    scheduler.add_job(send_pope_memes, CronTrigger(hour=correct_hour(21), minute=37))
    scheduler.add_job(split_log_file, CronTrigger(hour=correct_hour(0)))
    scheduler.add_job(connect_db, CronTrigger(minute='3-59/5'), args=[False])
    scheduler.add_job(check_channels, CronTrigger(hour='*/1', minute=0))
    scheduler.start()

def split_log_file():
    global logger
    global log_handler
    logger.log(msg = '---End of log---', level = logger.level)
    logger.removeHandler(log_handler)
    log_handler.close()
    if not path_exists(config['old_log_dir']):
        mkdir(config['old_log_dir'])
    move(config['log_file'], path_join(config['old_log_dir'], (datetime.now(tz=timezone('Europe/Warsaw')) - timedelta(days=1)).strftime('kremowka_%Y_%m_%d.log')))
    log_handler = logging.FileHandler(config['log_file'], 'a', 'utf8')
    formatter = logging.Formatter(fmt = '%(levelname)s :: %(asctime)s - %(message)s')
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.log(msg = '---Start of log---', level = logger.level)

def add_user_timeout(user_id):
    global timeout_users
    global scheduler
    timeout_users.append(user_id)
    scheduler.add_job(remove_user_timeout, 'date', run_date=datetime.now(tz=timezone('Europe/Warsaw')) + timedelta(seconds=30), args=[user_id])

def remove_user_timeout(user_id):
    global timeout_users
    timeout_users.remove(user_id)

def remove_server_channel(server_id):
    global channels
    channels.pop(server_id)
    db_cursor.execute('DELETE FROM channels WHERE guild_id=\"{}\"'.format(server_id))
    db_handler.commit()
    log('Removed server with id {}'.format(server_id))

async def check_channels():
    servers_to_remove = []
    for server, channel in channels.items():
        try:
            await client.fetch_guild(server)
        except disc_not_found:
            servers_to_remove.append(server)
        if channel == None:
            servers_to_remove.append(server)
    for server in servers_to_remove:
        remove_server_channel(server)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    try:
        if type(message.channel) == DMChannel and len(message.attachments) > 0:
            if message.author.id in timeout_users:
                await message.channel.send(dictionary['wait_for_downtime'])
                return
            if not memes_ok:
                await message.channel.send(dictionary['wrong_time_for_memes'])
                return
            if len(message.attachments) > 1:
                await message.channel.send(dictionary['seperate_memes_warning'])
                return
            if message.content != "":
                await message.channel.send(dictionary['no_message_warning'])
                return
            meme = message.attachments[0]
            if not meme.filename.endswith('.jpg') and not meme.filename.endswith('.png'):
                await message.channel.send(dictionary['wrong_extension_warning'])
                return
            await receive_file(meme.url, message.author.display_name, message.author.id, message.channel)
            return

        if type(message.channel) == DMChannel and validate_url(message.content):
            if message.author.id in timeout_users:
                await message.channel.send(dictionary['wait_for_downtime'])
                return
            if not message.content.endswith('.jpg') and not message.content.endswith('.png'):
                await message.channel.send(dictionary['wrong_extension_warning'])
                return
            await receive_file(message.content, message.author.display_name, message.author.id, message.channel)
            return

        if not message.content.startswith(config['prefix']):
            return
        content = message.content[len(config['prefix']):]

        if content.lower() == 'config' or content.lower().startswith('config '):
            if type(message.channel) == TextChannel:
                if message.guild.owner_id == message.author.id:
                    perms_ok = True
                elif message.author.guild_permissions.administrator or message.author.guild_permissions.manage_channels:
                    perms_ok = True
                else:
                    perms_ok = False
                if perms_ok:
                    words = content.split(' ', 1)
                    if len(words) <= 1:
                        await message.channel.send(dictionary['wrong_config'].format(prefix=config['prefix']))
                        return
                    channel_id = check_for_channel_id(words[1])
                    if channel_id == False:
                        await message.channel.send(dictionary['no_channel_found'])
                        return
                    success = configure_channel(channel_id, message.guild.id)
                    if not success:
                        await message.channel.send(dictionary['configure_channel_error'])
                        return
                    await message.channel.send(dictionary['configure_channel_success'])
                    return
                else:
                    await message.channel.send(dictionary['no_permission_config'])
                    return
            else:
                await message.channel.send(dictionary['DM_config'])
                return

        if content.lower() == 'check' or content.lower().startswith('check '):
            words = content.split(' ', 1)
            if len(words) <= 1:
                await message.channel.send(dictionary['wrong_check'].format(prefix=config['prefix']))
                return
            if not words[1].isdigit():
                await message.channel.send(dictionary['wrong_id'])
                return
            query = 'SELECT images.status, images.submitted_by FROM images WHERE images.id={0}'.format(words[1])
            db_cursor.execute(query)
            result = db_cursor.fetchone()
            if not result:
                await message.channel.send(dictionary['wrong_id'])
                return
            await message.channel.send(dictionary['status_report'].format(status=statuses[result[0]], meme_id=words[1], author=result[1]))
            return

        if content.lower().startswith('help'):
            await message.channel.send(help_str.format(prefix=config['prefix']))
            return
        
        if content.lower().startswith('about'):
            await message.channel.send(about_str)
            return

        # only for admin
        if message.author.id == config['admin_id']:
            if content == 'off':
                log('Turning off bot')
                await client.close()
            if content == 'meme':
                await prepare_embed()
                await message.channel.send(embed=pope_embed)
            if content == '2137':
                await prepare_embed()
                await send_pope_memes()

    except Exception as e:
        tb = exception_traceback()
        lines = tb.split('\n')
        for line in lines:
            if len(line) == 0:
                continue
            logger.error(line)
        raise e

def main():
    global config
    global dictionary
    global memes_ok
    global statuses
    global help_str
    global about_str
    config = dotenv_values('.env')
    config['admin_id'] = int(config['admin_id'])
    config['time_offset'] = int(config['time_offset'])
    dictionary = dotenv_values(config['dictionary'])
    statuses = dotenv_values(config['statuses'])
    with open(config['help_file'], 'r', encoding='utf8') as file:
        help_str = file.read()
    with open(config['about_file'], 'r', encoding='utf8') as file:
        about_str = file.read()
    memes_ok = True
    logging.addLevelName(15, 'OUTPUT')
    logging.OUTPUT = 15
    set_logger()
    connect_db()
    client.run(config['token'])

if __name__=='__main__':
    main()