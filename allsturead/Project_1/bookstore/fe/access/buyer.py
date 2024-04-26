import requests
import simplejson
from urllib.parse import urljoin
from fe.access.auth import Auth


class Buyer:
    def __init__(self, url_prefix, user_id, password):
        self.url_prefix = urljoin(url_prefix, "buyer/")
        self.user_id = user_id
        self.password = password
        self.token = ""
        self.terminal = "my terminal"
        self.auth = Auth(url_prefix)
        code, self.token = self.auth.login(self.user_id, self.password, self.terminal)
        assert code == 200

    def new_order(self, store_id: str, book_id_and_count: [(str, int)]) -> (int, str):
        books = []
        for id_count_pair in book_id_and_count:
            books.append({"id": id_count_pair[0], "count": id_count_pair[1]})
        json = {"user_id": self.user_id, "store_id": store_id, "books": books}
        url = urljoin(self.url_prefix, "new_order")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return r.status_code, response_json.get("order_id")

    def payment(self, order_id: str):
        json = {"user_id": self.user_id, "password": self.password, "order_id": order_id, }
        url = urljoin(self.url_prefix, "payment")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_funds(self, add_value: str) -> int:
        json = {"user_id": self.user_id, "password": self.password, "add_value": add_value, }
        url = urljoin(self.url_prefix, "add_funds")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

# other func:

    def receive_books(self, user_id: str, order_id: str) -> int:
        json = {"user_id": user_id, "order_id": order_id}
        url = urljoin(self.url_prefix, "receive_books")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def cancel_order(self, user_id: str, order_id: str) -> int:
        json = {"user_id": user_id, "order_id": order_id}
        url = urljoin(self.url_prefix, "cancel_order")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def auto_cancel_order(self, order_id: str) -> int:
        json = {"order_id": order_id}
        url = urljoin(self.url_prefix, "auto_cancel_order")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def is_order_cancelled(self, order_id: str) -> int:
        json = {"order_id": order_id}
        url = urljoin(self.url_prefix, "is_order_cancelled")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def check_hist_order(self, user_id: str) -> int:
        json = {"user_id": user_id}
        url = urljoin(self.url_prefix, "check_hist_order")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def search(self, keyword, store_id=None, page=1):
        # store
        json = {
            "keyword": keyword,
            "page": page
        }
        if store_id:
            json["store_id"] = store_id

        url = urljoin(self.url_prefix, "search")
        r = requests.post(url, json=json)
        return r.content, r.status_code