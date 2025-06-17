#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extraction Service untuk IQPlus Financial News
Bertugas melakukan scraping berita dan menyimpan ke MongoDB
"""

from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from pymongo import MongoClient
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import pytz
import logging
import os
import time
import random
import json

app = Flask(__name__)

# Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/')
MONGO_DB = 'iqplus_db'
MONGO_COLLECTION = 'raw_news'
CHROME_URL = os.getenv('CHROME_URL', 'http://chrome:4444/wd/hub')
JAKARTA_TZ = pytz.timezone('Asia/Jakarta')
MAX_PAGES = 5

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inisialisasi_webdriver():
    """Inisialisasi WebDriver headless"""
    logger.info("🚀 Memulai inisialisasi WebDriver...")
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless=new')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Remote(
        command_executor=CHROME_URL,
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
                logger.error("❌ Semua percobaan gagal.")
                raise Exception(f"Gagal membuka {url}")
            time.sleep(delay + random.random())

def extract_news_from_date(target_date):
    """Extract berita dari tanggal tertentu"""
    driver = inisialisasi_webdriver()
    base_url = "http://www.iqplus.info/news/stock_news/go-to-page"
    berita_list = []
    
    try:
        page = 1
        while page <= MAX_PAGES:
            logger.info(f"📄 === MEMPROSES HALAMAN {page} ===")
            logger.info(f"🎯 Target date: {target_date}")
            page_url = f"{base_url},{page}.html"
            logger.info(f"🔗 URL yang akan dibuka: {page_url}")
            
            retry_get(driver, page_url)
            logger.info(f"✅ Berhasil membuka halaman {page}")
            
            # Debug: Cek apakah halaman berhasil dimuat
            current_url = driver.current_url
            page_title = driver.title
            logger.info(f"📍 Current URL: {current_url}")
            logger.info(f"📝 Page Title: {page_title}")            # Debug: Check page source length and content
            page_source_length = len(driver.page_source)
            logger.info(f"📏 Page source length: {page_source_length} characters")
            
            # Debug: Cek elemen kunci di halaman
            try:
                body_element = driver.find_element(By.TAG_NAME, "body")
                logger.info("✅ Body element found")
            except NoSuchElementException:
                logger.error("❌ Body element not found!")
                break

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "load_news"))
                )
                logger.info("✅ Element 'load_news' ditemukan")
            except TimeoutException:
                logger.warning("⏰ Elemen load_news tidak ditemukan dalam waktu timeout")
                # Debug: List semua ID yang ada di halaman
                try:
                    all_elements_with_id = driver.find_elements(By.XPATH, "//*[@id]")
                    ids_found = [elem.get_attribute("id") for elem in all_elements_with_id if elem.get_attribute("id")]
                    logger.info(f"🔍 IDs yang ditemukan di halaman: {ids_found[:10]}...")  # Show first 10 IDs
                except Exception as e:
                    logger.warning(f"Error saat mencari IDs: {e}")
                break

            try:
                berita_section = driver.find_element(By.ID, "load_news")
                logger.info("✅ Berhasil menemukan section 'load_news'")
                berita_list_element = berita_section.find_element(By.CLASS_NAME, "news")
                logger.info("✅ Berhasil menemukan class 'news'")
                berita_items = berita_list_element.find_elements(By.TAG_NAME, "li")
                logger.info(f"✅ Berhasil menemukan {len(berita_items)} item <li>")
            except NoSuchElementException as e:
                logger.warning(f"🛑 Tidak dapat menemukan elemen: {e}")
                # Debug: Cek struktur HTML yang ada
                try:
                    load_news_html = driver.find_element(By.ID, "load_news").get_attribute('outerHTML')[:500]
                    logger.info(f"🔍 HTML load_news (first 500 chars): {load_news_html}")
                except:
                    logger.warning("Tidak dapat mengambil HTML load_news")
                break
                      
            if not berita_items:
                logger.warning("🛑 Tidak ada berita di halaman ini.")
                break
            
            logger.info(f"📊 Ditemukan {len(berita_items)} berita di halaman {page}")
            any_news_from_target = False
            oldest_date_on_page = None

            # Debug: Show first few news items found
            logger.info("🔍 === DEBUGGING BERITA YANG DITEMUKAN ===")
            for debug_i, debug_item in enumerate(berita_items[:3]):  # Show first 3 items
                try:
                    debug_link = debug_item.find_element(By.TAG_NAME, "a")
                    debug_date = debug_item.find_element(By.TAG_NAME, "b").text.strip()
                    debug_title = debug_link.text.strip()
                    logger.info(f"📰 Item {debug_i+1}: {debug_title} | Date: {debug_date}")
                except Exception as e:
                    logger.warning(f"Debug error on item {debug_i+1}: {e}")
            logger.info("🔍 === END DEBUGGING ===")

            for i in range(len(berita_items)):
                try:
                    # Hindari StaleElementReferenceException
                    berita_section = driver.find_element(By.ID, "load_news")
                    berita_list_element = berita_section.find_element(By.CLASS_NAME, "news")
                    berita_items = berita_list_element.find_elements(By.TAG_NAME, "li")
                    if i >= len(berita_items):
                        logger.warning(f"⚠️ Index {i} melebihi jumlah berita yang tersedia")
                        continue
                        
                    berita = berita_items[i]
                    link_element = berita.find_element(By.TAG_NAME, "a")
                    public_date_str = berita.find_element(By.TAG_NAME, "b").text.strip()
                    
                    logger.info(f"🔍 Processing berita {i+1}: Date string = '{public_date_str}'")
                    
                    try:
                        # Parse tanggal
                        public_date_clean = public_date_str.replace(" - ", " ")
                        try:
                            # Format 1: DD/MM/YY HH:MM
                            berita_date = datetime.strptime(public_date_clean, "%d/%m/%y %H:%M").date()
                            logger.info(f"✅ Format 1 berhasil: {public_date_clean} -> {berita_date}")
                        except ValueError:
                            try:
                                # Format 2: DD/MM/YY tanpa waktu
                                if "/" in public_date_clean:
                                    date_part = public_date_clean.split(" ")[0]
                                    day, month, year = date_part.split("/")
                                    year_int = int(year)
                                    full_year = 2000 + year_int if year_int < 50 else 1900 + year_int
                                    berita_date = datetime(full_year, int(month), int(day)).date()
                                    logger.info(f"✅ Format 2 berhasil: {public_date_clean} -> {berita_date}")
                                else:
                                    raise ValueError("Format tanggal tidak dikenali")
                            except Exception as e:
                                logger.warning(f"❌ Gagal parse format kedua: {e}")
                                continue
                        
                        if oldest_date_on_page is None or berita_date < oldest_date_on_page:
                            oldest_date_on_page = berita_date
                            
                    except ValueError as ve:
                        logger.warning(f"📅 Format tanggal salah: {public_date_str} | Error: {ve}")
                        continue

                    # Debug: Show comparison
                    logger.info(f"📅 Comparing: berita_date={berita_date} vs target_date={target_date}")

                    # Hanya proses jika tanggal berita sesuai target
                    if berita_date == target_date:
                        any_news_from_target = True
                        judul = link_element.text.strip()
                        link = link_element.get_attribute("href")

                        logger.info(f"🎯 MATCH! Memproses berita: {judul}")

                        # Buka halaman detail berita
                        logger.info(f"🔗 Membuka halaman detail: {link}")
                        retry_get(driver, link)
                        time.sleep(2)

                        try:
                            content_element = driver.find_element(By.ID, "zoomthis")
                            konten = content_element.text.strip()
                            logger.info(f"📝 Berhasil ambil konten ({len(konten)} karakter)")
                        except NoSuchElementException:
                            konten = "Konten tidak ditemukan"
                            logger.warning("📝 Konten tidak ditemukan di halaman berita.")

                        # Tambahkan ke list berita
                        berita_data = {
                            "headline": judul,
                            "link": link,
                            "published_at": public_date_str,
                            "content": konten,
                            "extracted_at": datetime.now(JAKARTA_TZ).isoformat(),
                            "source": "iqplus"
                        }
                        
                        berita_list.append(berita_data)
                        logger.info(f"📰 Berhasil ekstrak berita: {judul}")
                        
                        # Kembali ke halaman list
                        logger.info(f"🔙 Kembali ke halaman list: {page_url}")
                        retry_get(driver, page_url)
                        time.sleep(2)
                    else:
                        logger.info(f"⏭️ Skip berita (tanggal tidak match): {berita_date} != {target_date}")

                except Exception as e:
                    logger.error(f"❌ Error saat memproses berita ke-{i+1}: {e}")
                    continue
            
            # Logika pagination dengan debugging
            logger.info(f"🔍 Pagination check: oldest_date_on_page={oldest_date_on_page}, target_date={target_date}")
            logger.info(f"🔍 any_news_from_target={any_news_from_target}")
            
            should_continue = (oldest_date_on_page is None or oldest_date_on_page >= target_date)
            if should_continue:
                logger.info(f"➡️ Lanjut ke halaman {page + 1} (masih ada kemungkinan berita target)")
                page += 1
            else:
                logger.info("🔚 Halaman berikutnya berisi berita yang lebih lama dari target date, berhenti.")
                break

        logger.info(f"🏁 Total berita berhasil dikumpulkan: {len(berita_list)}")
        return berita_list

    finally:
        driver.quit()

def save_to_mongodb(berita_list):
    """Simpan berita ke MongoDB"""
    if not berita_list:
        logger.warning("🚫 Tidak ada berita untuk disimpan")
        return 0
    
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION]
    
    inserted = 0
    for berita in berita_list:
        # Cek duplikasi
        filter_criteria = {"headline": berita["headline"], "published_at": berita["published_at"]}
        if collection.find_one(filter_criteria):
            logger.info(f"🔁 Berita duplikat dilewati: {berita['headline']}")
            continue
            
        collection.insert_one(berita)
        inserted += 1
        logger.info(f"💾 Berhasil menyimpan: {berita['headline']}")
    
    client.close()
    logger.info(f"🏁 Total berita berhasil disimpan: {inserted} dari {len(berita_list)}")
    return inserted

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "extraction-iqplus"})

@app.route('/extract', methods=['POST'])
def extract_news():
    """Endpoint untuk ekstraksi berita"""
    try:
        data = request.get_json()
        date_str = data.get('date', None)
        
        if date_str:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            # Default ke kemarin
            target_date = (datetime.now(JAKARTA_TZ) - timedelta(days=1)).date()
        
        logger.info(f"🎯 Mulai ekstraksi untuk tanggal: {target_date}")
        berita_list = extract_news_from_date(target_date)
        
        # Simpan ke MongoDB
        inserted_count = save_to_mongodb(berita_list)
        
        # Simpan juga ke file JSON untuk sharing antar container
        output_file = f"/app/data/extracted_news_{target_date.strftime('%Y%m%d')}.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(berita_list, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            "status": "success",
            "message": f"Berhasil ekstrak dan simpan {inserted_count} berita",
            "extracted_count": len(berita_list),
            "inserted_count": inserted_count,
            "target_date": str(target_date),
            "output_file": output_file
        })
        
    except Exception as e:
        logger.error(f"❌ Error dalam ekstraksi: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
