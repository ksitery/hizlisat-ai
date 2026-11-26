import os
import time
from dotenv import load_dotenv
from google import genai
from PIL import Image

load_dotenv()

def _get_api_keys() -> list[str]:
    raw_keys = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY", "")
    return [k.strip() for k in raw_keys.split(",") if k.strip()]

def _get_models_for_client(client: genai.Client) -> list[str]:
    preferred = [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-3.8-flash",
    ]
    discovered = []
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "gemini" in name and ("flash" in name or "pro" in name):
                if not any(x in name for x in ["image", "audio", "tts", "live", "embedding", "veo", "imagen", "robotics", "2.0"]):
                    if name not in preferred and name not in discovered:
                        discovered.append(name)
    except Exception:
        pass
    return (preferred + discovered)[:4]

_CACHED_MODELS: list[str] = []

def _generate_with_fallback(contents: list) -> str:
    global _CACHED_MODELS
    api_keys = _get_api_keys()
    if not api_keys:
        raise ValueError("API anahtarı bulunamadı. Lütfen GEMINI_API_KEY ayarını kontrol edin.")

    errors = []
    for key in api_keys:
        client = genai.Client(api_key=key)
        if not _CACHED_MODELS:
            _CACHED_MODELS = _get_models_for_client(client)

        for model_name in _CACHED_MODELS:
            for attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents
                    )
                    return response.text
                except Exception as e:
                    err_str = str(e)
                    errors.append(f"{model_name}: {err_str}")
                    if attempt == 0 and ("503" in err_str or "UNAVAILABLE" in err_str):
                        time.sleep(1.5)
                        continue
                    break

    raise RuntimeError(" | ".join(errors))

def analyze_product(image: Image.Image, platform: str = "Dolap", condition: str = "Az Kullanılmış", extra_notes: str = "") -> str:
    img_copy = image.copy()
    img_copy.thumbnail((768, 768))

    prompt = f"""
    Sen Türkiye'deki ikinci el satış platformlarında ({platform}) uzmanlaşmış bir e-ticaret ve fiyatlandırma danışmanısın.
    Yüklenen ürün fotoğrafını incele ve satıcının ürünü en hızlı ve kârlı şekilde satmasını sağlayacak ilan paketini oluştur.

    Satıcının Seçtiği Platform: {platform}
    Ürünün Durumu: {condition}
    Satıcının Ek Notu: {extra_notes if extra_notes else "Yok"}

    Yanıtını tam olarak şu başlıklarla, net ve kopyalamaya hazır formatta ver:

    ### 1. Ürün Tespiti ve Durum Analizi
    * **Tahmini Marka / Model / Tür:** (Fotoğraftan tespit edilen detaylar)
    * **Görsel Durum ve Kusur Kontrolü:** (Yıpranma, leke, çizik veya temizlik durumu)

    ### 2. Hızlı Satış Fiyat Önerisi (TL)
    * **Hızlı Satış Fiyatı (24-48 saat içinde gider):** ... TL
    * **İdeal Piyasa Fiyatı (Pazarlık paylı liste fiyatı):** ... TL
    * **Fiyatlandırma Gerekçesi:** (Kısa açıklama)

    ### 3. Dikkat Çekici İlan Başlığı (3 Alternatif)
    1. (Arama algoritmasına uygun, marka ve özellik odaklı başlık)
    2. (Fırsat / durum odaklı başlık)
    3. (Kısa ve net başlık)

    ### 4. İkna Edici İlan Açıklaması (Kopyala-Yapıştır)
    (Alıcının aklındaki soruları yanıtlayan, güven veren, samimi ve profesyonel satış metni)

    ### 5. Öne Çıkan Etiketler (Hashtag)
    (Platform aramalarında üst sıralara çıkaracak 8-10 adet etiket)

    ### 6. Fotoğraf ve Satış İpucu
    (Bu ürünün daha hızlı satılması için fotoğraf açısı veya ilan ayarıyla ilgili 1 pratik tavsiye)
    """

    return _generate_with_fallback([img_copy, prompt])

def refine_listing(current_listing: str, user_feedback: str, platform: str = "Dolap", condition: str = "Az Kullanılmış") -> str:
    prompt = f"""
    Sen Türkiye'deki ikinci el satış platformlarında ({platform}) uzmanlaşmış bir e-ticaret ve fiyatlandırma danışmanısın.
    Aşağıda daha önce hazırladığın ürün ilanı yer alıyor. Kullanıcı bu ilanı kendi fikrine ve isteğine göre güncellemeni istiyor.

    Ürünün Durumu: {condition}
    Mevcut İlan:
    ---
    {current_listing}
    ---

    Kullanıcının Değişiklik İsteği / Fikri:
    "{user_feedback}"

    Lütfen kullanıcının istediği değişiklikleri eksiksiz uygulayarak ilanı aynı 6 başlık düzeniyle (1. Ürün Tespiti ve Durum Analizi, 2. Hızlı Satış Fiyat Önerisi, 3. Dikkat Çekici İlan Başlığı, 4. İkna Edici İlan Açıklaması, 5. Öne Çıkan Etiketler, 6. Fotoğraf ve Satış İpucu) kopyalamaya hazır şekilde yeniden oluştur.
    """

    return _generate_with_fallback([prompt])