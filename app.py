import os
import re
import json
import urllib.request
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
if "uploaded_files_sig" not in st.session_state:
    st.session_state.uploaded_files_sig = None


def _clean_markdown(text: str) -> str:
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    cleaned = re.sub(r"__(.*?)__", r"\1", cleaned)
    return cleaned.strip()


def _extract_copy_sections(ad_text: str) -> dict[str, str]:
    sections = {"title": "", "description": "", "hashtags": ""}

    title_match = re.search(
        r"###\s*3\..*?\n(.*?)(?=\n###\s*4\.|\Z)", ad_text, flags=re.DOTALL
    )
    if title_match:
        lines = [line.strip() for line in title_match.group(1).strip().splitlines() if line.strip()]
        if lines:
            first_title = re.sub(r"^\d+[\.\)]\s*", "", lines[0])
            sections["title"] = _clean_markdown(first_title)

    desc_match = re.search(
        r"###\s*4\..*?\n(.*?)(?=\n###\s*5\.|\Z)", ad_text, flags=re.DOTALL
    )
    if desc_match:
        sections["description"] = _clean_markdown(desc_match.group(1))

    tags_match = re.search(
        r"###\s*5\..*?\n(.*?)(?=\n###\s*6\.|\Z)", ad_text, flags=re.DOTALL
    )
    if tags_match:
        sections["hashtags"] = _clean_markdown(tags_match.group(1))

    return sections


# --- ANA EKRAN ---
st.title("🏷️ HızlıSat AI")
st.caption("Ürünün fotoğrafını yükle; yapay zeka saniyeler içinde ideal satış fiyatını, kargo boyutunu, başlıkları ve açıklamayı ücretsiz hazırlasın.")

st.divider()

uploaded_files = st.file_uploader(
    "Ürün Fotoğrafı Yükle (En fazla 3 fotoğraf – JPG, PNG, WEBP)",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True,
)

if uploaded_files:
    if len(uploaded_files) > 3:
        st.warning("En fazla 3 fotoğraf analiz edilir; ilk 3 fotoğraf seçildi.")
        uploaded_files = uploaded_files[:3]

    current_sig = [(f.name, f.size) for f in uploaded_files]
    if st.session_state.uploaded_files_sig != current_sig:
        st.session_state.uploaded_files_sig = current_sig
        st.session_state.generated_ad = None
else:
    if st.session_state.uploaded_files_sig is not None:
        st.session_state.uploaded_files_sig = None
        st.session_state.generated_ad = None

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

    with st.expander("➕ Ürün Detayları Ekle (İsteğe Bağlı – Marka, Model, Beden/Özellik)", expanded=False):
        st.caption("Fotoğraftan net anlaşılmayan marka, beden veya teknik detayları eklerseniz fiyat ve başlıklar çok daha isabetli olur.")
        brand_model = st.text_input(
            "Marka / Model",
            placeholder="Örn: Zara, Nike Air Force, Asus Vivobook, Tefal..."
        )
        specs = st.text_input(
            "Beden / Ölçü / Teknik Özellik",
            placeholder="Örn: M Beden, 42 Numara, 16 GB RAM / 512 GB SSD, 2024 alım..."
        )
        extra_notes = st.text_input(
            "Ek Notlar / Kusur Durumu",
            placeholder="Örn: Faturası ve kutusu var, sağ kolda minik leke var..."
        )

    generate_clicked = st.form_submit_button("🚀 Fiyat ve İlan Oluştur", type="primary", use_container_width=True)

images: list[Image.Image] = []
if uploaded_files:
    images = [Image.open(f) for f in uploaded_files]
    if len(images) == 1:
        st.image(images[0], caption="Yüklenen Ürün", width=350)
    else:
        img_cols = st.columns(len(images))
        for idx, img in enumerate(images):
            with img_cols[idx]:
                st.image(img, caption=f"Fotoğraf {idx + 1}", use_container_width=True)
else:
    st.info("Başlamak için yukarıdan satmak istediğin ürünün fotoğrafını seç (etiket veya kusur fotoğrafı da ekleyebilirsin).")

ad_placeholder = st.empty()
rendered_in_this_run = False

if generate_clicked:
    if not images:
        st.warning("Lütfen önce en az bir ürün fotoğrafı yükleyin.")
    else:
        try:
            with ad_placeholder.container():
                st.success("İlan paketin hazırlanıyor...")
                result = st.write_stream(
                    analyze_product_stream(
                        images=images,
                        platform=platform,
                        condition=condition,
                        brand_model=brand_model,
                        specs=specs,
                        extra_notes=extra_notes,
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

# --- OLUŞAN İLAN, TEK TIKLA KOPYALAMA VE REVİZYON ---
if st.session_state.generated_ad:
    if not rendered_in_this_run:
        with ad_placeholder.container():
            st.success("İlan paketin hazır! Aşağıdaki kutulardan tek dokunuşla kopyalayabilirsin.")
            st.markdown(st.session_state.generated_ad)

    copy_sections = _extract_copy_sections(st.session_state.generated_ad)
    if any(copy_sections.values()):
        st.divider()
        st.subheader("📋 Tek Tıkla Kopyala")
        st.caption("Kutuların sağ üst köşesindeki kopyala simgesine dokunarak doğrudan ilana yapıştırabilirsin.")
        if copy_sections["title"]:
            st.markdown("**İlan Başlığı:**")
            st.code(copy_sections["title"], language=None, wrap_lines=True)
        if copy_sections["description"]:
            st.markdown("**İlan Açıklaması:**")
            st.code(copy_sections["description"], language=None, wrap_lines=True)
        if copy_sections["hashtags"]:
            st.markdown("**Etiketler:**")
            st.code(copy_sections["hashtags"], language=None, wrap_lines=True)

    st.divider()
    st.subheader("✏️ İlanı Fikrine Göre Özelleştir")
    st.caption("Tek tıkla hızlı düzenleme yapabilir veya aşağıya kendi isteğini yazabilirsin.")

    revision_prompt_to_run = None

    qcol1, qcol2, qcol3 = st.columns(3)
    with qcol1:
        if st.button("📉 Fiyatı %15 Düşür", use_container_width=True):
            revision_prompt_to_run = "Fiyat önerilerini yaklaşık %15 daha hızlı satılacak seviyeye düşür ve açıklamayı buna göre güncelle."
    with qcol2:
        if st.button("🤝 Pazarlık Ekle", use_container_width=True):
            revision_prompt_to_run = "İlan açıklamasına ciddi alıcıyla makul pazarlık payı olduğu ve hızlı kargo yapılacağı bilgisini ekle."
    with qcol3:
        if st.button("✂️ Daha Kısa Yaz", use_container_width=True):
            revision_prompt_to_run = "İlan açıklamasını daha kısa, öz ve maddeler halinde kolay okunur şekilde sadeleştir."

    with st.form("revision_form"):
        revision_idea = st.text_area(
            "Özel İstek Yaz (İsteğe bağlı)",
            placeholder="Örn: Fiyatı 150 TL bandına çekelim, öğrenciye indirim yapılabileceğini ekleyelim...",
            height=85
        )
        revise_clicked = st.form_submit_button("🔄 İsteğime Göre Yeni İlan Oluştur", use_container_width=True)

    if revise_clicked:
        if not revision_idea.strip():
            st.warning("Lütfen ilanda nasıl bir değişiklik istediğini kısaca yaz.")
        else:
            revision_prompt_to_run = revision_idea.strip()

    if revision_prompt_to_run:
        try:
            with ad_placeholder.container():
                st.success("İlan isteğine göre güncelleniyor...")
                updated_ad = st.write_stream(
                    refine_listing_stream(
                        current_listing=st.session_state.generated_ad,
                        user_feedback=revision_prompt_to_run,
                        platform=st.session_state.last_platform,
                        condition=st.session_state.last_condition
                    )
                )
            st.session_state.generated_ad = updated_ad
            st.rerun()
        except Exception as e:
            st.error(f"İlan güncellenirken bir hata oluştu: {e}")

    if st.button("🗑️ Yeni Ürün İçin Ekranı Temizle", use_container_width=True):
        st.session_state.generated_ad = None
        st.rerun()

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
            placeholder="Örn: Çok hızlı ilan oluşturdu, yeni özellik olarak...",
            height=95
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
            if feedback_endpoint.startswith("http") and "..." not in feedback_endpoint:
                try:
                    payload = json.dumps({
                        "puan": rating,
                        "mesaj": user_suggestion.strip(),
                        "iletisim": user_contact.strip() or "Belirtilmedi"
                    }).encode("utf-8")
                    req = urllib.request.Request(
                        feedback_endpoint,
                        data=payload,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                            "User-Agent": "Mozilla/5.0 (HizliSat-AI/1.0)"
                        }
                    )
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        if 200 <= resp.status < 300:
                            st.success("Teşekkürler! Deneyiminiz ve öneriniz doğrudan geliştiriciye iletildi.")
                        else:
                            st.warning("Geri bildirim sunucusu yanıt vermedi, lütfen daha sonra tekrar deneyin.")
                except Exception:
                    st.warning("Bağlantı nedeniyle gönderilemedi, lütfen daha sonra tekrar deneyin.")
            else:
                st.success("Teşekkürler! Geri bildiriminiz kaydedildi.")

st.divider()
st.caption("🏷️ HızlıSat AI • Yapay Zeka Destekli İkinci El İlan ve Fiyatlandırma Asistanı")