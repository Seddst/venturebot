from telegram.ext import Updater, CommandHandler, MessageHandler

# The token for the bot
TOKEN = '657970619:AAGoqd7cNglxm2yfUdd2t2YYGkOliPPx4t4'


def main():
    """Run the bot."""
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Defining the commands that the bot can handle
    echo_handler = CommandHandler('echo', echo)
    potato_handler = CommandHandler('potato', potato)


    #adding the handlers to the bot so that the bot can use them
    dispatcher.add_handler(echo_handler)
    dispatcher.add_handler(potato_handler)

    #start the bot
    updater.start_polling()

    #make it loop
    updater.idle()



def echo(bot, update):
    """Echo the message the user sent, minus the @bot"""
    update.message.reply_text(" ".join(update.message.text.split(" ")[1:]))


def potato(bot, update):
    update.message.reply_text("Hi look, I iz a potato.")


if __name__ == '__main__':
    main()