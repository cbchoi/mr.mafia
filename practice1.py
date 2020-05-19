import os 
basedir = os.path.abspath(os.path.dirname(__file__)) 

from telegram.ext import Updater, CommandHandler
from instance.credential import *

#사진 보내는 코드 bot.send_photo(chat_id=update.message.chat_id, photo='이미지 주소')

def check_id(bot, update):
	try:
		id=update.message.chat.id
		print('Chat ID',id)
		return id
	except:
		id=update.channel_post.chat.id
		return id

def check_nickname(bot, update):
	try:
		nickname=update.message.from_user.first_name
		print('Chat Nickname',nickname)
		return nickname
	except:
		nickname=update.channel_post.from_user.first_name
		return nickname

def start_command(bot, update):
	id=check_id(bot,update)
	nickname=check_nickname(bot,update)
	bot.send_message(chat_id=id, text='안녕하세요 '+nickname+'! 2020-1 ICT어플리케이션개발 스피드게임 만들기 연습용봇입니다 :)')
	bot.send_message(chat_id=id, text='원하는 메뉴를 입력해주세요.\n1.카테고리 만들기\n2.카테고리 목록 보기\n3.카테고리 선택 하기\n4.게임 시작')

def end_command(bot, update):
	id=check_id(bot,update)
	bot.send_message(chat_id=id, text='시스템을 종료합니다.')
	updater.start_polling.stop()
	updater.stop()

updater=Updater(TOKEN)

updater.dispatcher.add_handler(CommandHandler('start',start_command))
updater.dispatcher.add_handler(CommandHandler('end',end_command))


updater.start_polling(poll_interval=0.0, timeout=10, clean=False, bootstrap_retries=0)

updater.idle()