import base64
import io

import fitz  # pymupdf
from PIL import Image

import config


def extract(data: bytes) -> dict:
    """Extract text and images from PDF bytes.

    Returns {"text": str, "images": list[dict]} where images are
    base64-encoded Claude vision content blocks (up to 5).
    """
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception:
        return {"text": "", "images": []}

    text_parts = []
    images = []

    for page in doc:
        text_parts.append(page.get_text())

        if len(images) < 5:
            for img_info in page.get_images(full=True):
                if len(images) >= 5:
                    break
                xref = img_info[0]
                try:
                    base_image = doc.extract_image(xref)
                    img_bytes = base_image["image"]
                    img = Image.open(io.BytesIO(img_bytes))
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    b64 = base64.standard_b64encode(buf.getvalue()).decode()
                    images.append({
                        "type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": b64},
                    })
                except Exception:
                    pass

    full_text = "\n".join(text_parts)
    return {
        "text": full_text[: config.MAX_TEXT_CHARS],
        "images": images,
    }
