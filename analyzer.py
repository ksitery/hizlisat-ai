import io
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

FAST_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
]

def _get_api_keys() -> list[str]:
    raw_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY", "")
    return [k.strip() for k in raw_keys.split(",") if k.strip()]

def _prepare_image_part(image: Image.Image) -> types.Part:
    img_copy = image.copy()
    if img_copy.mode in ("RGBA", "P", "LA"):
        img_copy = img_copy.convert("RGB")
    img_copy.thumbnail((512, 512))
    buf = io.BytesIO()
    img_copy.save(buf, format="JPEG", quality=80)
    return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")

def _stream_with_fallback(contents: list):
    api_keys = _get_api_keys()
    if not api_keys:
        raise ValueError("API anahtarı bulunamadı. Lütfen GEMINI_API_KEYS ayarını kontrol edin.")

    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        max_output_tokens=900,
        temperature=0.7,
    )

    errors = []
    for key in api_keys:
        client = genai.Client(api_key=key)
        for model_name in FAST_MODELS:
            for attempt in range(2):
                yielded = False
                try:
                    response = client.models.generate_content_stream(
                        model=model_name,
                        contents=contents,
                        config=config,
                    )
                    for chunk in response:
                        if chunk.text:
                            yielded = True
                            yield chunk.text
                    if yielded:
                        return
                except Exception as e:
                    if yielded:
                        raise
                    err_str = str(e)
                    errors.append(f"{model_name}: {err_str}")
                    if attempt == 0 and ("503" in err_str or "UNAVAILABLE" in err_str):
                        time.sleep(1)
                        continue
                    break

    raise RuntimeError(" | ".join(errors))

def analyze_product_stream(image: Image.Image, platform: str = "Dolap", condition: str = "Az Kullanılmış", extra_notes: str = ""):
    image_part = _prepare_image_part(image)

    prompt = f"""
    Sen Türkiye'deki ikinci el satış platformlarında ({platform}) uzman bir e-ticaret ve fiyatlandırma danışmanısın.
    Görseli incele ve aşağıdaki bilgilere göre kısa, net, kopyalamaya hazır bir ilan paketi oluştur.

    Platform: {platform} | Durum: {condition} | Ek Not: {extra_notes if extra_notes else "Yok"}

    Yanıtını tam olarak şu 6 başlıkla ver:

    ### 1. Ürün Tespiti ve Durum Analizi
    * **Tahmini Marka / Model / Tür:** (Görselden tespit edilen detaylar)
    * **Görsel Durum:** (Temizlik ve kusur kontrolü)

    ### 2. Hızlı Satış Fiyat Önerisi (TL)
    * **Hızlı Satış Fiyatı (24-48 saat):** ... TL
    * **İdeal Piyasa Fiyatı (Pazarlık paylı):** ... TL
    * **Gerekçe:** (1-2 cümle)

    ### 3. Dikkat Çekici İlan Başlığı (3 Alternatif)
    1. (Arama algoritmasına uygun başlık)
    2. (Fırsat / durum odaklı başlık)
    3. (Kısa ve net başlık)

    ### 4. İkna Edici İlan Açıklaması (Kopyala-Yapıştır)
    (Alıcıya güven veren, net ve samimi satış metni)

    ### 5. Öne Çıkan Etiketler (Hashtag)
    (8 adet platform etiketi)

    ### 6. Fotoğraf ve Satış İpucu
    (Daha hızlı satış için 1 pratik tavsiye)
    """

    yield from _stream_with_fallback([image_part, prompt])

def refine_listing_stream(current_listing: str, user_feedback: str, platform: str = "Dolap", condition: str = "Az Kullanılmış"):
    prompt = f"""
    Sen {platform} platformunda uzman bir ikinci el satış danışmanısın.
    Aşağıdaki mevcut ilanı kullanıcının isteğine göre güncelle.

    Durum: {condition}
    Mevcut İlan:
    ---
    {current_listing}
    ---

    Kullanıcı İsteği: "{user_feedback}"

    İsteği eksiksiz uygulayarak aynı 6 başlık düzeniyle (1. Ürün Tespiti ve Durum Analizi, 2. Hızlı Satış Fiyat Önerisi, 3. Dikkat Çekici İlan Başlığı, 4. İkna Edici İlan Açıklaması, 5. Öne Çıkan Etiketler, 6. Fotoğraf ve Satış İpucu) kopyalamaya hazır yeni ilanı yaz.
    """

    yield from _stream_with_fallback([prompt])