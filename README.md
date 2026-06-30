# Tokpedd

Scraping data produk dan ulasan dari Tokopedia menggunakan GraphQL API, aiohttp, dan BeautifulSoup.

## Struktur Project

```
├── data_json/                  # Hasil scraping
├── logs/                       # Log file
├── lib/
│   ├── text_query/
│   │   ├── query_scraper.txt
│   │   ├── query_ulasan.txt
│   │   └── query_items.txt
│   ├── tokopedia_scraper.py    # GraphQL search API (aiohttp)
│   ├── tokopedia_ulasan.py     # GraphQL review API (aiohttp)
│   ├── tokopedia_product.py    # GraphQL PDP API (belum aktif)
│   └── utils.py                # Fungsi bantuan
├── tests/                      # Unit test
├── Dockerfile
├── .dockerignore
├── main.py
├── requirements.txt
└── README.md
```

## Instalasi

```bash
pip install -r requirements.txt
```

## Penggunaan

```bash
# Default (keyword: esp32, 5 halaman)
python main.py

# Custom keyword & halaman
python main.py -k "laptop gaming" --max-pages 3

# Export ke CSV
python main.py -k "esp32" --max-pages 5 --format csv

# Export ke Excel
python main.py -k "esp32" --format xlsx

# Custom output directory
python main.py -k "esp32" --output-dir ./hasil
```

### Argumen CLI

| Argumen | Short | Default | Deskripsi |
|---------|-------|---------|-----------|
| `--keyword` | `-k` | `esp32` | Keyword pencarian |
| `--max-pages` | | `5` | Jumlah halaman maksimal (60 produk/halaman) |
| `--output-dir` | | `./data_json` | Folder output |
| `--format` | | `json` | Format output: `json`, `csv`, `xlsx` |

## Docker

```bash
docker build -t tokpedd .

docker run --rm -v $(pwd)/data_json:/app/data_json tokpedd

docker run --rm -v $(pwd)/data_json:/app/data_json tokpedd -k "laptop gaming" --max-pages 3 --format csv
```

## Testing

```bash
python -m pytest tests/ -v
```

## Modul

- **`lib/tokopedia_scraper.py`** — Scraping data produk via GraphQL search API (aiohttp async). Pagination otomatis berdasarkan `totalData`.
- **`lib/tokopedia_ulasan.py`** — Scraping ulasan produk via GraphQL review API (aiohttp async).
- **`lib/tokopedia_product.py`** — Detail produk via GraphQL PDP API (belum aktif, endpoint butuh autentikasi).
- **`lib/utils.py`** — Fungsi bantuan: save/load JSON, export CSV/Excel, pengukur waktu.
- **`main.py`** — Skrip utama yang mengkoordinasikan scraping, rating, ulasan, dan penyimpanan data.

## Catatan

- Product page scraping (rating per-bintang) masih pakai `requests` karena Tokopedia memblokir aiohttp di endpoint HTML.
- GraphQL API (search + ulasan) sudah menggunakan `aiohttp` async.
- Star ratings per-bintang diambil dari HTML product page dengan BeautifulSoup, bukan dari GraphQL search API.
