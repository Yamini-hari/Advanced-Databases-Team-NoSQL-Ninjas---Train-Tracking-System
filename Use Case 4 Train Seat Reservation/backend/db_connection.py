from neo4j import GraphDatabase
from pymongo import MongoClient

# Define your Neo4j connection details
neo_uri = "bolt://localhost:7687"
neo_username = "neo4j"
neo_password = "12345678"
neo_database = "neo4j" 

# Define your Neo4j connection details
mongo_uri = "mongodb://localhost:27017"
mongo_database="seats_management"
 

def neo_connection():
    # Connect to the Neo4j database
    driver = GraphDatabase.driver(neo_uri, auth=(neo_username, neo_password), database=neo_database)
    session = driver.session()
    return session

class MongoDBConnection:
 
    def __init__(self, uri, database, user=None, password=None):
        self._uri = uri
        self._database_name = database
        self._user = user
        self._password = password
        self._client = None
        self._database = None
        self._collection = None
 
    def connect(self):
        self._client = MongoClient(self._uri, username=self._user, password=self._password)
        self._database = self._client[self._database_name]
 
    def close(self):
        if self._client is not None:
            self._client.close()
 
    def query(self, collection_name, query):
        collection = self._database[collection_name]
        result = collection.find(query)
        return list(result)
    
    def aggregate(self, collection_name, pipeline):
        collection = self._database[collection_name]
        result = collection.aggregate(pipeline)
        return list(result)
    
    def insert(self, collection_name, document):
        collection = self._database[collection_name]
        result = collection.insert_one(document)
        return result.inserted_id
    
    def update_booking(self, collection_name, query, update):
        collection = self._database[collection_name]
        collection.update_one(query, {"$set": update})
        
# Create a MongoDB connection and execute the query
mongo_connection = MongoDBConnection(uri=mongo_uri, database=mongo_database)
mongo_connection.connect()