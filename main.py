import bot
import os
# Bot(os.environ.get('TOKEN'), os.environ.get('OWN_TOKEN')).run()

if __name__ == '__main__':
    bot.SchoolBot(os.environ.get('TOKEN'), os.environ.get('OWN_TOKEN')).run()
