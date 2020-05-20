import pymongo
import telegram

conn = pymongo.MongoClient('mongodb://db:27017')
db = conn.get_database('flames')

from gridfs import GridFS
from gridfs.errors import NoFile
from instance.credential import *
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename

fs = GridFS(db)

updates = telegram.Bot(TOKEN).get_updates() #업데이트 내역을 받아옵니다

filename = secure_filename(form.file.data.filename) 
oid = fs.put(form.file.data, content_type=form.file.data.content_type, filename=filename)
now = datetime.now()
enddate=now+relativedelta(days=+1)
item = Item(iname=form.iname.data, price=form.price.data, req=form.req.data, file=filename, hash_data=form.hash.data.split(";"),date=enddate.strftime('%Y-%m-%d %H:%M:%S'))
collection = db.get_collection('items')
collection.insert_one(item.to_dict())

print([u.message.photo for u in updates if u.message.photo]) #내역중 메세지를 출력합니다.