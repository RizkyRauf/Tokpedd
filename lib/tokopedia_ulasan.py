import math
import os
import requests
from datetime import datetime

class UlasanRequest():
    
    """
    Kelas untuk menangani permintaan ulasan produk dari Tokopedia menggunakan API GraphQL.

    Atribut:
    - url (str): URL endpoint GraphQL untuk daftar ulasan produk.
    """

    def __init__(self) -> None:
        """
        Menginisialisasi kelas UlasanRequest dengan URL endpoint GraphQL.
        """
        self.url = "https://gql.tokopedia.com/graphql/productReviewList"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
            "Content-Type": "application/json",
            "Origin": "https://www.tokopedia.com",
        }
        
    
    def calculate_total_pages(self, total_ulasan):
        """
        Menghitung jumlah total halaman berdasarkan jumlah ulasan.

        Args:
        - total_ulasan (int): Jumlah total ulasan.

        Returns:
        - int: Jumlah halaman yang diperlukan untuk mengambil semua ulasan, mempertimbangkan batasan 10 ulasan per halaman.
        """
        return math.ceil(total_ulasan / 10)
        
    def read_query(self):
        file_path = os.path.join(os.path.dirname(__file__), 'text_query/query_ulasan.txt')
        with open(file_path, 'r') as file:
            query_items = file.read()
        return query_items
    
    
    def request_ulasan(self, product_id, total_ulasan, limit=10):
        """
        Mengirim permintaan untuk mengambil ulasan produk dari Tokopedia menggunakan API GraphQL.

        Args:
        - product_id (str): ID produk untuk mengambil ulasan.
        - total_ulasan (int): Jumlah total ulasan untuk produk.
        - limit (int): Jumlah ulasan yang diambil per halaman. Default adalah 10.

        Returns:
        - list: Daftar dictionary yang berisi detail ulasan, diformat sebagai:
          [
              {
                  'E-Commerce': "Tokopedia",
                  'Id Produk': shop_info['shopID'],
                  'Nama Produk': shop_info['name'],
                  'Link Produk': shop_info['url'],
                  'Id Ulasan': review['id'],
                  'Message': review['message'],
                  'Rating': review['productRating'],
                  'User Name': review['user']['fullName'],
                  'User Link': review['user']['url'],
                  'Date': date
              },
              ...
          ]
        """
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
                response = requests.post(self.url, headers=self.headers, json=payload, timeout=30)
                response.raise_for_status()

                data = response.json().get('data', {}).get('productrevGetProductReviewList', {})

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
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")

        return all_ulasan