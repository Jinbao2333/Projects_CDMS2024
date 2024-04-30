from pymongo import MongoClient

class Store:

    def __init__(self, db_path):
        self.clint = MongoClient(db_path)
        self.db = self.client["bookstore"]
        self.init_collections()
    
    def init_collections(self):
        self.user_col = self.db["user"]
        self.store_col = self.db["store"]
        self.book_col = self.db["book"]
        self.detail_col = self.db["detail"]
        self.order_col = self.db["order"]
        
        self.user_col.create_index([("user_id", 1)],unique = True)
        self.store_col.create_index([("store_id", 1)],unique = True)
        self.book_col.create_index([()])
        
database_instance = None

def init_database(dbpath):
    global database_instance
    database_instance = Store(dbpath)

def get_bd_conn():
    global database_instance
    db_path = "mongodb://localhost:27017/"
    database_instance = Store(db_path)
    return database_instance