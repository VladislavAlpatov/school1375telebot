from modules import bot
import os
# Bot(os.environ.get('TOKEN'), os.environ.get('OWN_TOKEN')).run()

if __name__ == '__main__':
    bot.Bot(os.environ.get('TOKEN'), os.environ.get('OWN_TOKEN')).run()
