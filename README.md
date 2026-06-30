# Tokopedia Scraper

## Deskripsi

Scraping data produk dan ulasan dari Tokopedia menggunakan GraphQL API dan BeautifulSoup.

## Struktur Project

```
├── data_json/
│   ├── full_data_<keyword>.json
│   └── data_ulasan_<keyword>.json
├── lib/
│   └── text_query/
│   │   ├── query_items.txt
│   │   ├── query_scraper.txt
│   │   └── query_ulasan.txt
│   ├── tokopedia_scraper.py
│   ├── tokopedia_product.py
│   ├── tokopedia_ulasan.py
│   └── utils.py
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

## Modul

- `data_json/`: Hasil scraping dalam format JSON.
- `lib/tokopedia_scraper.py`: Mengumpulkan data produk dari Tokopedia via GraphQL search API. Mengembalikan id, nama, harga, rating, kategori, toko, dll.
- `lib/tokopedia_product.py`: (Opsional) Mengumpulkan detail produk via GraphQL PDP API — **saat ini endpoint membutuhkan autentikasi**.
- `lib/tokopedia_ulasan.py`: Mengumpulkan ulasan produk via GraphQL API.
- `lib/utils.py`: Fungsi bantuan (save/load JSON, pengukur waktu).
- `main.py`: Skrip utama yang mengkoordinasikan scraping dan penyimpanan data.

## Instalasi

1. Python 3.7+.
2. Install dependensi:
```bash
pip install -r requirements.txt
```

## Penggunaan

```bash
python main.py
```

Ubah keyword di `main.py` baris `keyword = "esp32"` sesuai kebutuhan.

## Performa

- Scraping 60 produk dari GraphQL search API: **~10 detik**
- Scraping ulasan: tergantung jumlah ulasan per produk
- Tidak menggunakan Playwright/browser — cepat dan ringan

## Catatan

- Star ratings per-bintang (rating_5..1) tidak tersedia di search API dan membutuhkan rendering JavaScript (Playwright) jika diperlukan.
- Endpoint PDP detail produk saat ini membutuhkan header autentikasi tertentu dan tidak dapat diakses via requests biasa.
