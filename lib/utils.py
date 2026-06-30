import os
import json
import time
import asyncio
from functools import wraps

def save_to_json(data, filename, folder='output'):
    """
    Menyimpan data ke dalam berkas JSON di folder yang ditentukan.
    Mencegah duplikasi data saat menyimpan.

    Args:
        data (list): Data yang akan disimpan.
        filename (str): Nama berkas JSON.
        folder (str): Nama folder tempat berkas JSON akan disimpan. Default adalah 'output'.
    """
    # Membuat folder jika belum ada
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    file_path = os.path.join(folder, filename)
    
    # Muat data yang ada jika berkas sudah ada
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    # Gabungkan data baru dengan data yang ada dan hilangkan duplikasi
    combined_data = existing_data + data

    # Menggunakan set untuk menghilangkan duplikasi dengan cara mengubah dictionary menjadi string
    unique_data = list({json.dumps(d, sort_keys=True) for d in combined_data})
    unique_data = [json.loads(d) for d in unique_data]

    # Simpan data gabungan yang unik ke berkas JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)
    
    print(f"Data berhasil disimpan ke {file_path}")
    

def measure_time(method):
    """
    Dekorator untuk mengukur waktu eksekusi sebuah metode.

    Mengembalikan sebuah fungsi pembungkus yang mengukur waktu eksekusi metode yang didekorasi
    dan mencetaknya ke konsol.

    Args:
        method (function): Metode yang akan diukur waktunya.

    Returns:
        function: Fungsi pembungkus yang mengukur dan mencatat waktu eksekusi metode.
    """
    @wraps(method)
    async def async_wrapper(self, *args, **kwargs):
        start_time = time.time()
        result = await method(self, *args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Waktu yang diperlukan untuk {method.__name__}: {elapsed_time:.2f} detik")
        return result

    @wraps(method)
    def sync_wrapper(self, *args, **kwargs):
        start_time = time.time()
        result = method(self, *args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Waktu yang diperlukan untuk {method.__name__}: {elapsed_time:.2f} detik")
        return result

    if asyncio.iscoroutinefunction(method):
        return async_wrapper
    else:
        return sync_wrapper
    
def load_json(file_path):
    """
    Memuat data JSON dari sebuah berkas.

    Args:
        file_path (str): Path ke berkas JSON.

    Returns:
        dict: Data JSON yang dimuat sebagai dictionary Python, atau list kosong jika gagal.
    """
    if not os.path.exists(file_path):
        print(f"Berkas '{file_path}' tidak ditemukan.")
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        return json_data
    except Exception as e:
        print(f"Gagal memuat berkas JSON '{file_path}'. Error: {str(e)}")
        return []
    
def save_to_json_ulasan(data, file_name, output_dir='.'):
    """
    Menyimpan data sebagai JSON ke berkas yang ditentukan.

    Args:
        data (list or dict): Data yang akan disimpan sebagai JSON.
        file_name (str): Nama berkas JSON untuk disimpan.
        output_dir (str): Direktori output tempat berkas akan disimpan. Default adalah direktori saat ini.

    Returns:
        bool: True jika penyimpanan berhasil, False jika gagal.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        
        print(f"Data disimpan ke '{file_path}'.")
        return True
    except Exception as e:
        print(f"Gagal menyimpan data ke berkas JSON '{file_name}'. Error: {str(e)}")
        return False
