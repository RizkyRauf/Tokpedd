"""
Script sederhana untuk inspeksi raw data dari TokopediaScraper.

Tujuan:
1. Lihat struktur data mentah yang dikembalikan scraper (1 produk contoh + summary).
2. Cek apakah pagination (halaman ke-2, ke-3, dst) benar-benar berfungsi dan
   mengembalikan produk yang berbeda dari halaman pertama.

Cara pakai:
    python inspect_raw_data.py
    python inspect_raw_data.py --keyword "laptop gaming" --max-pages 3
"""
import argparse
import asyncio
import json
import sys
import os

# Supaya bisa import lib/ walau script ini diletakkan di root project
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.tokopedia_scraper import TokopediaScraper


async def main(keyword: str, max_pages: int):
    scraper = TokopediaScraper()

    print(f"Mengambil data untuk keyword: '{keyword}', max_pages: {max_pages}")
    print("-" * 60)

    products = await scraper.scraper_tokped(keyword, max_pages=max_pages)

    print("-" * 60)
    print(f"Total produk terkumpul: {len(products)}")

    if not products:
        print("Tidak ada data yang didapat. Cek koneksi atau struktur response API.")
        return

    # Tampilkan 1 contoh data mentah per produk (struktur lengkap)
    print("\n=== Contoh 1 item data mentah ===")
    print(json.dumps(products[0], indent=2, ensure_ascii=False))

    # Cek apakah ada ID produk yang duplikat antar "halaman"
    # (indikasi pagination berhasil mengambil produk berbeda, bukan ulang dari halaman 1)
    ids = [p.get('id') for p in products]
    unique_ids = set(ids)
    print(f"\n=== Cek duplikasi ID produk ===")
    print(f"Jumlah produk: {len(ids)}")
    print(f"Jumlah ID unik: {len(unique_ids)}")
    if len(ids) == len(unique_ids):
        print("✅ Tidak ada duplikat — pagination mengambil produk yang berbeda tiap halaman.")
    else:
        duplicate_count = len(ids) - len(unique_ids)
        print(f"⚠️  Ada {duplicate_count} ID duplikat — kemungkinan halaman selanjutnya mengulang data.")

    # Simpan semua raw data ke file supaya bisa dibuka manual
    output_file = "raw_data_inspect.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    print(f"\nSeluruh raw data disimpan ke: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspeksi raw data dari TokopediaScraper")
    parser.add_argument("--keyword", "-k", default="esp32", help="Keyword pencarian")
    parser.add_argument("--max-pages", type=int, default=2, help="Jumlah halaman yang diambil (untuk cek pagination, pakai >=2)")
    args = parser.parse_args()

    asyncio.run(main(args.keyword, args.max_pages))