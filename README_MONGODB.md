# 🗄️ MongoDB Operations Guide - ETL IQPlus

Panduan lengkap untuk mengoperasikan dan memonitor MongoDB dalam sistem ETL IQPlus.

## 📋 **Daftar Isi**
- [Quick Commands](#-quick-commands)
- [MongoDB Collections](#-mongodb-collections)
- [Data Exploration](#-data-exploration)
- [Analytics Queries](#-analytics-queries)
- [Troubleshooting](#-troubleshooting)
- [Export Data](#-export-data)

---

## 🚀 **Quick Commands**

### **1. Cek Status Container MongoDB**
```powershell
# Cek apakah MongoDB container berjalan
docker ps | findstr mongodb

# Cek logs MongoDB
docker logs mongodb --tail 20
```

### **2. Akses MongoDB Shell**
```powershell
# Masuk ke MongoDB shell
docker exec -it mongodb mongosh

# Langsung akses database iqplus_db
docker exec -it mongodb mongosh iqplus_db
```

### **3. Quick Health Check**
```powershell
# Cek databases yang tersedia
docker exec mongodb mongosh --eval "show dbs"

# Cek collections di iqplus_db
docker exec mongodb mongosh --eval "use iqplus_db; show collections"

# Cek jumlah data di semua collections
docker exec mongodb mongosh --eval "
use iqplus_db; 
print('raw_news:', db.raw_news.countDocuments()); 
print('processed_news:', db.processed_news.countDocuments()); 
print('final_news:', db.final_news.countDocuments()); 
print('news_analytics:', db.news_analytics.countDocuments());"
```

---

## 📊 **MongoDB Collections**

### **Collection Structure:**

| Collection | Deskripsi | Source | Schema |
|------------|-----------|---------|---------|
| `raw_news` | Data mentah hasil extraction | Extraction Service | headline, link, content, published_at, extracted_at |
| `processed_news` | Data dengan sentiment analysis | Transform Service | + sentiment, confidence, tickers, reasoning |
| `final_news` | Data final siap analisis | Load Service | Complete processed data |
| `news_analytics` | Summary dan statistik | Analytics Service | sentiment_distribution, top_tickers, etc. |

---

## 🔍 **Data Exploration**

### **1. Melihat Sample Data**

#### **Raw News (Data Mentah)**
```powershell
# Lihat 1 sample raw news
docker exec mongodb mongosh --eval "db.raw_news.findOne()" iqplus_db

# Lihat 5 berita terbaru
docker exec mongodb mongosh --eval "db.raw_news.find().sort({extracted_at: -1}).limit(5)" iqplus_db
```

#### **Processed News (Dengan Sentiment)**
```powershell
# Lihat 1 sample processed news
docker exec mongodb mongosh --eval "db.processed_news.findOne()" iqplus_db

# Lihat berita dengan sentiment positif
docker exec mongodb mongosh --eval "db.processed_news.find({sentiment: 'positive'}).limit(3)" iqplus_db

# Lihat berita dengan sentiment negatif
docker exec mongodb mongosh --eval "db.processed_news.find({sentiment: 'negative'})" iqplus_db
```

#### **Analytics Summary**
```powershell
# Lihat analytics terbaru
docker exec mongodb mongosh --eval "db.news_analytics.find().sort({generated_at: -1}).limit(1)" iqplus_db
```

### **2. Filter Data Berdasarkan Tanggal**

```powershell
# Berita hari ini
$TODAY = Get-Date -Format "yyyy-MM-dd"
docker exec mongodb mongosh --eval "db.processed_news.find({extracted_at: {`$regex: '$TODAY'}})" iqplus_db

# Berita minggu ini
docker exec mongodb mongosh --eval "db.processed_news.find({extracted_at: {`$gte: new Date(Date.now() - 7*24*60*60*1000)}})" iqplus_db
```

### **3. Filter Berdasarkan Ticker Saham**

```powershell
# Berita untuk ticker tertentu (contoh: TLKM)
docker exec mongodb mongosh --eval "db.processed_news.find({tickers: 'TLKM'})" iqplus_db

# Berita untuk multiple tickers
docker exec mongodb mongosh --eval "db.processed_news.find({tickers: {`$in: ['TLKM', 'BRIS', 'ANTM']}})" iqplus_db
```

---

## 📈 **Analytics Queries**

### **1. Sentiment Distribution**
```powershell
# Distribusi sentiment
docker exec mongodb mongosh --eval "
db.processed_news.aggregate([
  {`$group: {_id: '`$sentiment', count: {`$sum: 1}}},
  {`$sort: {count: -1}}
])" iqplus_db
```

### **2. Top Tickers**
```powershell
# Top 10 tickers paling banyak diberitakan
docker exec mongodb mongosh --eval "
db.processed_news.aggregate([
  {`$unwind: '`$tickers'},
  {`$group: {_id: '`$tickers', count: {`$sum: 1}}},
  {`$sort: {count: -1}},
  {`$limit: 10}
])" iqplus_db
```

### **3. Sentiment per Ticker**
```powershell
# Sentiment analysis per ticker
docker exec mongodb mongosh --eval "
db.processed_news.aggregate([
  {`$unwind: '`$tickers'},
  {`$group: {
    _id: {ticker: '`$tickers', sentiment: '`$sentiment'}, 
    count: {`$sum: 1}
  }},
  {`$sort: {'_id.ticker': 1, 'count': -1}}
])" iqplus_db
```

### **4. Confidence Score Analysis**
```powershell
# Average confidence per sentiment
docker exec mongodb mongosh --eval "
db.processed_news.aggregate([
  {`$group: {
    _id: '`$sentiment',
    avg_confidence: {`$avg: '`$confidence'},
    count: {`$sum: 1}
  }},
  {`$sort: {avg_confidence: -1}}
])" iqplus_db
```

---

## 🛠️ **Troubleshooting**

### **1. Container Issues**
```powershell
# Restart MongoDB container
docker-compose restart mongodb

# Cek error logs
docker logs mongodb --tail 50

# Cek resource usage
docker stats mongodb --no-stream
```

### **2. Connection Issues**
```powershell
# Test koneksi dari container lain
docker exec extraction-iqplus curl -f http://mongodb:27017/ || echo "MongoDB tidak dapat diakses"

# Cek network
docker network ls | findstr etl
```

### **3. Data Issues**
```powershell
# Cek ukuran database
docker exec mongodb mongosh --eval "db.stats()" iqplus_db

# Cek index yang tersedia
docker exec mongodb mongosh --eval "db.processed_news.getIndexes()" iqplus_db
```

---

## 📤 **Export Data**

### **1. Export ke JSON**
```powershell
# Export processed news ke file JSON
docker exec mongodb mongoexport --db=iqplus_db --collection=processed_news --out=/tmp/processed_news.json

# Copy file ke host
docker cp mongodb:/tmp/processed_news.json ./data_export/
```

### **2. Export ke CSV**
```powershell
# Export basic fields ke CSV
docker exec mongodb mongoexport --db=iqplus_db --collection=processed_news --type=csv --fields=headline,sentiment,confidence,tickers --out=/tmp/news_sentiment.csv

# Copy ke host
docker cp mongodb:/tmp/news_sentiment.csv ./data_export/
```

### **3. Backup Database**
```powershell
# Backup complete database
docker exec mongodb mongodump --db iqplus_db --out /tmp/backup

# Copy backup ke host
docker cp mongodb:/tmp/backup ./backup/$(Get-Date -Format "yyyy-MM-dd")
```

---

## 🎯 **Use Cases Examples**

### **Monitoring ETL Pipeline**
```powershell
# Cek progress extraction hari ini
$TODAY = Get-Date -Format "yyyy-MM-dd"
docker exec mongodb mongosh --eval "
print('=== ETL PROGRESS HARI INI ===');
print('Raw News:', db.raw_news.countDocuments({extracted_at: {`$regex: '$TODAY'}}));
print('Processed News:', db.processed_news.countDocuments({processed_at: {`$regex: '$TODAY'}}));
print('Analytics Generated:', db.news_analytics.countDocuments({generated_at: {`$regex: '$TODAY'}}));
" iqplus_db
```

### **Quality Assurance**
```powershell
# Cek data yang belum diproses
docker exec mongodb mongosh --eval "
print('=== DATA QUALITY CHECK ===');
print('Raw news tanpa processing:', db.raw_news.countDocuments() - db.processed_news.countDocuments());
print('News dengan confidence rendah:', db.processed_news.countDocuments({confidence: {`$lt: 0.5}}));
print('News tanpa ticker:', db.processed_news.countDocuments({tickers: {`$size: 0}}));
" iqplus_db
```

### **Business Intelligence**
```powershell
# Market sentiment overview
docker exec mongodb mongosh --eval "
print('=== MARKET SENTIMENT OVERVIEW ===');
var analytics = db.news_analytics.findOne({}, {}, {sort: {generated_at: -1}});
if(analytics) {
  print('Total News:', analytics.total_news);
  print('Positive:', analytics.sentiment_distribution.positive, '(' + analytics.sentiment_percentage.positive + '%)');
  print('Neutral:', analytics.sentiment_distribution.neutral, '(' + analytics.sentiment_percentage.neutral + '%)');
  print('Negative:', analytics.sentiment_distribution.negative, '(' + analytics.sentiment_percentage.negative + '%)');
  print('Top Tickers:', analytics.top_tickers.slice(0,5).map(t => t[0] + ':' + t[1]).join(', '));
}
" iqplus_db
```

---

## 🔗 **Related Commands**

- **Start MongoDB**: `docker-compose up mongodb -d`
- **Stop MongoDB**: `docker-compose stop mongodb`
- **Reset MongoDB**: `docker-compose down && docker volume rm etl-iqplus_mongodb_data && docker-compose up mongodb -d`
- **MongoDB Logs**: `docker logs mongodb -f`

---

## 📝 **Notes**

1. **Performance**: MongoDB indexes otomatis dibuat untuk field yang sering diquery
2. **Backup**: Disarankan backup berkala menggunakan script otomatis
3. **Monitoring**: Gunakan MongoDB Compass untuk GUI monitoring (opsional)
4. **Security**: Dalam production, setup authentication dan SSL

---

**🎯 Pro Tips:**
- Gunakan `--pretty` untuk output yang lebih rapi: `mongosh --eval "db.collection.find().pretty()"`
- Batasi output dengan `.limit(n)` untuk query besar
- Gunakan projection untuk mengambil field tertentu saja: `.find({}, {headline: 1, sentiment: 1})`
