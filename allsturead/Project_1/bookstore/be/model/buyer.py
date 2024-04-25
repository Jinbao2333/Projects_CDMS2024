import uuid
import json
import logging
from be.model import db_conn
from be.model import error
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
            total_price = 0
            for book_id, count in id_and_count:
                result = self.conn.store_col.find_one({"store_id": store_id, "books.book_id": book_id}, {"books.$": 1})
                if not result:
                    return error.error_non_exist_book_id(book_id) + (order_id,)
                result1 = self.conn.book_col.find_one({"id": book_id})
                stock_level = result["books"][0]["stock_level"]

                price = result1["price"]
                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                result = self.conn.store_col.update_one({"store_id": store_id, "books.book_id": book_id, "books.stock_level": {"$gte": count}},
                                                               {"$inc": {"books.$.stock_level": -count}})

                if result.modified_count == 0:
                    return error.error_stock_level_low(book_id) + (order_id,)

                self.conn.order_detail_col.insert_one({
                    "order_id": uid,
                    "book_id": book_id,
                    "count": count,
                    "price": price
                })

                total_price += price * count
            now_time = datetime.utcnow()
            self.conn.order_col.insert_one({
                "order_id": uid,
                "store_id": store_id,
                "user_id": user_id,
                "create_time": now_time,
                "price": total_price,
                "status": 0
            })
            order_id = uid

        except BaseException as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            result = self.conn.order_col.find_one({"order_id": order_id, "status": 0})
            if result is None:
                return error.error_invalid_order_id(order_id)
            buyer_id = result["user_id"]
            store_id = result["store_id"]
            total_price = result["price"]
            if buyer_id != user_id:
                return error.error_authorization_fail()


            result = self.conn.user_col.find_one({"user_id": buyer_id})
            if result is None:
                return error.error_non_exist_user_id(buyer_id)
            balance = result.get("balance", 0)
            if password != result.get("password", ""):
                return error.error_authorization_fail()


            result = self.conn.store_col.find_one({"store_id": store_id})

            if result is None:
                return error.error_non_exist_store_id(store_id)
            seller_id = result.get("user_id")
            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)


            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)
            result = self.conn.user_col.update_one({"user_id": buyer_id, "balance": {"$gte": total_price}}, {"$inc": {"balance": -total_price}})
            if result.matched_count == 0:
                return error.error_not_sufficient_funds(order_id)


            result = self.conn.user_col.update_one({"user_id": seller_id}, {"$inc": {"balance": total_price}})
            if result.matched_count == 0:
                return error.error_non_exist_user_id(buyer_id)


            self.conn.order_col.insert_one({
                "order_id": order_id,
                "store_id": store_id,
                "user_id": buyer_id,
                "status": 1,
                "price": total_price
            })
            result = self.conn.order_col.delete_one({"order_id": order_id, "status": 0})
            if result.deleted_count == 0:
                return error.error_invalid_order_id(order_id)
        except BaseException as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            result = self.conn.user_col.find_one({"user_id": user_id})
            if result is None:
                return error.error_authorization_fail()
            if result.get("password") != password:
                return error.error_authorization_fail()

            result = self.conn.user_col.update_one({"user_id": user_id}, {"$inc": {"balance": add_value}})
            if result.matched_count == 0:
                return error.error_non_exist_user_id(user_id)
        except BaseException as e:
            return 528, "{}".format(str(e))

        return 200, ""
    
    def receive_books(self, user_id: str, order_id: str) -> (int, str):
        try :
            result = self.conn.order_col.find_one({
                "$or": [
                    {"order_id": order_id, "status": 1},
                    {"order_id": order_id, "status": 2},
                    {"order_id": order_id, "status": 3},
                ]
            })
            if result == None:
                return error.error_invalid_order_id(order_id)
            buyer_id = result.get("user_id")
            paid_status = result.get("status")

            if buyer_id != user_id:
                return error.error_authorization_fail()
            if paid_status == 1:
                return error.error_books_not_sent()
            if paid_status == 3:
                return error.error_books_repeat_receive()

            self.conn.order_col.update_one({"order_id": order_id}, {"$set": {"status": 3}})
        except BaseException as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def cancel_order(self, user_id: str, order_id: str) -> (int, str):
        try:
            # 未付款
            result = self.conn.order_col.find_one({"order_id": order_id, "status": 0})
            if result:
                buyer_id = result.get("user_id")
                if buyer_id != user_id:
                    return error.error_authorization_fail()
                store_id = result.get("store_id")
                price = result.get("price")
                self.conn.order_col.delete_one({"order_id": order_id, "status": 0})
            # 已付款
            else:
                result = self.conn.order_col.find_one({
                    "$or": [
                        {"order_id": order_id, "status": 1},
                        {"order_id": order_id, "status": 2},
                        {"order_id": order_id, "status": 3},
                    ]
                })
                if result:
                    buyer_id = result.get("user_id")
                    if buyer_id != user_id:
                        return error.error_authorization_fail()
                    store_id = result.get("store_id")
                    price = result.get("price")

                    result1 = self.conn.store_col.find_one({"store_id": store_id})

                    if result1 is None:
                        return error.error_non_exist_store_id(store_id)
                    seller_id = result1.get("user_id")

                    result2 = self.conn.user_col.update_one({"user_id": seller_id}, {"$inc": {"balance": -price}})
                    if result2 is None:
                        return error.error_non_exist_user_id(seller_id)


                    result3 = self.conn.user_col.update_one({"user_id": buyer_id}, {"$inc": {"balance": price}})
                    if result3 is None:
                        return error.error_non_exist_user_id(user_id)

                    result4 = self.conn.order_col.delete_one({
                    "$or": [
                        {"order_id": order_id, "status": 1},
                        {"order_id": order_id, "status": 2},
                        {"order_id": order_id, "status": 3},
                    ]
                })
                    if result4 is None:
                        return error.error_invalid_order_id(order_id)

                else:
                    return error.error_invalid_order_id(order_id)

            # recovery the stock
            result = self.conn.order_detail_col.find({"order_id": order_id})
            for book in result:
                book_id = book["book_id"]
                count = book["count"]
                result1 = self.conn.store_col.update_one({"store_id": store_id, "books.book_id": book_id}, {"$inc": {"books.$.stock_level": count}})
                if result1.modified_count == 0:
                    return error.error_stock_level_low(book_id) + (order_id,)

            self.conn.order_col.insert_one({"order_id": order_id, "user_id": user_id, "store_id": store_id, "price": price, "status": 4})
        except BaseException as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def check_hist_order(self, user_id: str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            ans = []
            # 未付款
            result = self.conn.order_col.find({"user_id": user_id, "status": 0})
            if result:
                for order in result:
                    tmp_details = []
                    order_id = order.get("order_id")
                    order_detail_result = self.conn.order_detail_col.find({"order_id": order_id})

                    if order_detail_result:
                        for order_detail in order_detail_result:
                            tmp_details.append({
                                "book_id": order_detail.get("book_id"),
                                "count": order_detail.get("count"),
                                "price": order_detail.get("price")
                            })
                    else:
                        return error.error_invalid_order_id(order_id)

                    ans.append({
                        "status": "unpaid",
                        "order_id": order_id,
                        "buyer_id": order.get("user_id"),
                        "store_id": order.get("store_id"),
                        "total_price": order.get("price"),
                        "details": tmp_details
                    })
            # 已付款
            books_status_list = ["unsent", "sent but not received", "received"]
            result = self.conn.order_col.find({
                "$or": [
                    {"user_id": user_id, "status": 1},
                    {"user_id": user_id, "status": 2},
                    {"user_id": user_id, "status": 3},
                ]
            })
            if result:
                for i in result:
                    tmp_details = []
                    order_id = i.get("order_id")
                    order_detail_result = self.conn.order_detail_col.find({"order_id": order_id})
                    if order_detail_result:
                        for order_detail in order_detail_result:
                            tmp_details.append({
                                "book_id": order_detail.get("book_id"),
                                "count": order_detail.get("count"),
                                "price": order_detail.get("price")
                            })
                    else:
                        return error.error_invalid_order_id(order_id)
                    ans.append({
                        "order_id": order_id,
                        "buyer_id": i.get("user_id"),
                        "store_id": i.get("store_id"),
                        "total_price": i.get("price"),
                        "status": books_status_list[i.get("status") - 1],
                        "details": tmp_details
                    })
            # 已取消
            result = self.conn.order_col.find({"user_id": user_id, "status": 4})
            if result:
                for order_cancel in result:
                    tmp_details = []
                    order_id = order_cancel.get("order_id")
                    order_detail_result = self.conn.order_detail_col.find({"order_id": order_id})
                    if order_detail_result:
                        for order_detail in order_detail_result:
                            tmp_details.append({
                                "book_id": order_detail.get("book_id"),
                                "count": order_detail.get("count"),
                                "price": order_detail.get("price")
                            })
                    else:
                        return error.error_invalid_order_id(order_id)

                    ans.append({
                        "status": "cancelled",
                        "order_id": order_id,
                        "buyer_id": order_cancel.get("user_id"),
                        "store_id": order_cancel.get("store_id"),
                        "total_price": order_cancel.get("price"),
                        "details": tmp_details
                    })

        except BaseException as e:
            return 528, "{}".format(str(e))
        if not ans:
            return 200, "ok", "No orders found "
        else:
            return 200, "ok", ans

    def auto_cancel_order(self) -> (int, str):
        try:
            wait_time = 20  # 等待时间20s
            interval = datetime.utcnow() - timedelta(seconds=wait_time) # UTC时间
            orders_to_cancel = self.conn.order_col.find({"create_time": {"$lte": interval}, "status": 0})
            if orders_to_cancel:
                for order in orders_to_cancel:
                    order_id = order["order_id"]
                    user_id = order["user_id"]
                    store_id = order["store_id"]
                    price = order["price"]
                    self.conn.order_col.delete_one({"order_id": order_id, "status": 0})
                    result = self.conn.order_detail_col.find({"order_id": order_id})

                    for book in result:
                        book_id = book["book_id"]
                        count = book["count"]
                        result1 = self.conn.store_col.update_one({"store_id": store_id, "books.book_id": book_id}, {"$inc": {"books.$.stock_level": count}})
                        if result1.modified_count == 0:
                            return error.error_stock_level_low(book_id) + (order_id,)

                    self.conn.order_col.insert_one({"order_id": order_id, "user_id": user_id,"store_id": store_id, "price": price, "status": 4})
        except BaseException as e:
            return 528, "{}".format(str(e))
        return 200, "ok"

    def is_order_cancelled(self, order_id: str) -> (int, str):
        result = self.conn.order_col.find_one({"order_id": order_id, "status": 4})
        if result is None:
            return error.error_auto_cancel_fail(order_id)
        else:
            return 200, "ok"

    def search(self, keyword, store_id=None, page=1, per_page=10):
        try:
            query = {"$text": {"$search": keyword}}
            if store_id:
                result1 = self.conn.store_col.find({"store_id": store_id}, {"books.book_id": 1, "_id": 0})
                for result in result1:
                    print(result)
                books_id = [i["book_id"] for i in result1["books"]]
                query["id"] = {"$in": books_id}

            result = self.conn.book_col.find(query,
                                              {"score": {"$meta": "textScore"}, "_id": 0, "picture": 0}).sort(
                [("score", {"$meta": "textScore"})])

            result.skip((int(page) - 1) * per_page).limit(per_page)
        except BaseException as e:
            return 530, f"{str(e)}"
        return 200, list(result)


scheduler = BackgroundScheduler()
scheduler.add_job(Buyer().auto_cancel_order, 'interval', id='5_second_job', seconds=5)
scheduler.start()