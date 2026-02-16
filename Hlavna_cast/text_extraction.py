from pypdf import PdfReader
import fitz
import easyocr
import numpy as np
import cv2

ZNAKY = "ˇ´`^~˝˚’'"
reader_ocr = easyocr.Reader(['sk', 'en'], gpu=False)

def pdf_to_text(pdf_cesta: str):
    reader_pdf = PdfReader(pdf_cesta)
    doc_fitz = fitz.open(pdf_cesta)

    segmenty = []

    for i, page in enumerate(reader_pdf.pages, start=1):
        text = page.extract_text() or ""
        text = text.translate(str.maketrans("", "", ZNAKY)).strip()

        blok = f"Strana {i}\n{text}"

        page_fitz = doc_fitz[i - 1]
        images = page_fitz.get_images(full=True)

        for idx, img_info in enumerate(images, start=1):
            xref = img_info[0]
            base_image = doc_fitz.extract_image(xref)
            img_bytes = base_image["image"]

            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            result = reader_ocr.readtext(img, detail=0, paragraph=True)
            ocr_text = "\n".join(result).strip()

            if ocr_text:
                blok += f"\n\n[OCR OBRÁZOK {idx}]\n{ocr_text}"

        segmenty.append(
            {
                "page": i,
                "text": blok,
            }
        )


    return segmenty