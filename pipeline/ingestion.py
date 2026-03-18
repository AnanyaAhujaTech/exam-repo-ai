import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from docx import Document
import os


# ================= PDF EXTRACTION =================

def extract_text_pymupdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)

    for page in doc:
        text += page.get_text()

    return text.strip()


def extract_text_ocr(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)

    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text += pytesseract.image_to_string(img)

    return text.strip()


# ================= DOCX EXTRACTION =================

def extract_text_docx(docx_path):
    doc = Document(docx_path)
    text = []

    for para in doc.paragraphs:
        if para.text.strip():
            text.append(para.text.strip())

    return "\n".join(text)


# ================= MAIN INGESTION =================

def extract_text(file_path):

    file_name = os.path.basename(file_path)
    ext = file_name.lower().split(".")[-1]

    if ext == "pdf":

        text = extract_text_pymupdf(file_path)

        # fallback to OCR
        if len(text) < 200:
            text = extract_text_ocr(file_path)
            method = "ocr"
        else:
            method = "pymupdf"

    elif ext == "docx":

        text = extract_text_docx(file_path)
        method = "docx"

    else:
        raise ValueError("Unsupported file type")

    return {
        "file_name": file_name,
        "file_type": ext,
        "raw_text": text,
        "extraction_method": method
    }
