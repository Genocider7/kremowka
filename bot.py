from warnings import filterwarnings
filterwarnings('ignore') #pytz raises a very irritating warning because of apscheduler

import discord, mysql.connector, requests, validators, logging
from dotenv import dotenv_values
from datetime import datetime, timedelta
from random import choice
from pytz import timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from hashlib import md5

intents = discord.Intents.default()
intents.guilds = True
client = discord.Client(intents=intents)
pope_embed = None
channels = {}
logger = None

def set_logger():
    global logger
    logger = logging.getLogger()
    logger.setLevel(logging.OUTPUT)
    handler = logging.FileHandler(config['log_file'], 'a', 'utf8')
    formatter = logging.Formatter(fmt = '%(levelname)s :: %(asctime)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def log(message):
    logger.log(msg = message, level = logger.level)
    print(message)

def connect_db():
    global db_handler
    global db_cursor
    db_handler = mysql.connector.connect(
        host='localhost',
        user=config['db_username'],
        password=config['db_password'],
        database=config['database']
    )
    db_cursor = db_handler.cursor()
    log('Connected to mysql database!')

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
    pope_embed = discord.Embed()
    pope_embed.set_image(url=url)
    pope_embed.set_footer(text=dictionary['embed_footer'].format(author_name=author))

async def prepare_embed():
    image = get_random_image()
    get_image_embed(image)

async def send_pope_memes():
    for channel in channels.values():
        await channel.send(embed=pope_embed)

async def stop_receiving_memes():
    global memes_ok 
    memes_ok = False

async def start_receiving_memes():
    global memes_ok 
    memes_ok = True

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
    extension = url[-3:]
    basename = md5((str(author_id) + str(datetime.now())).encode()).hexdigest()
    with open(config['save_directory'] + basename + '.' + extension, 'wb') as file:
        file.write(requests.get(url).content)
    db_cursor.execute('INSERT INTO images (basename, extension, submitted_by, submitted_by_id) VALUES (\"' + basename + '\", \"' + extension + '\", \"' + author_name + '\", \"' + str(author_id) + '\")')
    db_handler.commit()
    db_cursor.execute('SELECT images.id AS id FROM images WHERE images.basename=\"' + basename + '\" ORDER BY images.id DESC LIMIT 1')
    result = db_cursor.fetchone()
    id = result[0]
    await where_to_send.send(dictionary['meme_sent'].format(meme_id=id)) #TODO do something with that id (checking status for example)
    add_user_timeout(author_id)

@client.event
async def on_ready():
    global Mainscheduler
    global timeout_users
    timeout_users = []
    get_channels_from_db()
    log('Connected to discord servers!')
    log('logged in as ' + client.user.name)
    log('id ' + str(client.user.id))
    Mainscheduler = AsyncIOScheduler(timezone='Europe/Warsaw')
    Mainscheduler.add_job(stop_receiving_memes, CronTrigger(hour=21, minute=35, second=0))
    Mainscheduler.add_job(start_receiving_memes, CronTrigger(hour=21, minute=40, second=0))
    Mainscheduler.add_job(prepare_embed, CronTrigger(hour=21, minute=30, second=0))
    Mainscheduler.add_job(send_pope_memes, CronTrigger(hour=21, minute=37, second=0))
    Mainscheduler.start()

def add_user_timeout(user_id):
    global timeout_users
    global Mainscheduler
    timeout_users.append(user_id)
    Mainscheduler.add_job(remove_user_timeout, 'date', run_date=datetime.now(tz=timezone('Europe/Warsaw')) + timedelta(minutes=10), args=[user_id])

def remove_user_timeout(user_id):
    global timeout_users
    timeout_users.remove(user_id)

@client.event
async def on_message(message):
    if type(message.channel) == discord.DMChannel and len(message.attachments) > 0:
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

    if type(message.channel) == discord.DMChannel and validators.url(message.content):
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
        if type(message.channel) == discord.TextChannel:
            if message.guild.owner_id == message.author.id:
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

    # only for admin
    if message.author.id == config['admin_id']:
        if content == 'off':
            await client.close()
        if content == 'meme':
            await prepare_embed()
            await message.channel.send(embed=pope_embed)
        if content == '2137':
            await prepare_embed()
            await send_pope_memes()

def main():
    global config
    global dictionary
    global memes_ok
    config = dotenv_values('.env')
    config['admin_id'] = int(config['admin_id'])
    dictionary = dotenv_values(config['dictionary'])
    memes_ok = True
    logging.addLevelName(5, 'OUTPUT')
    logging.OUTPUT = 5
    set_logger()
    connect_db()
    client.run(config['token'])

if __name__=='__main__':
    main()