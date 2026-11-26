import os
import time
from dotenv import load_dotenv
from google import genai
from PIL import Image

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_active_models() -> list[str]:
    preferred = ["gemini-3.8-flash"]
    discovered = []
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "gemini" in name and ("flash" in name or "pro" in name):
                if not any(x in name for x in ["image", "audio", "tts", "live", "embedding", "veo", "imagen", "robotics", "2.0", "2.5"]):
                    if name not in preferred and name not in discovered:
                        discovered.append(name)
    except Exception:
        pass
    return (preferred + discovered)[:4]

def analyze_product(image: Image.Image, platform: str = "Dolap", condition: str = "Az Kullanılmış", extra_notes: str = "") -> str:
    img_copy = image.copy()
    img_copy.thumbnail((1024, 1024))

    prompt = f"""
    Sen Türkiye'deki ikinci el satış platformlarında (Dolap, Gardrops, Sahibinden, Letgo) uzmanlaşmış bir e-ticaret ve fiyatlandırma danışmanısın.
    Yüklenen ürün fotoğrafını detaylıca incele ve aşağıdaki bilgilere göre satıcının ürünü en hızlı ve kârlı şekilde satmasını sağlayacak bir ilan paketi oluştur.

    Satıcının Seçtiği Platform: {platform}
    Ürünün Durumu: {condition}
    Satıcının Ek Notu: {extra_notes if extra_notes else "Yok"}

    Lütfen yanıtını tam olarak şu başlıklarla, net ve kopyalamaya hazır formatta ver:

    ### 1. Ürün Tespiti ve Durum Analizi
    * **Tahmini Marka / Model / Tür:** (Fotoğraftan tespit edebildiğin detaylar)
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

    errors = []
    for model_name in get_active_models():
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[img_copy, prompt]
                )
                return response.text
            except Exception as e:
                errors.append(f"{model_name}: {e}")
                if attempt == 0 and ("503" in str(e) or "UNAVAILABLE" in str(e)):
                    time.sleep(2)
                    continue
                break

    raise RuntimeError(" | ".join(errors))