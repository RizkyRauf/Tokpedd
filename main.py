from typing import List, Dict
import asyncio
import re
import logging
import os
import random
import argparse
import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from lib.tokopedia_scraper import TokopediaScraper
from lib.tokopedia_ulasan import UlasanRequest
from lib.utils import save_to_json, save_to_csv, save_to_excel, measure_time, load_json, save_to_json_ulasan
from bs4 import BeautifulSoup

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/tokpedd.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"


def _create_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


_sync_session = _create_session()


def scrape_star_ratings(item: dict) -> dict:
    import time as _time
    _time.sleep(random.uniform(0.3, 0.8))
    try:
        resp = _sync_session.get(item['link'], timeout=30, headers={"User-Agent": UA})
        if resp.status_code != 200:
            return item
        soup = BeautifulSoup(resp.text, 'lxml')

        count_ulasan = item.get('count_review', 0) or 0
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
    except Exception as e:
        logger.warning("Gagal scrape rating untuk %s: %s", item.get('link', ''), e)
    return item


@measure_time
async def proses_get_url(keyword: str, max_pages: int = 5) -> List[Dict]:
    from concurrent.futures import ThreadPoolExecutor

    print("Mulai scrape data ke tokopedia....")
    tokopedia = TokopediaScraper()
    products_data = await tokopedia.scraper_tokped(keyword, max_pages=max_pages)

    with ThreadPoolExecutor(max_workers=8) as ex:
        products_data = list(ex.map(scrape_star_ratings, products_data))

    print("Selesai scrape data ke tokopedia.... dan mengambil data sebanyak", len(products_data))
    return products_data


@measure_time
async def proses_ulasan_request(folder_path, nama_data_json):
    file_path = f"{folder_path}/{nama_data_json}"
    load_json_data = load_json(file_path)
    ulasan_request = UlasanRequest()

    if not load_json_data:
        return [], []

    semaphore = asyncio.Semaphore(5)

    async def process_item(session, item):
        async with semaphore:
            id_for_ulasan = item.get('id')
            if not id_for_ulasan:
                return None, item

            count_ulasan = item.get('count_ulasan_item', 0) or item.get('count_review', 0) or 10
            ulasan_data = await ulasan_request.request_ulasan(session, id_for_ulasan, count_ulasan)
            if ulasan_data:
                ratings = [r.get('Rating', 0) for r in ulasan_data if r.get('Rating')]
                if ratings:
                    item['count_ulasan_item'] = len(ratings)
                    item['rating_5_item'] = str(sum(1 for r in ratings if r == 5))
                    item['rating_4_item'] = str(sum(1 for r in ratings if r == 4))
                    item['rating_3_item'] = str(sum(1 for r in ratings if r == 3))
                    item['rating_2_item'] = str(sum(1 for r in ratings if r == 2))
                    item['rating_1_item'] = str(sum(1 for r in ratings if r == 1))

                return {
                    'ID Product': id_for_ulasan,
                    'Name Product': item.get('product_name'),
                    'Link Product': item.get('link'),
                    'ulasan': ulasan_data,
                }, item
            return None, item

    async with aiohttp.ClientSession() as session:
        tasks = [process_item(session, item) for item in load_json_data]
        results = await asyncio.gather(*tasks)

    detailed_data_ulasan = [r[0] for r in results if r[0] is not None]
    updated_items = [r[1] for r in results]

    return detailed_data_ulasan, updated_items


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tokpedd — Tokopedia product scraper")
    parser.add_argument("-k", "--keyword", default="esp32", help="Keyword pencarian (default: esp32)")
    parser.add_argument("--max-pages", type=int, default=5, help="Jumlah halaman maksimal (default: 5)")
    parser.add_argument("--output-dir", default="./data_json", help="Folder output (default: ./data_json)")
    parser.add_argument("--format", choices=["json", "csv", "xlsx"], default="json", help="Format output (default: json)")
    args = parser.parse_args()

    keyword = args.keyword
    max_pages = args.max_pages
    output_dir = args.output_dir

    scraped_data = asyncio.run(proses_get_url(keyword, max_pages=max_pages))
    ext = {"json": ".json", "csv": ".csv", "xlsx": ".xlsx"}[args.format]
    nama_data_json = f"full_data_{keyword.replace(' ', '_')}{ext}"

    if args.format == "json":
        save_to_json(scraped_data, nama_data_json, output_dir)
    elif args.format == "csv":
        save_to_csv(scraped_data, nama_data_json, output_dir)
    elif args.format == "xlsx":
        save_to_excel(scraped_data, nama_data_json, output_dir)

    data_ulasan, updated_items = asyncio.run(proses_ulasan_request(output_dir, f"full_data_{keyword.replace(' ', '_')}.json"))
    save_to_json_ulasan(data_ulasan, f'data_ulasan_{keyword.replace(" ", "_")}.json', output_dir)

    if args.format == "json":
        import json
        full_path = os.path.join(output_dir, nama_data_json)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(updated_items, f, ensure_ascii=False, indent=4)
        print(f"Data updated dengan rating dari ulasan di {full_path}")
