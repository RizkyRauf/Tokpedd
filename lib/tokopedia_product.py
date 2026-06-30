# STATUS: NOT IMPLEMENTED — endpoint requires authentication
# Modul ini tidak dipanggil dari main.py. Endpoint GraphQL PDPGetLayoutQuery
# membutuhkan autentikasi yang belum terimplementasi.

import requests
import os
import logging
import re
from urllib.parse import urlparse

class ProductItem:
    """
    Kelas ProductItem untuk mengambil data produk dari Tokopedia menggunakan GraphQL API.
    """

    def __init__(self):
        """
        Inisialisasi instance ProductItem dengan URL API GraphQL Tokopedia.
        """
        self.url = "https://gql.tokopedia.com/graphql/PDPGetLayoutQuery"

    def read_query(self):
        """
        Membaca dan mengembalikan query GraphQL dari file teks.
        
        Returns:
            str: String query GraphQL yang dibaca dari file.
        """
        file_path = os.path.join(os.path.dirname(__file__), "text_query/query_items.txt")
        with open(file_path, 'r') as file:
            query = file.read()
        return query

    def clean_text(self, text):
        """
        Membersihkan teks dari karakter yang tidak diinginkan.
        
        Args:
            text (str): Teks yang akan dibersihkan.
            
        Returns:
            str: Teks yang telah dibersihkan.
        """
        cleaned_text = re.sub(r'[\n\t]+', ' ', text)
        cleaned_text = re.sub(r'[\u2028\u2029]', '', cleaned_text)
        return cleaned_text
    
    def unpack_url(self, url):
        """
        Memisahkan URL untuk mendapatkan shop domain dan product key.
        
        Args:
            url (str): URL produk.
            
        Returns:
            tuple: Tuple yang berisi shop domain dan product key.
        """
        parts = urlparse(url)
        shop_domain = parts.path.split('/')[1]
        product_key = parts.path.split('/')[2]
        return shop_domain, product_key

    def request_product_page(self, url, api_version=1):
        """
        Mengirim permintaan ke halaman produk dan mengembalikan data produk.
        
        Args:
            url (str): URL produk.
            api_version (int): Versi API yang digunakan.
            
        Returns:
            tuple: Tuple yang berisi informasi produk seperti kategori, nama toko, jumlah terjual, rating, harga, nama produk, dan deskripsi.
            None: Jika terjadi kesalahan atau data tidak ditemukan.
        """
        try:
            shop_domain, product_key = self.unpack_url(url)
            query = self.read_query()

            variables = {
                "shopDomain": shop_domain,
                "productKey": product_key,
                "apiVersion": api_version
            }

            payload = {
                "operationName": "PDPGetLayoutQuery",
                "variables": variables,
                "query": query
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, seperti Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Referer": "https://www.tokopedia.com",
                "X-TKPD-AKAMAI": "pdpGetLayout",
                "Content-Type": "application/json"
            }

            response = requests.post(self.url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            if 'application/json' not in response.headers.get('Content-Type', ''):
                logging.error("Response content type is not JSON")
                return None

            data = response.json()

            if data is None:
                logging.error("Response data is None")
                return None

            if 'errors' in data:
                error_message = data['errors'][0]['message']
                if "[2001] product: not found" in error_message:
                    logging.error(f"Product not found: {error_message}")
                    return None

            if 'data' not in data or 'pdpGetLayout' not in data['data']:
                logging.error("Response data is missing 'data' or 'pdpGetLayout' key")
                return None

            basic_info = data['data']['pdpGetLayout']['basicInfo']
            category = basic_info['category'].get('name', 'Unknown')
            shop_name = basic_info.get('shopName', 'Unknown')
            count_sold = basic_info['txStats'].get('countSold', 'Unknown')
            rating = basic_info['stats'].get('rating', 'Unknown')

            price = 'Unknown'
            product_name = 'Unknown'
            description = 'Unknown'

            components = data['data']['pdpGetLayout']['components']

            for component in components:
                if component['type'] == 'product_content':
                    price_info = component['data'][0].get('price', {})
                    price = price_info.get('priceFmt', 'Unknown')
                    product_name_info = component['data'][0]
                    product_name = product_name_info.get('name', 'Unknown')
                elif component.get('name') == 'product_detail':
                    for content in component.get('data', []):
                        for detail in content.get('content', []):
                            if detail.get('title') == 'Deskripsi':
                                description = detail.get('subtitle', 'Unknown')
                                description = self.clean_text(description)[:200]
                                break
            
            return (category, shop_name, count_sold, rating, price, product_name, description)
    
        except requests.RequestException as e:
            logging.error(f"Request failed: {e}")
            return None
        except ValueError as e:
            logging.error(f"Value error: {e}")
            return None
        except IndexError as e:
            logging.error(f"Index error: {e}")
        except KeyError as e:
            logging.error(f"Key error: {e}")
            return None
