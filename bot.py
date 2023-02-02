import discord
from dotenv import dotenv_values

client = discord.Client()

@client.event
async def on_ready():
    print('Connected to discord servers!')
    print('logged in as ' + client.user.name)
    print('id ' + str(client.user.id))

@client.event
async def on_message(message):
    if not message.content.startswith(config['prefix']):
        return
    content = message.content[len(config['prefix']):]
    if message.author.id == config['admin_id']:
        if content == 'off':
            await client.close()

def main():
    global config
    config = dotenv_values('.env')
    config['admin_id'] = int(config['admin_id'])
    client.run(config['token'])

if __name__=='__main__':
    main()