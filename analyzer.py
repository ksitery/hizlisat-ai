import base64
import io
import json
import os
import time
import urllib.request
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

GEMINI_FAST_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
]

_GROQ_VISION_CACHE: list[str] = []
_GROQ_TEXT_CACHE: list[str] = []


def _get_keys(env_names: list[str]) -> list[str]:
    keys = []
    for name in env_names:
        raw = os.getenv(name, "")
        for item in raw.split(","):
            cleaned = item.strip()
            if cleaned and cleaned not in keys:
                keys.append(cleaned)
    return keys


def _encode_image_jpeg(image: Image.Image) -> tuple[bytes, str]:
    img_copy = image.copy()
    if img_copy.mode in ("RGBA", "P", "LA"):
        img_copy = img_copy.convert("RGB")
    img_copy.thumbnail((512, 512))
    buf = io.BytesIO()
    img_copy.save(buf, format="JPEG", quality=80)
    raw_bytes = buf.getvalue()
    b64_str = base64.b64encode(raw_bytes).decode("utf-8")
    return raw_bytes, b64_str


def _get_groq_models(api_key: str, vision: bool) -> list[str]:
    global _GROQ_VISION_CACHE, _GROQ_TEXT_CACHE
    if vision and _GROQ_VISION_CACHE:
        return _GROQ_VISION_CACHE
    if not vision and _GROQ_TEXT_CACHE:
        return _GROQ_TEXT_CACHE

    if vision:
        preferred = [
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
        ]
    else:
        preferred = [
            "llama-3.3-70b-versatile",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "llama-3.1-8b-instant",
        ]

    discovered = []
    try:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "HizliSat-AI/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for m in data.get("data", []):
                mid = m.get("id", "")
                if not mid or "guard" in mid or "whisper" in mid or "tts" in mid:
                    continue
                if vision and ("llama-4" in mid or "vision" in mid):
                    if mid not in preferred and mid not in discovered:
                        discovered.append(mid)
                elif not vision and ("llama" in mid or "qwen" in mid):
                    if mid not in preferred and mid not in discovered:
                        discovered.append(mid)
    except Exception:
        pass

    result = (preferred + discovered)[:3]
    if vision:
        _GROQ_VISION_CACHE = result
    else:
        _GROQ_TEXT_CACHE = result
    return result


def _stream_groq(prompt: str, image_b64: str | None = None):
    groq_keys = _get_keys(["GROQ_API_KEYS", "GROQ_API_KEY"])
    if not groq_keys:
        raise ValueError("GROQ_API_KEY tanımlı değil.")

    errors = []
    for key in groq_keys:
        models = _get_groq_models(key, vision=(image_b64 is not None))
        for model_name in models:
            yielded = False
            try:
                if image_b64:
                    content = [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                        },
                    ]
                else:
                    content = prompt

                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": content}],
                    "temperature": 0.7,
                    "max_tokens": 900,
                    "stream": True,
                }

                req = urllib.request.Request(
                    "https://api.groq.com/openai/v1/chat/completions",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                        "User-Agent": "HizliSat-AI/1.0",
                    },
                )

                with urllib.request.urlopen(req, timeout=25) as resp:
                    for raw_line in resp:
                        line = raw_line.decode("utf-8").strip()
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        chunk = json.loads(data_str)
                        choices = chunk.get("choices") or []
                        if choices:
                            delta = choices[0].get("delta", {}).get("content")
                            if delta:
                                yielded = True
                                yield delta

                if yielded:
                    return
            except Exception as e:
                if yielded:
                    raise
                errors.append(f"Groq({model_name}): {e}")
                continue

    raise RuntimeError(" | ".join(errors))


def _stream_gemini(contents: list):
    gemini_keys = _get_keys(["GEMINI_API_KEYS", "GEMINI_API_KEY"])
    if not gemini_keys:
        raise ValueError("GEMINI_API_KEYS tanımlı değil.")

    config = types.GenerateContentConfig(
        max_output_tokens=900,
        temperature=0.7,
    )

    errors = []
    for key in gemini_keys:
        client = genai.Client(api_key=key)
        for model_name in GEMINI_FAST_MODELS:
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
                    errors.append(f"Gemini({model_name}): {err_str}")
                    if attempt == 0 and ("503" in err_str or "UNAVAILABLE" in err_str):
                        time.sleep(1)
                        continue
                    break

    raise RuntimeError(" | ".join(errors))


def _hybrid_stream(prompt: str, image: Image.Image | None = None):
    raw_bytes = None
    b64_str = None
    if image is not None:
        raw_bytes, b64_str = _encode_image_jpeg(image)

    groq_error = None
    try:
        yield from _stream_groq(prompt=prompt, image_b64=b64_str)
        return
    except Exception as e:
        groq_error = e

    try:
        if raw_bytes is not None:
            image_part = types.Part.from_bytes(data=raw_bytes, mime_type="image/jpeg")
            yield from _stream_gemini([image_part, prompt])
        else:
            yield from _stream_gemini([prompt])
    except Exception as gemini_error:
        raise RuntimeError(f"{groq_error} || {gemini_error}")


def analyze_product_stream(
    image: Image.Image,
    platform: str = "Dolap",
    condition: str = "Az Kullanılmış",
    brand_model: str = "",
    specs: str = "",
    extra_notes: str = "",
):
    brand_info = brand_model.strip() if brand_model.strip() else "Belirtilmedi (Görselden tahmin et)"
    specs_info = specs.strip() if specs.strip() else "Belirtilmedi"
    notes_info = extra_notes.strip() if extra_notes.strip() else "Yok"

    prompt = f"""
    Sen Türkiye'deki ikinci el satış platformlarında ({platform}) uzman bir e-ticaret ve fiyatlandırma danışmanısın.
    Görseli ve kullanıcının paylaştığı bilgileri birlikte değerlendirerek tamamen doğal, akıcı Türkçe ile kısa, net, kopyalamaya hazır bir ilan paketi oluştur.
    Eğer kullanıcı marka, model veya özellik belirttiyse mutlaka bu bilgileri esas al; belirtmediyse görselden tespit et.

    Platform: {platform}
    Durum: {condition}
    Marka / Model: {brand_info}
    Beden / Ölçü / Teknik Özellik: {specs_info}
    Ek Not / Kusur Durumu: {notes_info}

    Yanıtını tam olarak şu 6 başlıkla ver:

    ### 1. Ürün Tespiti ve Durum Analizi
    * **Marka / Model / Tür:** (Kullanıcının belirttiği ve görselden tespit edilen detaylar)
    * **Görsel Durum ve Özellikler:** (Temizlik, kusur kontrolü ve teknik/beden özeti)

    ### 2. Hızlı Satış Fiyat Önerisi (TL)
    * **Hızlı Satış Fiyatı (24-48 saat):** ... TL
    * **İdeal Piyasa Fiyatı (Pazarlık paylı):** ... TL
    * **Gerekçe:** (1-2 cümle)

    ### 3. Dikkat Çekici İlan Başlığı (3 Alternatif)
    1. (Arama algoritmasına uygun, marka ve özellik odaklı başlık)
    2. (Fırsat / durum odaklı başlık)
    3. (Kısa ve net başlık)