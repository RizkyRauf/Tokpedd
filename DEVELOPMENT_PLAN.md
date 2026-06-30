# Development Plan — Project Tokpedd

Status saat ini: **semua bug dari code review awal sudah selesai diperbaiki** Dokumen ini berisi rencana pengembangan lanjutan, diurutkan berdasarkan prioritas dan dampak.

## Ringkasan Prioritas

| # | Fitur | Prioritas | Effort | Dampak |
|---|---|---|---|---|
| 1 | CLI argument (keyword, max_pages) | Tinggi | Kecil | Tinggi |
| 2 | Migrasi `requests` → `aiohttp` | Sedang | Sedang | Sedang |
| 3 | Export ke CSV/Excel | Sedang | Kecil | Sedang |
| 4 | Unit test | Sedang | Sedang | Tinggi (jangka panjang) |
| 5 | Dockerfile | Rendah | Kecil | Sedang |

---

## 1. CLI Argument untuk Keyword & Max Pages

**Tujuan:** Hilangkan kebutuhan edit source code setiap kali ganti keyword pencarian atau jumlah halaman.

**File yang diubah:** `main.py`

**Rencana implementasi:**
- Tambahkan `argparse` di blok `if __name__ == "__main__":`.
- Argumen yang didukung:
  - `--keyword` / `-k` (required atau default `"esp32"`)
  - `--max-pages` (default `5`)
  - `--output-dir` (default `./data_json`)
- Validasi input dasar (keyword tidak boleh kosong, max-pages harus > 0).

**Contoh penggunaan setelah selesai:**
```bash
python main.py --keyword "laptop gaming" --max-pages 3
python main.py -k "esp32" --max-pages 10 --output-dir ./hasil
```

**Definition of Done:**
- [ ] `main.py` bisa dijalankan tanpa argumen (pakai default) dan tetap berjalan seperti sekarang
- [ ] `main.py` bisa dijalankan dengan argumen custom dan menghasilkan output sesuai parameter
- [ ] `python main.py --help` menampilkan deskripsi argumen yang jelas

---

## 2. Migrasi `requests` → `aiohttp`

**Tujuan:** Konsistensi arsitektur — `tokopedia_scraper.py` sudah full async, tapi `scrape_star_ratings` (main.py) dan `request_ulasan` (tokopedia_ulasan.py) masih sync request dijalankan lewat `ThreadPoolExecutor`. Migrasi ke `aiohttp` akan menyederhanakan kode dan meningkatkan efisiensi I/O.

**File yang diubah:** `main.py`, `lib/tokopedia_ulasan.py`

**Rencana implementasi:**
- Ubah `scrape_star_ratings(item)` jadi `async def`, ganti `requests.Session().get()` dengan `aiohttp.ClientSession().get()`.
- Ganti `ThreadPoolExecutor(max_workers=8)` dengan `asyncio.gather()` + `asyncio.Semaphore` (untuk membatasi concurrency, menggantikan peran `max_workers`).
- Lakukan hal yang sama untuk `UlasanRequest.request_ulasan()` di `tokopedia_ulasan.py`.
- Retry logic (`urllib3.util.retry.Retry`) yang sudah ada di `_create_session()` perlu direplikasi manual untuk `aiohttp` (atau pakai library seperti `aiohttp-retry`).
- Pastikan rate limiting (jeda acak dari fix 1.5) tetap dipertahankan, dipindah ke `await asyncio.sleep(random.uniform(0.2, 0.6))`.

**Risiko:** Perubahan ini cukup invasif — sebaiknya dikerjakan di branch terpisah dan dites menyeluruh sebelum merge, karena menyentuh alur data utama.

**Definition of Done:**
- [ ] Semua HTTP request di project menggunakan `aiohttp`, tidak ada lagi `requests` atau `ThreadPoolExecutor` untuk I/O network
- [ ] Hasil scraping (jumlah data, struktur JSON) tetap sama dengan versi sebelumnya untuk keyword yang sama
- [ ] Retry dan rate limiting tetap berfungsi

---

## 3. Export ke CSV/Excel

**Tujuan:** Mempermudah analisis data tanpa perlu convert manual dari JSON.

**File yang diubah:** `lib/utils.py` (tambah fungsi baru), `main.py`

**Rencana implementasi:**
- Tambah fungsi `save_to_csv(data, filename, folder)` dan/atau `save_to_excel(data, filename, folder)` di `utils.py` menggunakan `pandas`.
- Tambahkan dependency `pandas` (dan `openpyxl` untuk Excel) ke `requirements.txt`.
- Tambah argumen CLI `--format` (`json` / `csv` / `xlsx`, default `json`) di `main.py` agar user bisa pilih format output — ini bergantung pada item #1 (CLI argument) sudah selesai.

**Definition of Done:**
- [ ] Bisa generate output CSV dan Excel dari data yang sama dengan output JSON
- [ ] Kolom di CSV/Excel rapi dan readable (header sesuai nama field, bukan key mentah)

---

## 4. Unit Test

**Tujuan:** Mencegah regresi di fungsi-fungsi murni yang sering jadi sumber bug diam-diam (lihat temuan 1.4, 1.6 di code review sebelumnya).

**File baru:** `tests/test_utils.py`, `tests/test_tokopedia_ulasan.py`, `tests/test_tokopedia_scraper.py`

**Rencana implementasi:**
- Setup `pytest` sebagai test runner, tambahkan ke `requirements.txt` (atau buat `requirements-dev.txt` terpisah).
- Prioritas fungsi yang ditest lebih dulu (tidak butuh network, murni logic):
  - `calculate_total_pages()` di `tokopedia_ulasan.py`
  - `clean_text()` dan `unpack_url()` di `tokopedia_product.py`
  - Dedup logic di `save_to_json()` (`utils.py`)
  - `_parse_products()` di `tokopedia_scraper.py` (pakai sample response JSON sebagai fixture)
- Tambahkan GitHub Actions workflow sederhana (`.github/workflows/test.yml`) untuk run test otomatis setiap push/PR.

**Definition of Done:**
- [ ] Minimal 4 fungsi murni di atas punya test case (happy path + edge case seperti input kosong/invalid)
- [ ] `pytest` bisa dijalankan dengan satu command dan semua test pass
- [ ] (Opsional) CI pipeline aktif di GitHub Actions

---

## 5. Dockerfile

**Tujuan:** Mempermudah deployment/run di environment lain atau penjadwalan otomatis (cron job, scheduler).

**File baru:** `Dockerfile`, `.dockerignore`

**Rencana implementasi:**
- Base image `python:3.11-slim` atau `python:3.12-slim`.
- Copy `requirements.txt`, install dependency, copy source code.
- Set `ENTRYPOINT` ke `python main.py` dengan default args, atau biarkan args di-override saat `docker run`.
- `.dockerignore` exclude `data_json/`, `logs/`, `__pycache__/`, `.git/`.

**Contoh penggunaan setelah selesai:**
```bash
docker build -t tokpedd .
docker run --rm -v $(pwd)/data_json:/app/data_json tokpedd --keyword "esp32" --max-pages 5
```

**Definition of Done:**
- [ ] Image bisa di-build tanpa error
- [ ] Container bisa dijalankan dan menghasilkan output JSON yang ter-mount ke host
- [ ] README diupdate dengan instruksi run via Docker

---

## Urutan Eksekusi yang Disarankan

1. **Item #1 (CLI argument)** — paling cepat, langsung kerasa manfaatnya, dan jadi prasyarat untuk item #3.
2. **Item #3 (Export CSV/Excel)** — quick win lain, tidak terlalu invasif.
3. **Item #4 (Unit test)** — mulai dibangun bertahap, idealnya jalan paralel sambil mengerjakan fitur lain (test ditulis untuk kode yang sudah stabil).
4. **Item #2 (Migrasi aiohttp)** — paling invasif, kerjakan di branch terpisah setelah fitur-fitur lain stabil, supaya kalau ada regresi gampang diisolasi.
5. **Item #5 (Dockerfile)** — bisa dikerjakan kapan saja, tidak bergantung pada item lain, cocok jadi pengisi waktu luang di antara fitur besar.

## Catatan

- Setiap item sebaiknya dikerjakan di branch terpisah (`feat/cli-args`, `feat/export-csv`, dst.) dan di-PR satu-satu, mengikuti kebiasaan commit granular yang sudah diterapkan sebelumnya.
- Setelah item #1 dan #2 selesai, update `README.md` agar instruksi penggunaan tetap akurat.