from config import DB_URL, DB_NAME
from pymongo import MongoClient 

# mongodb credentials 
client = MongoClient(DB_URL) 
db = client[DB_NAME] 
collection = db["config"] 

def save_channel_id(channel_id: int):
  config_collection.find_one_and_update(
    {"_id": "channel"},
    {"$set": {"channel_id": channel_id}},
    upsert=True, 
    return_document=True
  )
  
def get_channel_id():
  doc = config_collection.find_one({"_id": "channel"}) 
  return doc["channel_id"] if doc else None