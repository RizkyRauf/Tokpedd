import math
import os
import aiohttp


class UlasanRequest():
    
    """
    Kelas untuk menangani permintaan ulasan produk dari Tokopedia menggunakan API GraphQL.
    """

    def __init__(self) -> None:
        self.url = "https://gql.tokopedia.com/graphql/productReviewList"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
            "Content-Type": "application/json",
            "Origin": "https://www.tokopedia.com",
        }
    
    def calculate_total_pages(self, total_ulasan):
        return math.ceil(total_ulasan / 10)
        
    def read_query(self):
        file_path = os.path.join(os.path.dirname(__file__), 'text_query/query_ulasan.txt')
        with open(file_path, 'r') as file:
            query_items = file.read()
        return query_items
    
    async def request_ulasan(self, session, product_id, total_ulasan, limit=10):
        all_ulasan = []

        total_pages = self.calculate_total_pages(total_ulasan)
        if total_pages == 0:
            print(f"Tidak ada ulasan untuk ID Produck: {product_id}")
            return None
        max_page = min(total_pages, 50)

        query = self.read_query()

        for page in range(1, max_page + 1):
            variables = {
                "productID": product_id,
                "page": page,
                "limit": limit,
                "sortBy": "create_time desc",
                "filterBy": ""
            }
            payload = {
                "operationName": "productReviewList",
                "variables": variables,
                "query": query
            }

            try:
                async with session.post(self.url, headers=self.headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        continue
                    data = await response.json()
                    data = data.get('data', {}).get('productrevGetProductReviewList', {})

                    review_list = data.get('list', [])

                    for review in review_list:
                        ulasan = {
                            'Id Ulasan': review.get('id', ''),
                            'Message': review.get('message', ''),
                            'Rating': review.get('productRating', ''),
                            'User Name': review['user'].get('fullName', ''),
                            'User Link': review['user'].get('url', ''),
                        }
                        all_ulasan.append(ulasan)
            except Exception as e:
                print(f"Error: {e}")

        return all_ulasan
