from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
user = os.getenv("MONGO_USER")
password = os.getenv("MONGO_PASS")

uri = f"mongodb+srv://{user}:{password}@vectordatabase.ufiyeyf.mongodb.net/?retryWrites=true&w=majority&appName=VectorDatabase"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
def get_collection():
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        collection = client["banco_vetorial"]["documentos"]
    except Exception as e:
        print(e)
    return collection