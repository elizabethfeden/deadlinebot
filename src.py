from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
						  ConversationHandler, PicklePersistence)

# google calendar api imports
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# LOGGING
import logging

logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
	level=logging.DEBUG)
logging.basicConfig(filename = 'log.txt', level = logging.DEBUG)
logger = logging.getLogger(__name__)

# TOKEN
TOKEN = "1271896830:AAEWHqxdIyICnm7sw5RcugCj1gGeKeC343M"

# FIRST STEPS FUNCTIONS
def start(update, context):
	text = "хелоу, я собрал тебе дедлайны!\n" \
		"жмакни /help, чтобы получить полный список команд."
	context.bot.send_message(chat_id = update.message.chat_id, text = text)

def help(update, context):
	context.bot.send_message(chat_id = update.message.chat_id, text = """
		вот, что я умею делать:
		/sendsticker
		/getcurevent
		/getnextevent
		/nextdeadline
		/listdeadlines
		/adddeadline
		/api
		""")

import random
def send_sticker(update, context):
	stickers = context.bot.get_sticker_set('ShkyaPack').stickers
	context.bot.send_sticker(chat_id = update.message.chat_id,
		sticker = stickers[random.randint(0, len(stickers) - 1)].file_id)

def default(update, context):
	# специально сломать бота:
	#context.bot.send_message(update.message.chat_id, 'a'*40960)
	
	if update.message.text != None:
		update.message.reply_text(update.message.text)
	else:
		update.message.reply_text("не надо мне этих ваших медиа...")

def error(update, context):
	update.message.reply_text("что-то пошло не так :(")
	logger.error('Update "%s" caused error "%s"', update, context.error)

# GOOGLE CALENDAR FUNCTIONS
def get_cur_event(update, context):
	# взаимодействие с api
	update.message.reply_text("в данный момент мы флексим")

def get_next_event(update, context):
	# взаимодействие с api
	update.message.reply_text("потом мы флексим")

def next_deadline(update, context):
	# взаимодействие с api
	update.message.reply_text("дедлайнов не существует")

def list_deadlines(update, context):
	# взаимодействие с api
	update.message.reply_text("дедлайнов не существует")

# ADD DEADLINE CONVERSATION
DATE, NAME, DESCRIPTION = range(3)

def ad_start(update, context):
	update.message.reply_text("введи дату дедлайна в формате:\nhh:mm dd/mm")
	return DATE

def ad_date(update, context):
	# parse date
	context.user_data['ad_date'] = update.message.text

	keyboard = ReplyKeyboardMarkup([['га', 'прога', 'матан', 'дм']], resize_keyboard = True)
	update.message.reply_text("выбери название дедлайна (либо напечатай какое-то другое)",
		reply_markup = keyboard)
	return NAME

def ad_name(update, context):
	context.user_data['ad_name'] = update.message.text
	update.message.reply_text("оставь описание", reply_markup = ReplyKeyboardRemove())
	return DESCRIPTION

def ad_description(update, context):
	# add event to google calendar...
	context.bot.send_message(chat_id = update.message.chat_id,
		text = "{}: {}\n{}".format(context.user_data['ad_date'],
		context.user_data['ad_name'], update.message.text))

	update.message.reply_text("готово!")
	return ConversationHandler.END

def cancel(update, context):
	update.message.reply_text("гаааляяяяя, отмеееена!", reply_markup = ReplyKeyboardRemove())
	return ConversationHandler.END




def main():
	pp = PicklePersistence(filename = 'conversationbot')
	updater = Updater(token = TOKEN, persistence = pp, use_context = True)
	dp = updater.dispatcher
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(CommandHandler('help', help))
	dp.add_handler(CommandHandler('sendsticker', send_sticker))
	dp.add_handler(CommandHandler('getcurevent', get_cur_event))
	dp.add_handler(CommandHandler('getnextevent', get_next_event))
	dp.add_handler(CommandHandler('nextdeadline', next_deadline))
	dp.add_handler(CommandHandler('listdeadlines', list_deadlines))

	add_deadline_handler = ConversationHandler(
		entry_points = [CommandHandler('adddeadline', ad_start)],

		states = {
			DATE: [MessageHandler(Filters.text, ad_date)],
			NAME: [MessageHandler(Filters.text, ad_name)],
			DESCRIPTION: [MessageHandler(Filters.text, ad_description)]
		},

		fallbacks = [ CommandHandler('cancel', cancel) ],
		name = "adddeadline",
		persistent = True
	)

	dp.add_handler(add_deadline_handler)

	#dp.add_handler(CommandHandler('api', api))
	dp.add_handler(MessageHandler(Filters.all, default))
	dp.add_error_handler(error)

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()



SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
def api(update, context):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        update.message.reply_text('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        update.message.reply_text(start + event['summary'])