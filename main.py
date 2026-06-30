from typing import List, Dict
import asyncio
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from lib.tokopedia_scraper import TokopediaScraper
from lib.tokopedia_product import ProductItem
from lib.tokopedia_ulasan import UlasanRequest
from lib.utils import save_to_json, measure_time, load_json, save_to_json_ulasan
import requests
from bs4 import BeautifulSoup


def scrape_star_ratings(item: dict) -> dict:
    try:
        resp = requests.get(item['link'], timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        })
        if resp.status_code != 200:
            return item
        soup = BeautifulSoup(resp.text, 'lxml')

        count_ulasan = item.get('count_review', 0)
        rating_5 = rating_4 = rating_3 = rating_2 = rating_1 = 0

        ulasan_el = soup.select_one('div.css-a21zsk div p')
        if ulasan_el:
            match = re.search(r'(\d[\d.]*)', ulasan_el.get_text(strip=True))
            if match:
                count_ulasan = int(match.group(1).replace('.', ''))

        rows = soup.select('table.css-8atqhb tbody tr, table[title="jumlah rating"] tbody tr, tr.css-1q2xtcf')
        for i, row in enumerate(rows[:5]):
            tds = row.find_all('td')
            if len(tds) >= 2:
                p = tds[1].find('p')
                if p and p.get_text(strip=True).isdigit():
                    val = int(p.get_text(strip=True))
                    if i == 0: rating_5 = val
                    elif i == 1: rating_4 = val
                    elif i == 2: rating_3 = val
                    elif i == 3: rating_2 = val
                    elif i == 4: rating_1 = val

        item.update({
            'count_ulasan_item': count_ulasan,
            'rating_5_item': str(rating_5), 'rating_4_item': str(rating_4),
            'rating_3_item': str(rating_3), 'rating_2_item': str(rating_2),
            'rating_1_item': str(rating_1),
        })
    except Exception:
        item.setdefault('count_ulasan_item', item.get('count_review', 0))
        item.setdefault('rating_5_item', '0')
        item.setdefault('rating_4_item', '0')
        item.setdefault('rating_3_item', '0')
        item.setdefault('rating_2_item', '0')
        item.setdefault('rating_1_item', '0')
    return item


@measure_time
async def proses_get_url(keyword: str) -> List[Dict]:
    print("Mulai scrape data ke tokopedia....")
    tokopedia = TokopediaScraper()
    products_data = await tokopedia.scraper_tokped(keyword)

    with ThreadPoolExecutor(max_workers=15) as ex:
        products_data = list(ex.map(scrape_star_ratings, products_data))

    print("Selesai scrape data ke tokopedia.... dan mengambil data sebanyak", len(products_data))
    return products_data


@measure_time
def proses_ulasan_request(folder_path, nama_data_json):
    file_path = f"{folder_path}/{nama_data_json}"
    load_json_data = load_json(file_path)
    ulasan_request = UlasanRequest()

    if not load_json_data:
        return []

    detailed_data_ulasan = []

    def process_item(item):
        id_for_ulasan = item.get('id')
        count_ulasan = item.get('count_ulasan_item', 0) or item.get('count_review', 0)
        if not id_for_ulasan or not count_ulasan:
            return None
        ulasan_data = ulasan_request.request_ulasan(id_for_ulasan, count_ulasan)
        if ulasan_data:
            return {
                'ID Product': id_for_ulasan,
                'Name Product': item.get('product_name'),
                'Link Product': item.get('link'),
                'ulasan': ulasan_data,
            }
        return None

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_item, item) for item in load_json_data]
        for future in as_completed(futures):
            result = future.result()
            if result:
                detailed_data_ulasan.append(result)

    return detailed_data_ulasan


if __name__ == "__main__":
    keyword = "esp32"

    scraped_data = asyncio.run(proses_get_url(keyword))
    nama_data_json = f"full_data_{keyword.replace(' ', '_')}.json"
    folder_path = "./data_json"
    save_to_json(scraped_data, nama_data_json, folder_path)

    data_ulasan = proses_ulasan_request(folder_path, nama_data_json)
    save_to_json_ulasan(data_ulasan, f'data_ulasan_{keyword.replace(" ", "_")}.json', folder_path)
