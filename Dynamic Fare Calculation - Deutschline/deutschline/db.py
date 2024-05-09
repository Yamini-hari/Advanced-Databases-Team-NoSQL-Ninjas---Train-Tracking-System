from neo4j import GraphDatabase
from pymongo import MongoClient

class Neo4jConnection:
 
    def __init__(self, uri, user, password, database=None):
        self._uri = uri
        self._user = user
        self._password = password
        self._database = database
        self._driver = None
 
    def connect(self):
        if self._database:
            uri = f"{self._uri}/db/{self._database}"
        else:
            uri = self._uri
        self._driver = GraphDatabase.driver(uri, auth=(self._user, self._password))
 
    def close(self):
        if self._driver is not None:
            self._driver.close()
 
    def query(self, cypher_query, parameters=None):
        with self._driver.session() as session:
            result = session.run(cypher_query, parameters)
            return result.data()

# Create a Neo4j connection and execute the query
neo4j_connection = Neo4jConnection(uri="neo4j://localhost:7687", user="neo4j", password="12345678")
neo4j_connection.connect()

class MongoDBConnection:
 
    def __init__(self, uri, database, user=None, password=None):
        self._uri = uri
        self._database_name = database
        self._user = user
        self._password = password
        self._client = None
        self._database = None
 
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
    
    def insert(self, collection_name, data):
        collection = self._database[collection_name]
        result = collection.insert_one(data)
        return result
    
# Create a MongoDB connection and execute the query
mongo_connection = MongoDBConnection(uri="mongodb://localhost:27017", database="test")
mongo_connection.connect()
