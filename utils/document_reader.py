from PIL import Image
import fitz
import pytesseract
import io

def read_uploaded_file(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()
    if name.endswith('.txt'):
        return raw.decode('utf-8', errors='ignore')
    if name.endswith('.pdf'):
        text = ""
        with fitz.open(stream=raw, filetype='pdf') as pdf:
            for page in pdf:
                text += page.get_text() + "\n"
        if text.strip(): return text
        try: return pytesseract.image_to_string(Image.open(io.BytesIO(raw)))
        except Exception: return ""
    if name.endswith(('.png', '.jpg', '.jpeg')):
        try: return pytesseract.image_to_string(Image.open(io.BytesIO(raw)))
        except Exception as exc: return f"OCR_ERROR: {exc}"
    return ""
