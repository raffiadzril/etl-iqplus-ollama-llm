# ETL IQPlus Financial News DAG
# - Extract: Scrape berita dari IQPlus khusus kemarin
# - Transform: Analisis LLM via Ollama
# - Load: Simpan ke MongoDB host.docker.internal
# - Alur: extract banyak berita → transform → store ke MongoDB

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pytz
import requests
import json
import time
import re
import logging
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from pymongo import MongoClient
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIG ---
MONGO_URI = 'mongodb://host.docker.internal:27017/'
MONGO_DB = 'iqplus_db-scraping'
MONGO_COLLECTION = 'stock_news'
OLLAMA_API = 'http://ollama:11434/api/chat'  # Gunakan nama service Docker
OLLAMA_FALLBACK_API = 'http://ollama:11434/api/chat'  # Tidak perlu fallback ke host
JAKARTA_TZ = pytz.timezone('Asia/Jakarta')
MAX_PAGES = 3  # Batas maksimal halaman yang akan dibuka
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- HELPER FUNCTION ---
def inisialisasi_webdriver():
    """Inisialisasi WebDriver headless baru"""
    logger.info("🚀 Memulai inisialisasi WebDriver...")
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless=new')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Remote(
        command_executor='http://chrome:4444/wd/hub',
        options=options
    )
    logger.info("✅ WebDriver berhasil diinisialisasi")
    return driver

def retry_get(driver, url, retries=3, delay=2):
    """Fungsi untuk mencoba membuka URL dengan retry jika gagal"""
    for attempt in range(retries):
        try:
            logger.info(f"🔄 Membuka URL: {url} (Percobaan ke-{attempt + 1})")
            driver.get(url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            return
        except Exception as e:
            logger.warning(f"⚠️ Gagal membuka {url}, percobaan ke-{attempt + 1}: {e}")
            if attempt == retries - 1:
                logger.error("❌ Semua percobaan gagal. Menghentikan task.")
                driver.quit()
                raise Exception(f"Gagal membuka {url}")
            time.sleep(delay + random.random())
    raise Exception(f"Gagal membuka {url}")

# --- EXTRACT BERITA KEMARIN ---
def extract_yesterday_news(**kwargs):
    driver = inisialisasi_webdriver()
    base_url = "http://www.iqplus.info/news/stock_news/go-to-page"
    target_date = (datetime.now(JAKARTA_TZ) - timedelta(days=1)).date()  # Kemarin (1 hari yang lalu)
    berita_kemarin = []
    try:
        page = 3
        while page <= MAX_PAGES:
            logger.info(f"📄 Membuka halaman {page}...")
            logger.info(f"🎯 Target date: {target_date}")
            retry_get(driver, f"{base_url},{page}.html")

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "load_news"))
                )
            except TimeoutException:
                logger.warning("⏰ Elemen load_news tidak ditemukan dalam waktu timeout")
                break

            try:
                berita_section = driver.find_element(By.ID, "load_news")
                berita_list_element = berita_section.find_element(By.CLASS_NAME, "news")
                berita_items = berita_list_element.find_elements(By.TAG_NAME, "li")
            except NoSuchElementException:
                logger.warning("🛑 Tidak ada berita di halaman ini.")
                break            
            if not berita_items:
                logger.warning("🛑 Tidak ada berita di halaman ini.")
                break
            
            logger.info(f"📊 Ditemukan {len(berita_items)} berita di halaman {page}")
            any_news_from_target = False
            oldest_date_on_page = None

            for i in range(len(berita_items)):
                try:
                    # Hindari StaleElementReferenceException
                    berita_section = driver.find_element(By.ID, "load_news")
                    berita_list_element = berita_section.find_element(By.CLASS_NAME, "news")
                    berita_items = berita_list_element.find_elements(By.TAG_NAME, "li")
                    if i >= len(berita_items):
                        continue
                        
                    berita = berita_items[i]
                    link_element = berita.find_element(By.TAG_NAME, "a")
                    public_date_str = berita.find_element(By.TAG_NAME, "b").text.strip()
                    
                    try:
                # Format tanggal bisa berbeda-beda, coba beberapa format
                        public_date_clean = public_date_str.replace(" - ", " ")
                        try:
                            # Format 1: DD/MM/YY HH:MM
                            berita_date = datetime.strptime(public_date_clean, "%d/%m/%y %H:%M").date()
                        except ValueError:
                            try:
                                # Format 2: DD/MM/YY tanpa waktu
                                if "/" in public_date_clean:
                                    date_part = public_date_clean.split(" ")[0]
                                    logger.info(f"Parsing date part: {date_part}")
                                    day, month, year = date_part.split("/")
                                    # Pastikan tahun 2 digit dikonversi ke 4 digit dengan benar
                                    year_int = int(year)
                                    full_year = 2000 + year_int if year_int < 50 else 1900 + year_int
                                    berita_date = datetime(full_year, int(month), int(day)).date()
                                else:
                                    raise ValueError("Format tanggal tidak dikenali")
                            except Exception as e:
                                logger.warning(f"Gagal parse format kedua: {e}")
                                # Format 3: "DD Bulan YYYY" (e.g., "26 Mei 2025")
                                try:
                                    bulan_indo = {
                                        'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
                                        'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
                                        'september': 9, 'oktober': 10, 'november': 11, 'desember': 12
                                    }
                                    parts = public_date_clean.split()
                                    if len(parts) >= 3:
                                        day = int(parts[0])
                                        month = bulan_indo.get(parts[1].lower(), 1)
                                        year = int(parts[2])
                                        berita_date = datetime(year, month, day).date()
                                    else:
                                        raise ValueError("Format tanggal tidak dikenali")
                                except Exception:
                                    logger.error(f"Semua format parsing gagal untuk: {public_date_str}")
                                    raise
                        
                        logger.info(f"Berhasil parse tanggal: {public_date_str} -> {berita_date}")
                        if oldest_date_on_page is None or berita_date < oldest_date_on_page:
                            oldest_date_on_page = berita_date
                    except ValueError as ve:
                        logger.warning(f"📅 Format tanggal salah: {public_date_str} | Error: {ve}")
                        continue

                    # Hanya proses jika tanggal berita adalah kemarin
                    if berita_date == target_date:
                        any_news_from_target = True
                        judul = link_element.text.strip()
                        link = link_element.get_attribute("href")

                        # Buka halaman detail berita
                        retry_get(driver, link)
                        time.sleep(2)

                        try:
                            content_element = driver.find_element(By.ID, "zoomthis")
                            konten = content_element.text.strip()
                        except NoSuchElementException:
                            konten = "Konten tidak ditemukan"
                            logger.warning("📝 Konten tidak ditemukan di halaman berita.")

                        # Tambahkan ke list berita
                        berita_data = {
                            "headline": judul,
                            "link": link,
                            "published_at": public_date_str,
                            "content": konten
                        }
                        
                        berita_kemarin.append(berita_data)
                        logger.info(f"📰 Berhasil ekstrak berita: {judul}")
                        
                        # Kembali ke halaman list
                        retry_get(driver, f"{base_url},{page}.html")
                        time.sleep(2)

                except Exception as e:
                    logger.error(f"❌ Error saat memproses berita ke-{i+1}: {e}")
                    continue  # Lanjut ke berita berikutnya
            
            # Jika ada berita dari target date di halaman ini, atau belum ada berita yang ditemukan,
            # dan tanggal terlama di halaman ini masih >= target date, lanjutkan ke halaman berikutnya
            if (any_news_from_target or not berita_kemarin) and (oldest_date_on_page is None or oldest_date_on_page >= target_date):
                page += 1
            else:
                # Jika berita di halaman ini lebih lama dari target date, berhenti
                logger.info("🔚 Halaman berikutnya berisi berita yang lebih lama dari target date, berhenti.")
                break

        logger.info(f"🏁 Total berita dari kemarin yang berhasil dikumpulkan: {len(berita_kemarin)}")
        kwargs['ti'].xcom_push(key='berita_kemarin', value=berita_kemarin)
        return berita_kemarin

    finally:
        driver.quit()

# --- TRANSFORM BERITA MULTIPLE ---
def transform_multiple_news(**kwargs):
    ti = kwargs['ti']
    berita_list = ti.xcom_pull(key='berita_kemarin')
    
    if not berita_list:
        logger.warning("🚫 Tidak ada berita untuk ditransformasi")
        return []
        
    transformed_list = []
    
    for berita in berita_list:
        system_prompt = """
        Anda adalah analis keuangan. Untuk berita berikut, lakukan:
        1. Analisis sentimen (positive/neutral/negative) dan confidence (0.0-1.0)
        2. Ekstrak ticker saham (jika ada)
        3. Buat ringkasan 1-3 kalimat dalam Bahasa Indonesia
        Format output JSON:
        {"sentiment":..., "confidence":..., "tickers": [...], "reasoning":..., "summary":...}
        """

        user_prompt = f"""
        Headline: {berita['headline']}
        Content: {berita['content']}
        """

        payload = {
            "model": "phi3",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        }
        #cek apakah payload sudah sesuai
        if not isinstance(payload, dict) or "model" not in payload or "messages" not in payload:
            logger.error("❌ Payload tidak valid, harus berupa dict dengan 'model' dan 'messages'")
            continue
        else:
            logger.info("✅ Payload valid, siap dikirim ke LLM dengan model: %s", payload["model"])

        try:            
            logger.info(f"🧠 Memproses berita dengan LLM: {berita['headline']}")
            # Coba API utama terlebih dahulu
            try:
                resp = requests.post(OLLAMA_API, json=payload, timeout=120)
                resp.raise_for_status()
            except (requests.exceptions.RequestException, requests.exceptions.ConnectionError):
                logger.warning("❗ Gagal terhubung ke container Ollama, mencoba fallback API")
                resp = requests.post(OLLAMA_FALLBACK_API, json=payload, timeout=120)
                resp.raise_for_status()
            result = resp.json()

            content = result.get("message", {}).get("content") or result["choices"][0]["message"]["content"]

            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                match = re.search(r'\{.*\}', content, re.DOTALL)
                data = json.loads(match.group(0)) if match else {}

            transformed = {
                "headline": berita["headline"],
                "link": berita["link"],
                "published_at": berita["published_at"],
                "content": berita["content"],
                **data
            }

            transformed_list.append(transformed)
            logger.info(f"✅ Berhasil transform berita: {berita['headline']}")

        except Exception as e:
            logger.error(f"❌ Gagal memproses berita '{berita['headline']}': {e}")
            transformed_list.append({
                "headline": berita["headline"], 
                "error": str(e),
                "link": berita.get("link", ""),
                "published_at": berita.get("published_at", ""),
                "content": berita.get("content", "")
            })
    
    ti.xcom_push(key='berita_transformed', value=transformed_list)
    return transformed_list

# --- LOAD BERITA MULTIPLE KE MONGODB ---
def load_multiple_news(**kwargs):
    ti = kwargs['ti']
    transformed_list = ti.xcom_pull(key='berita_transformed')
    
    if not transformed_list:
        logger.warning("🚫 Tidak ada berita untuk disimpan")
        return 0
    
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION]
    
    inserted = 0
    
    for transformed in transformed_list:
        if "error" in transformed:
            logger.warning(f"⚠️ Melewati berita '{transformed['headline']}' karena error: {transformed['error']}")
            continue
            
        if not transformed.get("headline") or not transformed.get("summary"):
            logger.warning(f"⚠️ Melewati berita '{transformed.get('headline', 'Unknown')}' karena tidak ada headline atau summary")
            continue
            
        filter_criteria = {"headline": transformed["headline"], "published_at": transformed["published_at"]}
        if collection.find_one(filter_criteria):
            logger.info(f"🔁 Berita duplikat dilewati: {transformed['headline']}")
            continue

        try:
            dt = datetime.strptime(transformed["published_at"], "%d/%m/%y %H:%M")
            dt = JAKARTA_TZ.localize(dt)
            transformed["effective_date"] = dt.isoformat()
        except Exception as e:
            logger.warning(f"⚠️ Gagal parse tanggal untuk '{transformed['headline']}': {e}")
            transformed["effective_date"] = transformed["published_at"]

        collection.insert_one(transformed)
        inserted += 1
        logger.info(f"💾 Berhasil menyimpan: {transformed['headline']}")
    
    logger.info(f"🏁 Total berita berhasil disimpan: {inserted} dari {len(transformed_list)}")
    return inserted

# --- DAG DEFINITION ---
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'etl_iqplus_multiple_news_dag',
    default_args=default_args,
    schedule_interval='0 7 * * *',  # Setiap hari jam 7 pagi
    catchup=False,
    description='ETL untuk berita kemarin: Extract -> Transform -> Load',
    tags=['etl', 'iqplus', 'llm', 'mongodb', 'multiple']
)

extract_task = PythonOperator(
    task_id='extract_yesterday_news',
    python_callable=extract_yesterday_news,
    provide_context=True,
    dag=dag
)

transform_task = PythonOperator(
    task_id='transform_multiple_news',
    python_callable=transform_multiple_news,
    provide_context=True,
    dag=dag
)

load_task = PythonOperator(
    task_id='load_multiple_news',
    python_callable=load_multiple_news,
    provide_context=True,
    dag=dag
)

# --- ALUR TASK ---
extract_task >> transform_task >> load_task
