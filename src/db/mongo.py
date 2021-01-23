import os
from pymongo import MongoClient

client = MongoClient(os.getenv('MONGODB_URL'))
mongo_db = client[os.getenv('MONGO_DATABASE')]
