import pytest
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book
import uuid

import random

class Testhistoryorder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.buyer_id = "test_check_hist_order_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.buyer_id

        b = register_new_buyer(self.buyer_id, self.password)
        self.buyer = b
        yield

    def test_have_orders(self):
        for i in range(10):
            self.seller_id = "test_check_hist_order_seller_id_{}".format(str(uuid.uuid1()))
            self.store_id = "test_check_hist_order_store_id_{}".format(str(uuid.uuid1()))
            gen_book = GenBook(self.seller_id, self.store_id)
            self.seller = gen_book.seller
            ok, buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
            self.buy_book_info_list = gen_book.buy_book_info_list
            assert ok

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

            code, self.order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
            assert code == 200

            is_cancelled = random.randint(0, 1)
            if is_cancelled == 1:
                code = self.buyer.cancel_order(self.buyer_id, self.order_id)
                assert code == 200
                continue
            else:
                is_paid = random.randint(0, 1)
                if is_paid == 1:
                    code = self.buyer.payment(self.order_id)
                    assert code == 200
                    is_cancelled = random.randint(0, 1)
                    # 发货和收货前
                    if is_cancelled == 1:
                        code = self.buyer.cancel_order(self.buyer_id, self.order_id)
                        assert code == 200
                        continue
                    else:
                        code = self.seller.send_books(self.seller_id, self.order_id)
                        assert code == 200
                        is_cancelled = random.randint(0, 1)
                        # 发货后收货前
                        if is_cancelled == 1:
                            code = self.buyer.cancel_order(self.buyer_id, self.order_id)
                            assert code == 200
                            continue
                        else:
                            code = self.buyer.receive_books(self.buyer_id, self.order_id)
                            assert code == 200
        code = self.buyer.check_hist_order(self.buyer_id)
        assert code == 200

    def test_non_exist_user_id(self):
        code = self.buyer.check_hist_order(self.buyer_id + 'x')
        assert code != 200

    def test_no_orders(self):
        code = self.buyer.check_hist_order(self.buyer_id)
        assert code == 200
