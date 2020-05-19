import pymongo,gridfs

String newFileName = "my-image"
File imageFile = File("/practice/image.png"
GridFS gfsPhoto = GridFS(db, "photo")
GridFSInputFile gfsFile = gfsPhoto.createFile(imageFile)
gfsFile.setFilename(newFileName)
gfsFile.save()