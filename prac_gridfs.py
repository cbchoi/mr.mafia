import pymongo
import telegram

conn = pymongo.MongoClient('mongodb://localhost:27017')
db = conn.get_database('mafia')

#from gridfs import GridFS
#from gridfs.errors import NoFile

#fs = GridFS(db)
#updates = telegram.Bot(TOKEN).get_updates() #업데이트 내역을 받아옵니다

#filename = secure_filename(form.file.data.filename) 
filename = './11.py'
f = open('./11.py', 'rb')
oid = fs.put(f.read(), filename=filename)


#now = datetime.now()
#enddate=now+relativedelta(days=+1)
#item = Item(iname=form.iname.data, price=form.price.data, req=form.req.data, file=filename, hash_data=form.hash.data.split(";"),date=enddate.strftime('%Y-%m-%d %H:%M:%S'))
#collection = db.get_collection('items')
#collection.insert_one(item.to_dict())
print(fs.get(oid).read())
#rint([u.message.photo for u in updates if u.message.photo]) #내역중 메세지를 출력합니다.
