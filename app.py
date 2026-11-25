import os
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from analyzer import analyze_product

load_dotenv()

st.set_page_config(
    page_title="HızlıSat AI | İkinci El İlan & Fiyat Asistanı",
    page_icon="🏷️",
    layout="centered"
)

if "free_uses_left" not in st.session_state:
    st.session_state.free_uses_left = 2
if "is_pro" not in st.session_state:
    st.session_state.is_pro = False
if "used_codes" not in st.session_state:
    st.session_state.used_codes = []

raw_pro_codes = os.getenv("PRO_CODES", "HIZLISAT2026")
valid_pro_codes = [c.strip() for c in raw_pro_codes.split(",") if c.strip()]

raw_single_codes = os.getenv("SINGLE_CODES", "TEK10")
valid_single_codes = [c.strip() for c in raw_single_codes.split(",") if c.strip()]

# --- YAN MENÜ (KREDİ VE AKTİVASYON PANELİ) ---
with st.sidebar:
    st.header("💎 Üyelik Durumu")
    if st.session_state.is_pro:
        st.success("🌟 AYLIK PRO AKTİF\n\nSınırsız ilan ve fiyat analizi yapabilirsiniz.")
    else:
        st.info(f"🎁 Kalan Analiz Hakkı: **{st.session_state.free_uses_left}**")
        st.markdown("---")
        st.subheader("🚀 Paket Satın Al")
        st.write("Yeni ilanlar oluşturmak için size uygun paketi seçip aktivasyon kodunuzu girin:")
        st.markdown(
            "- **Ek Sefer (1 Analiz Hakkı):** 10 TL\n"
            "- **Sınırsız Aylık Pro:** 50 TL"
        )
        # Shopier onayı gelince aşağıdaki iki link kendi ürün linklerinle değişecek:
        st.link_button("⚡ Ek Sefer Al – 10 TL (Shopier)", "https://www.shopier.com", use_container_width=True)
        st.link_button("👑 Aylık Pro Al – 50 TL (Shopier)", "https://www.shopier.com", use_container_width=True)

        st.markdown("---")
        access_code = st.text_input("Aktivasyon Kodunuz", type="password", placeholder="Kodu buraya girin...")
        if st.button("Kodu Aktifleştir", use_container_width=True):
            code = access_code.strip()
            if code in valid_pro_codes:
                st.session_state.is_pro = True
                st.rerun()
            elif code in valid_single_codes:
                if code in st.session_state.used_codes:
                    st.warning("Bu tek seferlik kodu zaten kullandınız.")
                else:
                    st.session_state.free_uses_left += 1
                    st.session_state.used_codes.append(code)
                    st.rerun()
            else:
                st.error("Geçersiz aktivasyon kodu.")

# --- ANA EKRAN ---
st.title("🏷️ HızlıSat AI")
st.caption("Ürünün fotoğrafını yükle; yapay zeka saniyeler içinde ideal satış fiyatını, dikkat çekici başlıkları ve açıklamayı hazırlasın.")

st.divider()

can_analyze = st.session_state.is_pro or st.session_state.free_uses_left > 0

if not can_analyze:
    st.warning("🔒 Ücretsiz analiz haklarınızı doldurdunuz!")
    st.markdown(
        """
        ### İlanlarınızı Hızla Satmaya Devam Edin
        Yeni ürünleriniz için saniyeler içinde piyasa fiyatı, algoritma uyumlu başlık ve hazır açıklama üretmek için paket seçebilirsiniz:
        * **Ek Sefer (1 Analiz Hakkı):** 10 TL
        * **Sınırsız Aylık Pro:** 50 TL
        
        👈 Sol menüdeki **Shopier** butonlarından ödemenizi yaptıktan sonra size iletilen aktivasyon kodunu girerek devam edebilirsiniz.
        """
    )
else:
    uploaded_file = st.file_uploader(
        "Ürün Fotoğrafı Yükle (JPG, PNG, WEBP)",
        type=["jpg", "jpeg", "png", "webp"]
    )

    col1, col2 = st.columns(2)
    with col1:
        platform = st.selectbox(
            "Satış Platformu",
            ["Dolap", "Gardrops", "Sahibinden", "Letgo"]
        )
    with col2:
        condition = st.selectbox(
            "Ürün Durumu",
            ["Sıfır / Etiketli", "Yeni Gibi", "Az Kullanılmış", "Kullanılmış / Yıpranmış"],
            index=2
        )

    extra_notes = st.text_input(
        "Ek Notlar (İsteğe bağlı)",
        placeholder="Örn: Faturası var, kutusu duruyor, sadece 2 kez kullanıldı..."
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Yüklenen Ürün", use_container_width=True)

        if st.button("🚀 Fiyat ve İlan Oluştur", type="primary", use_container_width=True):
            with st.spinner("Ürün inceleniyor, piyasa fiyatı ve satış metni hazırlanıyor..."):
                try:
                    result = analyze_product(
                        image=image,
                        platform=platform,
                        condition=condition,
                        extra_notes=extra_notes
                    )
                    if not st.session_state.is_pro:
                        st.session_state.free_uses_left -= 1
                    st.success("İlan paketin hazır! Aşağıdaki metinleri kopyalayıp doğrudan kullanabilirsin.")
                    st.markdown(result)
                    if not st.session_state.is_pro:
                        st.info(f"Kalan analiz hakkınız: {st.session_state.free_uses_left}")
                except Exception as e:
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        st.warning("Yapay zeka sunucularında anlık yoğunluk var. Birkaç saniye bekleyip tekrar butona bas.")
                    else:
                        st.error(f"Bir hata oluştu: {e}")
    else:
        st.info("Başlamak için yukarıdan satmak istediğin ürünün fotoğrafını seç.")