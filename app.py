import os
import json
import urllib.request
import urllib.parse
import streamlit as st
from PIL import Image
from analyzer import analyze_product_stream, refine_listing_stream

st.set_page_config(
    page_title="HızlıSat AI | İkinci El İlan & Fiyat Asistanı",
    page_icon="🏷️",
    layout="centered"
)

if "generated_ad" not in st.session_state:
    st.session_state.generated_ad = None
if "last_platform" not in st.session_state:
    st.session_state.last_platform = "Dolap"
if "last_condition" not in st.session_state:
    st.session_state.last_condition = "Az Kullanılmış"

# --- ANA EKRAN ---
st.title("🏷️ HızlıSat AI")
st.caption("Ürünün fotoğrafını yükle; yapay zeka saniyeler içinde ideal satış fiyatını, dikkat çekici başlıkları ve açıklamayı tamamen ücretsiz hazırlasın.")

st.divider()

uploaded_file = st.file_uploader(
    "Ürün Fotoğrafı Yükle (JPG, PNG, WEBP)",
    type=["jpg", "jpeg", "png", "webp"]
)

with st.form("product_form"):
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

    generate_clicked = st.form_submit_button("🚀 Fiyat ve İlan Oluştur", type="primary", use_container_width=True)

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Yüklenen Ürün", width=350)
else:
    st.info("Başlamak için yukarıdan satmak istediğin ürünün fotoğrafını seç.")

ad_placeholder = st.empty()
rendered_in_this_run = False

if generate_clicked:
    if uploaded_file is None:
        st.warning("Lütfen önce ürün fotoğrafı yükleyin.")
    else:
        try:
            with ad_placeholder.container():
                st.success("İlan paketin hazırlanıyor...")
                result = st.write_stream(
                    analyze_product_stream(
                        image=image,
                        platform=platform,
                        condition=condition,
                        extra_notes=extra_notes
                    )
                )
            st.session_state.generated_ad = result
            st.session_state.last_platform = platform
            st.session_state.last_condition = condition
            rendered_in_this_run = True
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                st.warning("Yapay zeka sunucularında anlık yoğunluk var. Birkaç saniye bekleyip tekrar butona bas.")
            elif "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                st.warning("Günlük ücretsiz analiz kotası doldu. Lütfen biraz sonra tekrar deneyin.")
            else:
                st.error(f"Bir hata oluştu: {e}")

# --- OLUŞAN İLAN VE KULLANICI FİKRİNE GÖRE YENİDEN DÜZENLEME ---
if st.session_state.generated_ad:
    if not rendered_in_this_run:
        with ad_placeholder.container():
            st.success("İlan paketin hazır! Aşağıdaki metinleri kopyalayıp doğrudan kullanabilirsin.")
            st.markdown(st.session_state.generated_ad)

    st.divider()
    st.subheader("✏️ İlanı Fikrine Göre Özelleştir")
    st.caption("Oluşan ilanda değiştirmek istediğin yerleri yaz; yapay zeka isteğine göre yeni ilanı hemen hazırlasın.")

    with st.form("revision_form"):
        revision_idea = st.text_area(
            "Nasıl değiştirelim?",
            placeholder="Örn: Fiyatı 150 TL bandına çekelim, öğrenciye indirim yapılabileceğini ekleyelim ve açıklama daha samimi olsun...",
            height=90
        )
        revise_clicked = st.form_submit_button("🔄 İsteğime Göre Yeni İlan Oluştur", use_container_width=True)

    if revise_clicked:
        if not revision_idea.strip():
            st.warning("Lütfen ilanda nasıl bir değişiklik istediğini kısaca yaz.")
        else:
            try:
                with ad_placeholder.container():
                    st.success("Fikrine göre yeni ilan hazırlanıyor...")
                    updated_ad = st.write_stream(
                        refine_listing_stream(
                            current_listing=st.session_state.generated_ad,
                            user_feedback=revision_idea.strip(),
                            platform=st.session_state.last_platform,
                            condition=st.session_state.last_condition
                        )
                    )
                st.session_state.generated_ad = updated_ad
            except Exception as e:
                st.error(f"İlan güncellenirken bir hata oluştu: {e}")

# --- KULLANICI DENEYİMİ, FİKİR VE ÖNERİ FORMU ---
st.divider()
with st.expander("💬 Deneyimini Paylaş & Bize Ulaş (Fikir ve Öneri)", expanded=False):
    st.write("HızlıSat AI'ı geliştirmemize yardımcı olun! Deneyiminizi, karşılaştığınız sorunları veya eklenmesini istediğiniz özellikleri bize yazabilirsiniz.")

    with st.form("feedback_form"):
        rating = st.radio(
            "Uygulama deneyiminizi nasıl değerlendirirsiniz?",
            ["⭐⭐⭐⭐⭐ Çok Beğendim", "⭐⭐⭐⭐ İyi", "⭐⭐⭐ Orta", "⭐⭐ Geliştirilmeli"],
            horizontal=True
        )
        user_suggestion = st.text_area(
            "Fikir, Öneri veya Deneyiminiz",
            placeholder="Örn: Çok hızlı ilan oluşturdu ama kargo boyutu tahmini de eklenirse harika olur...",
            height=100
        )
        user_contact = st.text_input(
            "İletişim Bilginiz (İsteğe bağlı)",
            placeholder="Geri dönüş yapabilmemiz için e-posta veya Instagram kullanıcı adınız..."
        )
        feedback_submitted = st.form_submit_button("📩 Fikir ve Öneriyi Gönder", use_container_width=True)

    if feedback_submitted:
        if not user_suggestion.strip():
            st.warning("Lütfen göndermeden önce görüş veya önerinizi yazın.")
        else:
            feedback_endpoint = os.getenv("FEEDBACK_URL", "").strip()
            contact_email = os.getenv("CONTACT_EMAIL", "").strip()

            if feedback_endpoint:
                try:
                    payload = json.dumps({
                        "puan": rating,
                        "mesaj": user_suggestion.strip(),
                        "iletisim": user_contact.strip() or "Belirtilmedi"
                    }).encode("utf-8")
                    req = urllib.request.Request(
                        feedback_endpoint,
                        data=payload,
                        headers={"Content-Type": "application/json", "Accept": "application/json"}
                    )
                    urllib.request.urlopen(req, timeout=8)
                    st.success("Teşekkürler! Deneyiminiz ve öneriniz doğrudan geliştiriciye iletildi.")
                except Exception:
                    st.error("Gönderim sırasında bağlantı hatası oluştu, lütfen tekrar deneyin.")
            else:
                st.success("Görüşünüz kaydedildi! Doğrudan geliştiriciye e-posta ile iletmek isterseniz aşağıdaki butona tıklayabilirsiniz:")
                subject = urllib.parse.quote(f"HızlıSat AI Geri Bildirim ({rating})")
                body = urllib.parse.quote(
                    f"Deneyim Puanı: {rating}\n"
                    f"İletişim: {user_contact.strip() or 'Belirtilmedi'}\n\n"
                    f"Fikir ve Öneri:\n{user_suggestion.strip()}"
                )
                mailto_link = f"mailto:{contact_email}?subject={subject}&body={body}"
                st.link_button("✉️ E-posta Uygulamasıyla Gönder", mailto_link, use_container_width=True)