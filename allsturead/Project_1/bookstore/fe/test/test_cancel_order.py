import pytest

from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book
import uuid

class TestCancelOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_cancel_order_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_cancel_order_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_cancel_order_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.buyer_id
        gen_book = GenBook(self.seller_id, self.store_id)
        self.seller = gen_book.seller
        ok, buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        self.buy_book_info_list = gen_book.buy_book_info_list
        self.buy_book_id_list = buy_book_id_list
        assert ok
        b = register_new_buyer(self.buyer_id, self.password)
        self.buyer = b

        self.total_price = 0
        for item in self.buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                self.total_price = self.total_price + book.price * num

        code = self.buyer.add_funds(self.total_price + 1000000)
        assert code == 200
        yield

    def test_paid(self):
        # 已付款
        code, self.order_id = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.buyer.cancel_order(self.buyer_id, self.order_id)
        assert code == 200

    def test_unpaid(self):
        # 未付款
        code, self.order_id = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code = self.buyer.cancel_order(self.buyer_id, self.order_id)
        assert code == 200

    def test_invalid_order_id_paid(self):
        # 已付款，order_id不存在
        code, self.order_id = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.buyer.cancel_order(self.buyer_id, self.order_id + 'x')
        assert code != 200

    def test_invalid_order_id_unpaid(self):
        # 未付款，order_id不存在
        code, self.order_id = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code = self.buyer.cancel_order(self.buyer_id, self.order_id + 'x')
        assert code != 200

    def test_authorization_error_paid(self):
        code, self.order_id = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.buyer.cancel_order(self.buyer_id + 'x', self.order_id)
        assert code != 200

    def test_authorization_error_unpaid(self):
        code, self.order_id = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code = self.buyer.cancel_order(self.buyer_id + 'x', self.order_id)
        assert code != 200

    def test_repeat_cancel_paid(self):
        code, self.order_id = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.buyer.cancel_order(self.buyer_id, self.order_id)
        assert code == 200
        code = self.buyer.cancel_order(self.buyer_id, self.order_id)
        assert code != 200

    def test_repeat_cancel_not_paid(self):
        code, self.order_id = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code = self.buyer.cancel_order(self.buyer_id, self.order_id)
        assert code == 200
        code = self.buyer.cancel_order(self.buyer_id, self.order_id)
        assert code != 200