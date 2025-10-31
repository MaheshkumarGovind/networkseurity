from urllib.parse import quote_plus
from pymongo.mongo_client import MongoClient

password = quote_plus("SQIUqxeaAsPvJpKm")  # encode password
uri = f"mongodb+srv://Mahesh:{password}@cluster0.rdi9pwm.mongodb.net/?appName=Cluster0"

client = MongoClient(uri)

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
