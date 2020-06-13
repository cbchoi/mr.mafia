import os
import io
import logging
import time
import pymongo
import json
import telegram
import matplotlib.pyplot as plt

from io import BytesIO
from bson import Binary
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, ConversationHandler
from instance.credential import *
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from PIL import Image

conn = pymongo.MongoClient('mongodb://localhost:27017')
db = conn.get_database('speedGame_prac')
basedir = os.path.abspath(os.path.dirname(__file__))
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
selected = dict()
user_state_map = dict()

class Parent():
  def __init__(self):
    pass

  def check_id(self, bot, update):
    try:
       _id=update.message.chat.id
       print('Chat ID',_id)
       return _id
    except:
       _id=update.channel_post.chat.id
       return _id

  def check_nickname(self, bot, update):
    try:
       nickname=update.message.from_user.first_name
       return nickname
    except:
       nickname=update.channel_post.from_user.first_name
       return nickname

  def build_menu(self, buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

  def cancel(self, bot, update):
    bot.send_message(chat_id=update.message.chat_id, 
                      text='취소하셨습니다.\n\n원하는 메뉴를 입력해주세요 ex./make, /select or /delete\
                      \n1.Make category\n2.Select category\n3.Delete category')
    user_state_map[update.message.chat_id] = {}

  def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

class Play(Parent):
  def __init__(self):
    self.id_quiz_map = dict()
    self.start = dict()
    self.index = dict()
    self.num = dict()
    self.show_list=[InlineKeyboardButton("Correct", callback_data="correct"),
                    InlineKeyboardButton("Pass", callback_data="pass"),
                    InlineKeyboardButton("Finish", callback_data="finish")]
    self.show_markup=InlineKeyboardMarkup(self.build_menu(self.show_list, len(self.show_list) - 1))

  def start_command(self, bot, update):
    _id=self.check_id(bot,update)
    collection = db.get_collection(str(_id))
    nickname=self.check_nickname(bot,update)
    user_state_map[_id]=None
    bot.send_message(chat_id=_id, text='안녕하세요 '+nickname+'!\
                    \n2020-1 ICT어플리케이션개발 스피드게임 만들기 연습용봇입니다 삐리삐리\
                    \n언제든 "/cancel"을 입력하시면 main으로 돌아오실 수 있습니다.')
    bot.send_message(chat_id=_id, text='원하는 메뉴를 입력해주세요 ex./make, /select or /delete\
                    \n1.Make category\n2.Select category\n3.Delete category')

  def start_game(self, bot,update):
    _id = self.check_id(bot,update)
    self.id_quiz_map[_id] = [0,0,0]
    collection = db.get_collection(str(_id))
    result = collection.find_one({'name':selected[update.message.chat_id]})
    self.index[update.message.chat_id]=-1
    self.num[update.message.chat_id] = len(result['Item'])
    bot.send_photo(chat_id=update.message.chat.id, 
                  photo=io.BytesIO(result['Item'][self.index[update.message.chat_id]]))
    update.message.reply_text("문제는 총 "+str(self.num[update.message.chat_id])+"개 입니다.\
                            \n그만하려면 finish를 눌러주세요.", 
                            reply_markup=self.show_markup)
    self.start[update.message.chat_id]=time.time()

  def finish(self, bot, update):
    id_quiz_map = self.id_quiz_map
    start = self.start[update.callback_query.message.chat_id]
    end=time.time()
    labels=['pass','correct']
    ratio=[id_quiz_map[update.callback_query.message.chat_id][1],
          id_quiz_map[update.callback_query.message.chat_id][0]]
    plt.pie(ratio, labels=labels, shadow=True, startangle=90)
    plt.savefig('graphIMG.png',dpi=100)
    img=Image.open('graphIMG.png')
    im=io.BytesIO()
    img.save(im, format='PNG')
    bot.edit_message_text(text='게임이 종료되었습니다.\
                          \n다시 시작하시려면 /start를 입력해 메뉴로 돌아가세요.',
                          chat_id=update.callback_query.message.chat_id,
                          message_id=update.callback_query.message.message_id)
    bot.send_photo(chat_id=update.callback_query.message.chat_id,
                  photo=io.BytesIO(im.getvalue()))
    bot.send_message(chat_id=update.callback_query.message.chat_id,
                    text='소요시간 '+str(round(end-start,2))+'초\n패스한 문제: '
                          +str(id_quiz_map[update.callback_query.message.chat_id][1])+'개\n맞춘문제: '
                          +str(id_quiz_map[update.callback_query.message.chat_id][0])+'개')
    user_state_map[update.callback_query.message.chat_id] = {}
    os.remove('graphIMG.png')
    plt.clf()

  def correct(self,bot, update):
    id_quiz_map = self.id_quiz_map
    id_quiz_map[update.callback_query.message.chat_id][0] += 1
    id_quiz_map[update.callback_query.message.chat_id][2] += 1
    if id_quiz_map[update.callback_query.message.chat_id][2]==self.num[update.callback_query.message.chat_id]: 
      self.finish(bot,update)
    data_selected = update.callback_query.data
    collection = db.get_collection(str(update.callback_query.message.chat_id))
    result = collection.find_one({'name':selected[update.callback_query.message.chat_id]})
    if abs(self.index[update.callback_query.message.chat_id]) < self.num[update.callback_query.message.chat_id]:
      self.index[update.callback_query.message.chat_id] -= 1
      bot.send_photo(chat_id=update.callback_query.message.chat_id, 
                    photo=io.BytesIO(result['Item'][self.index[update.callback_query.message.chat_id]]))
      bot.send_message(chat_id=update.callback_query.message.chat_id,
                    text=str(abs(self.index[update.callback_query.message.chat_id]))+'번째사진!',
                    reply_markup=self.show_markup)
      
  def _pass(self, bot, update):
    id_quiz_map = self.id_quiz_map
    id_quiz_map[update.callback_query.message.chat_id][1] += 1
    id_quiz_map[update.callback_query.message.chat_id][2] += 1
    if id_quiz_map[update.callback_query.message.chat_id][2]==self.num[update.callback_query.message.chat_id]:
      self.finish(bot, update)
    data_selected = update.callback_query.data
    collection = db.get_collection(str(update.callback_query.message.chat_id))
    result = collection.find_one({'name':selected[update.callback_query.message.chat_id]})
    if abs(self.index[update.callback_query.message.chat_id]) < self.num[update.callback_query.message.chat_id]:
      self.index[update.callback_query.message.chat_id] -= 1
      bot.send_photo(chat_id=update.callback_query.message.chat_id,
                    photo=io.BytesIO(result['Item'][self.index[update.callback_query.message.chat_id]]))
      bot.send_message(chat_id=update.callback_query.message.chat_id,
                    text=str(abs(self.index[update.callback_query.message.chat_id]))+'번째사진!',
                    reply_markup=self.show_markup)

class Editor(Parent):
  def __init__(self):
    self.photos = {}
    self.name = {}

  def get_category(self, bot, update):
    collection = db.get_collection(str(update.message.chat_id))
    results = collection.find()
    string = ""
    for result in results:
      string += result['name']+'\n'
    return string

  def make_category(self, bot, update):
    _id=self.check_id(bot,update)
    update.message.reply_text('카테고리 이름을 입력해주세요.')
    user_state_map[update.message.chat_id] = 'check_category_name'

  def name_category(self, bot, update):
    self.name[update.message.chat_id] = update.message.text
    collection = db.get_collection(str(update.message.chat_id))
    results = collection.find()
    for result in results:
      if self.name[update.message.chat_id] == result['name']:
        update.message.reply_text('이미 있는 카테고리 이름입니다. 아무내용이나 입력하면 재실행합니다.')
        user_state_map[update.message.chat_id] = {}
        user_state_map[update.message.chat_id] = 'check_category_name'
        return self.name[update.message.chat_id]
    if update.message.text=='/cancel':
      self.cancel(bot,update)
    update.message.reply_text(text="사진을 전송해주세요.")
    user_state_map[update.message.chat_id] = 'push_photos'

  def get_photos(self, bot, update):
    show_list = list()
    show_list.append(InlineKeyboardButton("추가할게!", callback_data="yes"))
    show_list.append(InlineKeyboardButton("그만할게!", callback_data="no"))
    show_markup = InlineKeyboardMarkup(self.build_menu(show_list, len(show_list) - 1))
    update.message.reply_text(text='사진을 더 전송하시겠습니까?.',reply_markup=show_markup)
    if update.message.chat_id not in self.photos:
      self.photos[update.message.chat_id] = []
    self.photos[update.message.chat_id].append(Binary(update.message.photo[-1].get_file().download_as_bytearray()))

  def yes(self, bot, update):
    bot.edit_message_text(text='사진을 전송해주세요.',
                          chat_id=update.callback_query.message.chat_id,
                          message_id=update.callback_query.message.message_id)
    user_state_map[update.callback_query.message.chat_id] = 'push_photos'

  def no(self,bot,update):
    collection = db.get_collection(str(update.callback_query.message.chat_id))
    collection.insert_one({"name":self.name[update.callback_query.message.chat_id],
                          "Item":self.photos[update.callback_query.message.chat_id]})
    self.photos = {}
    bot.edit_message_text(text='종료되었습니다.\n\n원하는 메뉴를 입력해주세요 ex./make, /select, or /delete\
                          \n1.Make category\n2.Select category\n3.Delete category',
                          chat_id=update.callback_query.message.chat_id,
                          message_id=update.callback_query.message.message_id)

  def select_category(self,bot,update):
    collection = db.get_collection(str(update.message.chat_id))
    if collection.estimated_document_count() == 0 : # MongoDB가 비어있다면
        bot.send_message(chat_id=update.message.chat_id,
                        text='저장된 category가 없습니다. 먼저 category를 생성해주시기 바랍니다.')
        self.cancel(bot,update)
        return
    update.message.reply_text('카테고리의 이름을 입력해주세요.')
    string = self.get_category(bot, update)
    update.message.reply_text(string)
    if update.message.text=='/cancel':
      self.cancel(bot,update)
    user_state_map[update.message.chat_id] = 'check_category_list'

  def ready_to_go(self, bot, update):
    selected[update.message.chat_id] = update.message.text
    flag=False
    if selected[update.message.chat_id] == '/cancel':
      self.cancel(bot,update)
    else:
      collection = db.get_collection(str(update.message.chat_id))
      results = collection.find()
      for result in results:
        if selected[update.message.chat_id] == result['name']:
          update.message.reply_text('준비가 완료되었습니다! 게임을 시작하려면 아무내용이나 입력해주세요.')
          flag=True
          user_state_map[update.message.chat_id] = 'game_start'
      if flag==False:
        update.message.reply_text('존재하지 않는 카테고리 이름입니다. 재실행을 위해 /select를 입력해주세요.')

  def delete(self, bot, update):
    collection = db.get_collection(str(update.message.chat_id))
    if collection.estimated_document_count() == 0 : # MongoDB가 비어있다면
        bot.send_message(chat_id=update.message.chat_id, 
                        text='저장된 category가 없습니다. 먼저 category를 생성해주시기 바랍니다.')
        self.cancel(bot,update)
        return 
    update.message.reply_text('어떤 것을 지우기 원합니까? (ID/category/photo)')
    user_state_map[update.message.chat_id] = 'user_input_delete'

  def which_one(self, bot, update):
    which = update.message.text
    if update.message.text=='/cancel':
      self.cancel(bot,update)
    if which == 'ID':
      bot.send_message(chat_id = update.message.chat_id, 
                      text='ID를 선택하셨습니다. 아무내용이나 입력하여 계속 진행해주세요.')
      user_state_map[update.message.chat_id] = 'user_input_delete_ID'
    elif which == 'category':
      bot.send_message(chat_id = update.message.chat_id, 
                      text='category를 선택하셨습니다. 아무내용이나 입력하여 계속 진행해주세요.')
      user_state_map[update.message.chat_id] = 'user_input_delete_category'
    elif which == 'photo':
      bot.send_message(chat_id = update.message.chat_id, 
                      text='photo를 선택하셨습니다. 아무내용이나 입력하여 계속 진행해주세요.')
      user_state_map[update.message.chat_id] = 'user_input_delete_photo_category'
    else:
      update.message.reply_text('잘못입력하셨습니다. (ID/category/photo) 중에 입력해주세요.')

  def which_collection(self, bot, update):
    collection_list = db.list_collection_names()
    bot.send_message(chat_id = update.message.chat_id, 
                    text='ID를 제거하기 원하시다면 ID를 재입력해주시기 바랍니다.')
    update.message.reply_text(str(update.message.chat_id))
    if update.message.text=='/cancel':
      self.cancel(bot,update)
    user_state_map[update.message.chat_id] = 'delete_ID'

  def delete_collection(self, bot, update):
    text = str(update.message.text)
    collection_list = db.list_collection_names()
    if update.message.text=='/cancel':
      self.cancel(bot,update)
    if not text in collection_list:
      update.message.reply_text('잘못입력하셨습니다. 아무내용이나 입력하여 계속 진행해주세요.')
      user_state_map[update.message.chat_id] = 'user_input_delete_ID'
    else:
      delete = db[text]
      delete.drop()
      bot.send_message(chat_id = update.message.chat_id, 
                      text='ID가 제거되었습니다.')
      bot.send_message(chat_id=update.message.chat_id,
                      text='원하는 메뉴를 입력해주세요 ex./make, /select or /delete\
                      \n1.Make category\n2.Select category\n3.Delete category')

  def which_category(self,bot,update):
    bot.send_message(chat_id = update.message.chat_id, text='지우고 싶은 category를 입력해주세요.')
    string = self.get_category(bot,update)
    update.message.reply_text(string)
    if update.message.text=='/cancel':
      self.cancel(bot,update)
    user_state_map[update.message.chat_id] = 'delete_category'

  def delete_category(self,bot,update):
    self.name[update.message.chat_id] = update.message.text
    collection = db.get_collection(str(update.message.chat_id))
    result = collection.find_one({"name":self.name[update.message.chat_id]})
    if result == None:
      update.message.reply_text('잘못입력하셨습니다. 아무내용이나 입력하여 계속 진행해주세요.')
      user_state_map[update.message.chat_id] = 'user_input_delete_category'
    else:
      collection = db.get_collection(str(update.message.chat_id))
      collection.delete_one({'name':self.name[update.message.chat_id]})
      bot.send_message(chat_id = update.message.chat_id, text='삭제되었습니다.')
      bot.send_message(chat_id=update.message.chat_id, 
                      text='원하는 메뉴를 입력해주세요 ex./make, /select or /delete\
                      \n1.Make category\n2.Select category\n3.Delete category')
    if update.message.text=='/cancel':
      self.cancel(bot,update)

  def which_category2(self, bot, update):
    update.message.reply_text('어떤 category의 사진을 지우기 원하시나요?')
    string = self.get_category(bot,update)
    update.message.reply_text(string)
    if update.message.text=='/cancel':
      self.cancel(bot,update)
    user_state_map[update.message.chat_id] = 'user_input_delete_photo'
    
  def which_photo(self, bot, update):
    self.name[update.message.chat_id] = update.message.text
    collection = db.get_collection(str(update.message.chat_id))
    result = collection.find_one({"name":self.name[update.message.chat_id]})
    if result == None:
      update.message.reply_text('잘못입력하셨습니다. 아무내용이나 입력하여 계속 진행해주세요.')
      user_state_map[update.message.chat_id] = 'user_input_delete_photo_category'
    else:
      self.photos[update.message.chat_id] = result['Item']
      index = 0
      for photo in result['Item']:
        im = Image.open(io.BytesIO(photo))
        re_im = im.resize((100,100))
        imgByteArr = io.BytesIO()
        re_im.save(imgByteArr, format='PNG')
        bot.send_message(chat_id=update.message.chat_id, text=str(index+1))
        bot.send_photo(chat_id=update.message.chat_id, 
                      photo=io.BytesIO(imgByteArr.getvalue()))
        index += 1
      bot.send_message(chat_id=update.message.chat_id, 
                      text="지우고 싶은 사진의 번호를 입력해주세요.")
      user_state_map[update.message.chat_id] = 'delete_photo'      
    if update.message.text=='/cancel':
      self.cancel(bot,update)

  def delete_photo(self, bot, update):
    number = update.message.text
    if not number.isdigit(): 
      if int(number) > len(self.photos[update.message.chat_id]) or int(number) < 0:
        update.message.reply_text('잘못입력하셨습니다. 아무내용이나 입력하여 계속 진행해주세요.')
        user_state_map[update.message.chat_id] = 'user_input_delete_photo'
    if update.message.text=='/cancel':
      self.cancel(bot,update)
    collection = db.get_collection(str(update.message.chat_id))
    collection.delete_one({"name":self.name[update.message.chat_id]})
    self.photos[update.message.chat_id].pop(int(number)-1)
    collection.insert_one({"name":self.name[update.message.chat_id], 
                        "Item":self.photos[update.message.chat_id]})
    update.message.reply_text('삭제되었습니다.')
    bot.send_message(chat_id=update.message.chat_id, 
                    text='원하는 메뉴를 입력해주세요 ex./make, /select or /delete\
                    \n1.Make category\n2.Select category\n3.Delete category')
    self.photos[update.message.chat_id], self.name[update.message.chat_id] = list(), None

def CustomMessageDispatcher(bot, update):
  global play
  global editor

  if update.message.chat_id in user_state_map:
    if user_state_map[update.message.chat_id] == 'check_category_name':
      editor.name_category(bot, update)
    elif user_state_map[update.message.chat_id] == 'push_photos':
      editor.get_photos(bot,update)
    elif user_state_map[update.message.chat_id] == 'check_category_list':
      editor.ready_to_go(bot,update)
    elif user_state_map[update.message.chat_id] == 'game_start':
      play.start_game(bot,update)
    elif user_state_map[update.message.chat_id] == 'user_input_delete':
      editor.which_one(bot,update)
    elif user_state_map[update.message.chat_id] == 'user_input_delete_ID':
      editor.which_collection(bot,update)
    elif user_state_map[update.message.chat_id] == 'delete_ID':
      editor.delete_collection(bot,update)
    elif user_state_map[update.message.chat_id] == 'user_input_delete_category':
      editor.which_category(bot,update)
    elif user_state_map[update.message.chat_id] == 'delete_category':
      editor.delete_category(bot,update)
    elif user_state_map[update.message.chat_id] == 'user_input_delete_photo_category':
      editor.which_category2(bot,update)
    elif user_state_map[update.message.chat_id] == 'user_input_delete_photo':
      editor.which_photo(bot,update)
    elif user_state_map[update.message.chat_id] == 'delete_photo':
      editor.delete_photo(bot,update)
    else:
      user_state_map[update.message.chat_id] = None
      update.message.reply_text("/cancel을 눌러 다시 시작해주세요.")
  else:
    update.message.reply_text("잘 못 알아들었어요. 다시 시작해주세요.")

updater=Updater(TOKEN)
play = Play()
editor = Editor()
updater.dispatcher.add_handler(CallbackQueryHandler(play.correct, pattern = 'correct'))
updater.dispatcher.add_handler(CallbackQueryHandler(play._pass, pattern = 'pass'))
updater.dispatcher.add_handler(CallbackQueryHandler(play.finish, pattern = 'finish'))
updater.dispatcher.add_handler(CallbackQueryHandler(editor.yes, pattern = 'yes'))
updater.dispatcher.add_handler(CallbackQueryHandler(editor.no, pattern = 'no'))
updater.dispatcher.add_handler(CommandHandler('start',play.start_command))
updater.dispatcher.add_handler(CommandHandler('make', editor.make_category))
updater.dispatcher.add_handler(CommandHandler('select',editor.select_category))
updater.dispatcher.add_handler(CommandHandler('delete',editor.delete))
updater.dispatcher.add_handler(CommandHandler('cancel',editor.cancel))
updater.dispatcher.add_handler(MessageHandler(Filters.photo, editor.get_photos))
updater.dispatcher.add_handler(MessageHandler(Filters.text, CustomMessageDispatcher))
updater.dispatcher.add_error_handler(play.error)

updater.start_polling(poll_interval=0.0, timeout=10, clean=False, bootstrap_retries=0)

updater.idle() 