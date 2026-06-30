import asyncio
import aiohttp
import math
import os
from urllib.parse import urlparse, urlunparse


class TokopediaScraper:
    """
    Kelas TokopediaScraper untuk melakukan scraping data produk dari Tokopedia menggunakan 
    GraphQL API.
    """

    def __init__(self) -> None:
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        self.product_url = "https://gql.tokopedia.com/graphql/ShopProducts"
        
    async def read_query_items(self):
        """
        Membaca dan mengembalikan query GraphQL dari file teks.

        Returns:
            str: String query GraphQL yang dibaca dari file.
        """
        file_path = os.path.join(os.path.dirname(__file__), 'text_query/query_scraper.txt')
        with open(file_path, 'r') as file:
            query_items = file.read()
        return query_items
        
    async def headers(self):
        """
        Mengembalikan headers untuk permintaan HTTP.

        Returns:
            dict: Headers HTTP.
        """
        return {
            'authority': 'gql.tokopedia.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://www.tokopedia.com',
            'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': self.user_agent,
            'x-device': 'default_v3',
            'x-source': 'tokopedia-lite',
            'x-tkpd-lite-service': 'zeus',
        }
    
    async def load_json(self, page: int, keyword: str, data: int):
        """
        Membuat payload JSON untuk permintaan GraphQL berdasarkan halaman, kata kunci, dan data.

        Args:
            page (int): Nomor halaman.
            keyword (str): Kata kunci pencarian.
            data (int): Indeks data awal.

        Returns:
            dict: Payload JSON untuk permintaan GraphQL.
        """
        payload = {
            "operationName": "SearchProductQueryV4",
            "variables": {
                "params": (
                    f"device=desktop&navsource=&ob=23&page={page}&q={keyword}&related=true&rows=60&safe_search=false&scheme=https&"
                    f"shipping=&source=search&srp_component_id=01.07.00.00&srp_page_id=&srp_page_title=&st=product&start={data}"
                )
            },
            "query": await self.read_query_items()
        }   
        return payload

    def _parse_products(self, result, products_data):
        products = result['data']['ace_search_product_v4']['data']['products']
        for product in products:
            links_url = product.get('url', '')
            clean_url = ''
            if links_url:
                parsed_url = urlparse(links_url)
                clean_url = urlunparse(parsed_url._replace(query=""))

            products_data.append({
                'id': str(product.get('id', '')),
                'city': product.get('shop', {}).get('city', ''),
                'link': clean_url,
                'product_name': product.get('name', ''),
                'price': product.get('priceStr', '') or str(product.get('price', '')),
                'rating': str(product.get('rating', '') or product.get('ratingAverage', '') or ''),
                'count_review': product.get('countReview', 0),
                'category': product.get('categoryBreadcrumb', '') or product.get('categoryName', ''),
                'shop_name': product.get('shop', {}).get('name', ''),
            })

    async def scraper_tokped(self, keyword: str, max_pages: int = 5):
        """
        Scrape produk dari Tokopedia untuk sebuah keyword.

        Jumlah halaman dihitung secara dinamis berdasarkan field `totalData`
        yang dikembalikan API pada permintaan halaman pertama, dibatasi oleh
        `max_pages` agar tidak membebani server untuk keyword dengan hasil
        sangat banyak.

        Args:
            keyword (str): Kata kunci pencarian.
            max_pages (int): Batas maksimum halaman yang akan diambil (60 produk/halaman).

        Returns:
            list: Daftar produk hasil scraping.
        """
        print("Mulai scrape data ke tokopedia....")
        products_data = []

        async with aiohttp.ClientSession() as session:
            first_payload = await self.load_json(page=1, keyword=keyword, data=0)
            first_result = await self.fetch_data(session, first_payload)

            header = first_result.get('data', {}).get('ace_search_product_v4', {}).get('header', {})
            total_data = header.get('totalData', 0) or 0
            total_pages = max(1, min(math.ceil(total_data / 60), max_pages)) if total_data else 1
            print(f"Total hasil ditemukan: {total_data}, mengambil {total_pages} halaman")

            self._parse_products(first_result, products_data)

            if total_pages > 1:
                tasks = []
                for page in range(2, total_pages + 1):
                    data_start = (page - 1) * 60
                    payload = await self.load_json(page=page, keyword=keyword, data=data_start)
                    tasks.append(asyncio.create_task(self.fetch_data(session, payload)))

                results = await asyncio.gather(*tasks)
                for result in results:
                    self._parse_products(result, products_data)

        return products_data
    
    async def fetch_data(self, session, payload):
        async with session.post(self.product_url, headers=await self.headers(), json=payload, timeout=30) as response:
            return await response.json()