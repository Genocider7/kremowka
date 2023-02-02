import discord, mysql.connector
from dotenv import dotenv_values
from datetime import datetime
from pytz import timezone
from random import choice
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

client = discord.Client()
pope_embed = None
hour_offset = 0

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
    print('Connected to mysql database!')

def get_random_image():
    db_cursor.execute('SELECT count(*) FROM images')
    count = db_cursor.fetchone()
    count = count[0]
    limit = max(1, (int)(count/20))
    db_cursor.execute('SELECT images.id AS id, images.url AS url, images.submitted_by AS author FROM images ORDER BY images.last_used, RAND() LIMIT ' + str(limit))
    pick = choice(db_cursor.fetchall())
    db_cursor.execute('UPDATE images SET images.last_used=\'' + datetime.now().strftime('%Y-%m-%d') + '\' WHERE id=' + str(pick[0]))
    db_handler.commit()
    return (pick[1], pick[2])

def get_image_embed(image):
    global pope_embed
    (url, author) = image
    pope_embed = discord.Embed()
    pope_embed.set_image(url=url)
    pope_embed.set_footer(text='Submitted by ' + author)

async def prepare_embed():
    image = get_random_image()
    get_image_embed(image)

def fix_hour(hour):
    if hour < 0:
        hour += 24
    if hour > 23:
        hour -= 24
    return hour

def set_time_offset():
    global hour_offset
    raw_polish_offset = datetime.now().astimezone(timezone('Europe/Warsaw')).strftime('%z')
    raw_local_offset = datetime.now().astimezone(timezone('CET')).strftime('%z')
    polish_offset = int(raw_polish_offset[:3])
    local_offset = int(raw_local_offset[:3])
    hour_offset = local_offset - polish_offset

async def send_pope_memes():
    print('It\'s 21:37 my dudes!')

@client.event
async def on_ready():
    print('Connected to discord servers!')
    print('logged in as ' + client.user.name)
    print('id ' + str(client.user.id))
    scheduler = AsyncIOScheduler()
    scheduler.add_job(prepare_embed, CronTrigger(hour=fix_hour(21 + hour_offset), minute=30, second=0))
    scheduler.add_job(send_pope_memes, CronTrigger(hour=fix_hour(21 + hour_offset), minute=37, second=0))
    scheduler.start()

@client.event
async def on_message(message):
    if not message.content.startswith(config['prefix']):
        return
    content = message.content[len(config['prefix']):]
    if message.author.id == config['admin_id']:
        if content == 'off':
            await client.close()
        if content == 'meme':
            await prepare_embed()
            await message.channel.send(embed=pope_embed)

def main():
    global config
    config = dotenv_values('.env')
    config['admin_id'] = int(config['admin_id'])
    set_time_offset()
    connect_db()
    client.run(config['token'])

if __name__=='__main__':
    main()