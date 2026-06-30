import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.tokopedia_ulasan import UlasanRequest
from lib.tokopedia_product import ProductItem
from lib.utils import save_to_json
from lib.tokopedia_scraper import TokopediaScraper
import json
import tempfile


class TestCalculateTotalPages:
    def setup_method(self):
        self.ulasan = UlasanRequest()

    def test_ten_reviews(self):
        assert self.ulasan.calculate_total_pages(10) == 1

    def test_eleven_reviews(self):
        assert self.ulasan.calculate_total_pages(11) == 2

    def test_zero_reviews(self):
        assert self.ulasan.calculate_total_pages(0) == 0

    def test_one_review(self):
        assert self.ulasan.calculate_total_pages(1) == 1

    def test_hundred_reviews(self):
        assert self.ulasan.calculate_total_pages(100) == 10

    def test_hundred_one_reviews(self):
        assert self.ulasan.calculate_total_pages(101) == 11


class TestCleanText:
    def setup_method(self):
        self.product = ProductItem()

    def test_newline_replaced(self):
        assert self.product.clean_text("hello\nworld") == "hello world"

    def test_tab_replaced(self):
        assert self.product.clean_text("hello\tworld") == "hello world"

    def test_line_separator_removed(self):
        assert self.product.clean_text("hello\u2028world") == "helloworld"

    def test_paragraph_separator_removed(self):
        assert self.product.clean_text("hello\u2029world") == "helloworld"

    def test_empty_string(self):
        assert self.product.clean_text("") == ""

    def test_no_special_chars(self):
        assert self.product.clean_text("hello world") == "hello world"

    def test_multiple_newlines(self):
        assert self.product.clean_text("a\n\n\nb") == "a b"


class TestUnpackUrl:
    def setup_method(self):
        self.product = ProductItem()

    def test_normal_url(self):
        shop, key = self.product.unpack_url("https://www.tokopedia.com/toko/produk-name")
        assert shop == "toko"
        assert key == "produk-name"

    def test_url_with_extra_path(self):
        shop, key = self.product.unpack_url("https://www.tokopedia.com/shop/product-123")
        assert shop == "shop"
        assert key == "product-123"


class TestSaveToJsonDedup:
    def test_dedup_preserves_order(self):
        data = [
            {"id": "1", "name": "a"},
            {"id": "2", "name": "b"},
            {"id": "1", "name": "a"},
            {"id": "3", "name": "c"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            save_to_json(data, "test.json", tmpdir)
            with open(os.path.join(tmpdir, "test.json")) as f:
                result = json.load(f)
            assert len(result) == 3
            assert result[0]["id"] == "1"
            assert result[1]["id"] == "2"
            assert result[2]["id"] == "3"

    def test_empty_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_to_json([], "test.json", tmpdir)
            with open(os.path.join(tmpdir, "test.json")) as f:
                result = json.load(f)
            assert result == []

    def test_merge_with_existing(self):
        existing = [{"id": "1", "name": "a"}]
        new = [{"id": "2", "name": "b"}]
        with tempfile.TemporaryDirectory() as tmpdir:
            save_to_json(existing, "test.json", tmpdir)
            save_to_json(new, "test.json", tmpdir)
            with open(os.path.join(tmpdir, "test.json")) as f:
                result = json.load(f)
            assert len(result) == 2


class TestParseProducts:
    def setup_method(self):
        self.scraper = TokopediaScraper()

    def test_parse_products_basic(self):
        result = {
            "data": {
                "ace_search_product_v4": {
                    "data": {
                        "products": [
                            {
                                "id": 123,
                                "url": "https://www.tokopedia.com/toko/product?query=1",
                                "name": "ESP32 Module",
                                "priceStr": "Rp50.000",
                                "rating": 4.5,
                                "countReview": 100,
                                "categoryBreadcrumb": "Electronics > Microcontroller",
                                "shop": {"city": "Jakarta", "name": "Toko electronics"},
                            }
                        ]
                    }
                }
            }
        }
        products_data = []
        self.scraper._parse_products(result, products_data)
        assert len(products_data) == 1
        p = products_data[0]
        assert p["id"] == "123"
        assert p["product_name"] == "ESP32 Module"
        assert p["price"] == "Rp50.000"
        assert p["rating"] == "4.5"
        assert p["count_review"] == 100
        assert p["link"] == "https://www.tokopedia.com/toko/product"

    def test_parse_products_empty(self):
        result = {
            "data": {
                "ace_search_product_v4": {
                    "data": {
                        "products": []
                    }
                }
            }
        }
        products_data = []
        self.scraper._parse_products(result, products_data)
        assert len(products_data) == 0

    def test_parse_products_missing_fields(self):
        result = {
            "data": {
                "ace_search_product_v4": {
                    "data": {
                        "products": [
                            {
                                "id": 456,
                                "url": "",
                                "name": "Minimal Product",
                            }
                        ]
                    }
                }
            }
        }
        products_data = []
        self.scraper._parse_products(result, products_data)
        assert len(products_data) == 1
        assert products_data[0]["link"] == ""
        assert products_data[0]["price"] == ""
