import streamlit as st
from PIL import Image
from analyzer import analyze_product

st.set_page_config(
    page_title="HızlıSat AI | İkinci El İlan & Fiyat Asistanı",
    page_icon="🏷️",
    layout="centered"
)

# --- ANA EKRAN ---
st.title("🏷️ HızlıSat AI")
st.caption("Ürünün fotoğrafını yükle; yapay zeka saniyeler içinde ideal satış fiyatını, dikkat çekici başlıkları ve açıklamayı ücretsiz hazırlasın.")

st.divider()

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
                st.success("İlan paketin hazır! Aşağıdaki metinleri kopyalayıp doğrudan kullanabilirsin.")
                st.markdown(result)
            except Exception as e:
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    st.warning("Yapay zeka sunucularında anlık yoğunluk var. Birkaç saniye bekleyip tekrar butona bas.")
                elif "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    st.warning("Günlük ücretsiz analiz kotası doldu. Lütfen daha sonra tekrar deneyin.")
                else:
                    st.error(f"Bir hata oluştu: {e}")
else:
    st.info("Başlamak için yukarıdan satmak istediğin ürünün fotoğrafını seç.")