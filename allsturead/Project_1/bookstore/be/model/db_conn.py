from be.model import store


class DBConn:
    def __init__(self):
        self.conn = store.get_db_conn()

    def _find_one(self, collection, query):
        try:
            result = self.conn[collection].find_one(query)
            return result is not None
        except Exception as e:
            # throw ERROR msgs if necessary
            print(f"Error in _find_one: {e}")
            return False

    def user_id_exist(self, user_id):
        query = {"user_id": user_id}
        return self._find_one("user_col", query)

    def book_id_exist(self, store_id, book_id):
        query = {"store_id": store_id, "books.book_id": book_id}
        return self._find_one("store_col", query)

    def store_id_exist(self, store_id):
        query = {"store_id": store_id}
        return self._find_one("store_col", query)