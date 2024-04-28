import json
import pytest
import uuid
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
from fe.access.search import RequestSearch
from fe.access import book


class TestSearch:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.buyer_id = "test_new_search_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = "test_new_search_buyer_id_{}".format(str(uuid.uuid1()))
        self.buyer = register_new_buyer(self.buyer_id, self.password)

        self.user_id = "test_crete_store_user_{}".format(str(uuid.uuid1()))
        self.store_id = "test_create_store_store_{}".format(str(uuid.uuid1()))
        self.password = self.user_id
        self.seller = register_new_seller(self.user_id, self.password)
        code = self.seller.create_store(self.store_id)
        assert code == 200
        self.keyword = "hello"
        self.rs = RequestSearch()
        book_db = book.BookDB()
        self.book_example = book_db.get_book_info(0, 1)[0]

    def test_all_field_search(self):
        content, code = self.buyer.search(self.keyword)
        content = json.loads(content)['message']
        print(content, len(content))
        assert code == 200

    def test_pagination(self):
        content, code = self.buyer.search(self.keyword, page=2)
        assert code == 200

    def test_search_title(self):
        title = f"hello_{str(uuid.uuid1())}"
        self.book_example.title = title
        code = self.seller.add_book(self.store_id, 0, self.book_example)
        assert code == 200

        code = self.rs.request_search_title(title=title)
        assert code == 200

        code = self.rs.request_search_title(title=title + "x")
        assert code == 501

    def test_search_title_in_store(self):
        title = f"hello_{str(uuid.uuid1())}"
        self.book_example.title = title
        self.seller.add_book(self.store_id, 0, self.book_example)

        code = self.rs.request_search_title_in_store(title=title, store_id=self.store_id)
        assert code == 200

        code = self.rs.request_search_title_in_store(title=title + "x",
                                                     store_id=self.store_id)
        assert code == 501

    def test_search_tag(self):
        tag = f"hello_{str(uuid.uuid1())}"
        self.book_example.tags = [tag]
        self.seller.add_book(self.store_id, 0, self.book_example)

        code = self.rs.request_search_tag(tag=tag)
        assert code == 200

        code = self.rs.request_search_tag(tag=tag + "x")
        assert code == 501

    def test_search_tag_in_store(self):
        tag = f"hello_{str(uuid.uuid1())}"
        self.book_example.tags = [tag]
        self.seller.add_book(self.store_id, 0, self.book_example)

        code = self.rs.request_search_tag_in_store(tag=tag, store_id=self.store_id)
        assert code == 200

        code = self.rs.request_search_tag_in_store(tag=tag + "x", store_id=self.store_id)
        assert code == 501

    def test_search_author(self):
        author = f"hello_{str(uuid.uuid1())}"
        self.book_example.author = author
        self.seller.add_book(self.store_id, 0, self.book_example)

        code = self.rs.request_search_author(author=author)
        assert code == 200

        code = self.rs.request_search_author(author=author + "x")
        assert code == 501

    def test_search_author_in_store(self):
        author = f"hello_{str(uuid.uuid1())}"
        self.book_example.author = author
        self.seller.add_book(self.store_id, 0, self.book_example)

        code = self.rs.request_search_author_in_store(author=author, store_id=self.store_id)
        assert code == 200

        code = self.rs.request_search_author_in_store(author=author + "x",
                                                      store_id=self.store_id)
        assert code == 501

    def test_search_content(self):
        key = "hello11"
        book_intro = f"{str(uuid.uuid1())} {key} {str(uuid.uuid1())}"
        self.book_example.book_intro = book_intro
        self.seller.add_book(self.store_id, 0, self.book_example)

        code = self.rs.request_search_content(content=key)
        assert code == 200

        code = self.rs.request_search_content(content=key + "x")
        assert code == 501

    def test_search_content_in_store(self):
        key = "hello12"
        book_intro = f"{str(uuid.uuid1())} {key} {str(uuid.uuid1())}"
        self.book_example.book_intro = book_intro
        self.seller.add_book(self.store_id, 0, self.book_example)

        code = self.rs.request_search_content_in_store(content=key, store_id=self.store_id)
        assert code == 200

        code = self.rs.request_search_content_in_store(content=key + "x",
                                                       store_id=self.store_id)
        assert code == 501


