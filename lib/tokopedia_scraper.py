import asyncio
import aiohttp
import os
import re
from urllib.parse import urlparse, urlunparse
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

class TokopediaScraper:
    """
    Kelas TokopediaScraper untuk melakukan scraping data produk dari Tokopedia menggunakan 
    GraphQL API dan Playwright.
    """

    def __init__(self) -> None:
        """
        Inisialisasi instance TokopediaScraper dengan user agent, URL produk, dan XPath.
        """
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, seperti Gecko) Chrome/126.0.0.0 Safari/537.36"
        self.product_url = "https://gql.tokopedia.com/graphql/ShopProducts"
        self.xpath = {
            'ulasan': "//div[@class='css-a21zsk ']/div/p",
            '5': "//table[@class='css-8atqhb' or @title='jumlah rating']/tbody/tr[1][@class='css-1q2xtcf']/td[2]/p",
            '4': "//table[@class='css-8atqhb' or @title='jumlah rating']/tbody/tr[2][@class='css-1q2xtcf']/td[2]/p",
            '3': "//table[@class='css-8atqhb' or @title='jumlah rating']/tbody/tr[3][@class='css-1q2xtcf']/td[2]/p",
            '2': "//table[@class='css-8atqhb' or @title='jumlah rating']/tbody/tr[4][@class='css-1q2xtcf']/td[2]/p",
            '1': "//table[@class='css-8atqhb' or @title='jumlah rating']/tbody/tr[5][@class='css-1q2xtcf']/td[2]/p",
        }
        
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
        
    async def jumlah_data(self):
        """
        Menghitung jumlah halaman dan data yang akan di-scrape.

        Returns:
            tuple: Jumlah data dan jumlah halaman.
        """
        jumlah_page = 1
        jumlah_data = jumlah_page * 20
        return jumlah_data, jumlah_page
    
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

    async def scraper_tokped(self, keyword: str):
        print("Mulai scrape data ke tokopedia....")
        jml_data, jml_page = await self.jumlah_data()  
        products_data = []
        tasks = []
        async with aiohttp.ClientSession() as session:
            for page, data in zip(range(1, jml_page + 1), range(0, jml_data, 60)):
                payload = await self.load_json(page=page, keyword=keyword, data=data)
                task = asyncio.create_task(self.fetch_data(session, payload))
                tasks.append(task)
                
            results = await asyncio.gather(*tasks)
            
            for result in results:
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

        return products_data
    
    async def fetch_data(self, session, payload):
        async with session.post(self.product_url, headers=await self.headers(), json=payload, timeout=30) as response:
            return await response.json()
    
    async def extract_data_rating(self, page: Page):
        async def extract_data_ulasan(timeout=5000):
            try:
                locator = page.locator(self.xpath['ulasan'])
                await locator.wait_for(state="visible", timeout=timeout)
                ulasan_locator = await locator.inner_text()
                ulasan_data = re.search(r'(\d+) ulasan', ulasan_locator)
                return int(ulasan_data.group(1)) if ulasan_data else 0
            except (PlaywrightTimeoutError, PlaywrightError, Exception):
                return 0
            
        async def extract_data_rating(rating_key, timeout=5000):
            try:
                locator = page.locator(self.xpath[rating_key])
                await locator.wait_for(state="visible", timeout=timeout)
                rating_locator = await locator.inner_text()
                return int(rating_locator)
            except (PlaywrightTimeoutError, PlaywrightError, Exception):
                return 0

        ulasan_data = await extract_data_ulasan()
        rating_5 = await extract_data_rating('5')
        rating_4 = await extract_data_rating('4')
        rating_3 = await extract_data_rating('3')
        rating_2 = await extract_data_rating('2')
        rating_1 = await extract_data_rating('1')

        return ulasan_data, rating_5, rating_4, rating_3, rating_2, rating_1