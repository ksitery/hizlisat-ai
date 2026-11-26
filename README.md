# 🏷️ HızlıSat AI — İkinci El İlan ve Fiyatlandırma Asistanı

**HızlıSat AI**, Dolap, Gardrops, Sahibinden ve Letgo gibi ikinci el satış platformlarında ürün satan kullanıcıların yalnızca bir ürün fotoğrafı yükleyerek saniyeler içinde piyasa analizi, fiyat önerisi, algoritma uyumlu başlıklar ve ikna edici ilan açıklamaları oluşturmasını sağlayan yapay zeka destekli bir web uygulamasıdır.

🔗 **Canlı Uygulama:** [hizlisat-ai.streamlit.app](https://hizlisat-ai.streamlit.app)

---

## 📸 Uygulama Ekran Görüntüleri

| Ürün Yükleme ve Detay Girişi | Yapay Zeka İlan Paketi ve Revizyon |
| :---: | :---: |
| ![Ana Ekran](screenshots/ana-ekran.png) | ![İlan Sonucu](screenshots/ilan-sonuc.png) |

---

## ✨ Öne Çıkan Özellikler

* **Hibrit ve Kesintisiz Yapay Zeka Mimarisi:** Birincil motor olarak **Groq Vision / Llama** modellerini kullanarak ultra hızlı (1–2 saniye) yanıt üretir; yoğunluk veya kota durumunda kullanıcıya hata yansıtmadan otomatik olarak **Google Gemini** yedek motoruna ve çoklu API anahtarı havuzuna geçiş yapar.
* **Canlı Akış (Streaming) Deneyimi:** Tüm ilan paketi kelime kelime gerçek zamanlı olarak ekrana akar; kullanıcı yanıtın tamamlanmasını beklemeden çıktıyı okumaya başlar.
* **Akıllı Görsel Optimizasyonu:** Yüklenen fotoğraflar sunucu tarafında `Pillow` ile otomatik olarak `512x512` JPEG formatına dönüştürülüp sıkıştırılır; mobil bağlantılarda dahi düşük gecikme sağlar.
* **İsteğe Bağlı Detay Girişi:** Fotoğraftan net anlaşılamayan marka, model, beden veya teknik özellikler açılır menü üzerinden girilerek fiyat ve başlık isabeti artırılabilir.
* **İnteraktif İlan Revizyonu:** Oluşturulan ilan üzerinde kullanıcının doğal dilde yazdığı değişiklik taleplerine (*"Fiyatı düşür"*, *"Öğrenciye uygun olduğunu vurgula"* vb.) göre ilan anında yeniden düzenlenir.
* **Dahili Geri Bildirim Sistemi:** Kullanıcıların deneyim puanı ve geliştirme önerilerini doğrudan geliştiriciye iletebildiği entegre iletişim modülü içerir.

---

## 🛠️ Kullanılan Teknolojiler

* **Dil & Arayüz:** Python 3, Streamlit (`write_stream`, `st.form`, `session_state`)
* **Yapay Zeka & Görüş Modelleri:** Groq API (Llama Vision & Text), Google GenAI SDK (`gemini-3.5-flash-lite`, `gemini-3.8-flash`)
* **Görüntü İşleme:** Pillow (PIL)
* **Dağıtım (Deployment):** GitHub + Streamlit Community Cloud (0 TL sunucu maliyeti)

---

## 📂 Proje Yapısı

```text
hizlisat-ai/
├── screenshots/
│   ├── ana-ekran.png   # Ürün yükleme ve detay giriş ekranı
│   └── ilan-sonuc.png  # Yapay zeka ilan çıktısı ve revizyon alanı
├── app.py              # Streamlit kullanıcı arayüzü, canlı akış, ilan revizyonu ve geri bildirim formu
├── analyzer.py         # Görsel sıkıştırma, Groq + Gemini hibrit motoru ve otomatik yedekleme mantığı
├── requirements.txt    # Proje bağımlılıkları
└── README.md           # Proje dokümantasyonu
```

---

## 🚀 Yerel Kurulum

1. **Depoyu klonlayın:**
   ```bash
   git clone [https://github.com/ksitery/hizlisat-ai.git](https://github.com/ksitery/hizlisat-ai.git)
   cd hizlisat-ai
   ```

2. **Sanal ortam oluşturun ve bağımlılıkları yükleyin:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Ortam değişkenlerini (`.env`) tanımlayın:**
   ```toml
   GROQ_API_KEY="gsk_..."
   GEMINI_API_KEYS="AIzaSy..."
   FEEDBACK_URL="[https://formspree.io/f/](https://formspree.io/f/)..." # İsteğe bağlı
   ```

4. **Uygulamayı başlatın:**
   ```bash
   streamlit run app.py
   ```