# ETL IQPlus Financial News DAG

Folder ini berisi pipeline ETL (Extract, Transform, Load) untuk berita IQPlus:
- Extract: Scraping berita dari IQPlus (menggunakan Selenium)
- Transform: Analisis berita menggunakan LLM (LM Studio) dari modul financial-news-analyzer-main
- Load: Simpan hasil ke MongoDB (host.docker.internal), timezone Asia/Jakarta, tanggal dimundurkan 2 hari

Pipeline ini berjalan di Docker dan dapat diintegrasikan dengan Airflow.

Struktur:
- dags/etl_iqplus_financial_dag.py  # DAG utama
- requirements.txt                  # Dependensi Python
- Dockerfile                        # Image Airflow + Selenium + LM Studio client

Pastikan LM Studio API berjalan di localhost:1234 dan MongoDB dapat diakses dari container.
