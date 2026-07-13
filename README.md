# 🛠️ IT Saha Ziyaret ve Takip Otomasyonu

IT Sistem ve Saha Destek personeli için geliştirilmiş, modern ve kullanıcı dostu bir **Saha Ziyaret Takip Uygulaması**.  
Streamlit tabanlı, SQLite veritabanı kullanan, yerel ağda çoklu kullanıcıya açılabilen bir masa üstü web uygulamasıdır.

---

## ✨ Özellikler

| Modül | Açıklama |
|---|---|
| 🏠 **Dashboard** | Aylık trend, firma dağılımı, teknisyen grafiği — Altair ile |
| ➕ **Yeni Kayıt** | Tarih, firma (otomatik tamamlama), konu, notlar, süre takibi |
| 📊 **Raporlar** | Genel / aylık raporlar, Excel (.xlsx) ve PDF (.pdf) dışa aktarım |
| 🗂️ **Tüm Kayıtlar** | Arama, filtre, düzenleme ve silme |
| 🔔 **Hatırlatıcılar** | Öncelik bazlı (Acil / Önemli / Normal) periyodik bakım uyarıları |
| 🗓️ **Takvim** | Ziyaretleri aylık takvimde görme, güne tıklayarak detay |
| 📋 **Yapılacaklar** | To-Do listesi — son tarih, öncelik, tamamlama takibi |
| 🔎 **Global Arama** | Tüm notlarda, firma/konu/teknisyen alanlarında tam metin arama |

---

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.10+
- pip

### Kurulum

```bash
# Depoyu klonlayın
git clone https://github.com/vasbabas/it-saha-ziyaret-takip.git
cd it-saha-ziyaret-takip

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
streamlit run app.py
```

Ya da Windows'ta `BASLAT.bat` dosyasına çift tıklayın.

### Aynı Ağda Kullanım

Uygulama çalışırken terminalde görünen **Network URL**'yi diğer cihazların tarayıcısına yazın:

```
http://192.168.x.x:8501
```

---

## 📁 Proje Yapısı

```
├── app.py          # Ana Streamlit uygulaması (8 sekme)
├── database.py     # SQLite veritabanı katmanı (CRUD + analiz sorguları)
├── reports.py      # Excel ve PDF rapor üretimi
├── BASLAT.bat      # Windows tek tıkla başlatıcı
├── requirements.txt
└── .gitignore
```

> **Not:** `visits.db` (veritabanı dosyası) `.gitignore` ile dışarıda bırakılmıştır — kişisel verileriniz GitHub'a yüklenmez.

---

## 🛠️ Teknoloji Yığını

- **[Streamlit](https://streamlit.io/)** — Web arayüzü
- **[Altair](https://altair-viz.github.io/)** — İnteraktif grafikler
- **[SQLite](https://www.sqlite.org/)** — Yerel veritabanı
- **[openpyxl](https://openpyxl.readthedocs.io/)** — Excel raporu
- **[ReportLab](https://www.reportlab.com/)** — PDF raporu

---

## 📄 Lisans

MIT License — Kişisel ve kurumsal kullanım serbesttir.
