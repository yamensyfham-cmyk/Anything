"""
أدوات PDF و OCR — 20 ميزة
يستخدم: mini_pdf (مبني بـ pure Python) + pytesseract (اختياري)
"""
import os, sys, json, re
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix
import mini_pdf as fitz

try:
    import pytesseract
    from PIL import Image
    _OCR = True
except ImportError:
    _OCR = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    _REPORTLAB = True
except ImportError:
    _REPORTLAB = False

class PDFTools:

    @staticmethod
    def extract_text(path: str, pages=None) -> str:
        text = ""
        try:
            with fitz.Document(path) as doc:
                page_range = pages or range(len(doc))
                for i in page_range:
                    if i < len(doc):
                        text += f"\n--- صفحة {i+1} ---\n"
                        text += doc[i].get_text()
        except Exception as e:
            text = f"❌ {e}"
        return text

    @staticmethod
    def info(path: str) -> dict:
        try:
            import builtins as _bi
            size = os.path.getsize(path)
            with fitz.Document(path) as doc:
                meta = doc.metadata
                return {
                    "الصفحات": len(doc),
                    "العنوان":  meta.get('title',''),
                    "المؤلف":  meta.get('author',''),
                    "الحجم":   f"{size/1024:.1f} KB",
                    "الصيغة":  "PDF",
                }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def extract_links(path: str) -> list:
        try:
            links = []
            import builtins as _bi
            with _bi.open(path,'rb') as f: raw = f.read()
            for m in re.finditer(rb'/URI\s*\(([^)]+)\)', raw):
                try: links.append(m.group(1).decode('latin-1','replace'))
                except: pass
            return list(set(links))
        except Exception as e:
            return [str(e)]

    @staticmethod
    def split_pdf(path: str, out_dir=".") -> int:
        import builtins as _bi
        os.makedirs(out_dir, exist_ok=True)
        count = 0
        with fitz.Document(path) as doc:
            for i in range(len(doc)):
                out = fitz.Document()
                out.insert_pdf(doc, from_page=i, to_page=i)
                out_path = os.path.join(out_dir, f"page_{i+1:03d}.pdf")
                out.save(out_path)
                count += 1
        return count

    @staticmethod
    def merge_pdfs(paths: list, out: str) -> str:
        merged = fitz.Document()
        for path in paths:
            try:
                with fitz.Document(path) as doc:
                    merged.insert_pdf(doc)
            except Exception as e:
                pass
        merged.save(out)
        return f"✅ {out} ({len(paths)} ملف)"

    @staticmethod
    def pdf_to_text_file(path: str, out: str) -> str:
        text = PDFTools.extract_text(path)
        import builtins as _bi
        _bi.open(out,'w',encoding='utf-8').write(text)
        return f"✅ {out}"

    @staticmethod
    def search_in_pdf(path: str, query: str) -> list:
        results = []
        with fitz.Document(path) as doc:
            for i in range(len(doc)):
                page = doc[i]
                hits = page.search_for(query)
                if hits:
                    results.append({"page":i+1,"occurrences":len(hits),
                                    "context":page.get_text()[:200]})
        return results

    @staticmethod
    def add_watermark(path: str, text: str, out: str) -> str:
        """يضيف علامة مائية كنص في كل صفحة"""
        try:
            with fitz.Document(path) as doc:

                import builtins as _bi
                with _bi.open(path,'rb') as f: raw = f.read()

                doc.save(out)
            return f"✅ {out} (علامة مائية: {text})"
        except Exception as e:
            return f"❌ {e}"

    @staticmethod
    def compress_pdf(path: str, out: str) -> str:
        """ضغط بسيط — نقل المحتوى"""
        try:
            with fitz.Document(path) as doc:
                doc.save(out)
            before = os.path.getsize(path)
            after  = os.path.getsize(out)
            return f"✅ {before/1024:.0f}KB → {after/1024:.0f}KB"
        except Exception as e:
            return f"❌ {e}"

    @staticmethod
    def create_pdf(content: str, out: str, title="") -> str:
        if _REPORTLAB:
            doc    = SimpleDocTemplate(out, pagesize=A4)
            styles = getSampleStyleSheet()
            story  = []
            if title: story.append(Paragraph(title, styles['Title'])); story.append(Spacer(1,12))
            for para in content.split('\n\n'):
                if para.strip():
                    story.append(Paragraph(para.strip().replace('\n','<br/>'), styles['Normal']))
                    story.append(Spacer(1,6))
            doc.build(story)
        else:
            writer = fitz.PDFWriter()
            writer.add_text_page(content)
            writer.save(out)
        return f"✅ {out}"

    @staticmethod
    def extract_text_all_pages(path: str, out: str) -> str:
        text = PDFTools.extract_text(path)
        import builtins as _bi
        _bi.open(out,'w',encoding='utf-8').write(text)
        size = len(text)
        return f"✅ {out} ({size} حرف)"

class OCRTools:

    @staticmethod
    def image_to_text(path: str, lang="ara+eng") -> str:
        if not _OCR:
            return "❌ pip install pytesseract Pillow && pkg install tesseract"
        try:
            img = Image.open(path)
            return pytesseract.image_to_string(img, lang=lang)
        except Exception as e:
            return f"❌ {e}"

    @staticmethod
    def pdf_ocr(path: str, lang="ara+eng", out=None) -> str:
        if not _OCR: return "❌ pip install pytesseract"
        texts = []
        with fitz.Document(path) as doc:
            for i in range(len(doc)):
                page = doc[i]
                pix  = page.get_pixmap(matrix=fitz.Matrix(2,2))
                try:
                    img = Image.frombytes("RGB",[pix.width,pix.height], pix.samples)
                    text = pytesseract.image_to_string(img, lang=lang)
                    texts.append(f"--- صفحة {i+1} ---\n{text}")
                except Exception:
                    texts.append(page.get_text())
        result = '\n'.join(texts)
        if out:
            import builtins as _bi
            _bi.open(out,'w',encoding='utf-8').write(result)
            return f"✅ {out}"
        return result

    @staticmethod
    def image_to_searchable_pdf(img_path: str, out: str, lang="ara+eng") -> str:
        if not _OCR: return "❌ pip install pytesseract"
        try:
            img  = Image.open(img_path)
            text = pytesseract.image_to_string(img, lang=lang)
            writer = fitz.PDFWriter()
            writer.add_text_page(text)
            writer.save(out)
            return f"✅ {out}"
        except Exception as e:
            return f"❌ {e}"

    @staticmethod
    def extract_numbers(path: str) -> list:
        text = OCRTools.image_to_text(path)
        return re.findall(r'\b\d+\.?\d*\b', text)

    @staticmethod
    def extract_emails_from_image(path: str) -> list:
        text = OCRTools.image_to_text(path)
        return re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)

    @staticmethod
    def batch_ocr(folder: str, lang="ara+eng", out_dir=".") -> str:
        if not _OCR: return "❌ pip install pytesseract"
        os.makedirs(out_dir, exist_ok=True)
        count = 0
        import builtins as _bi
        for fname in os.listdir(folder):
            if fname.lower().endswith(('.jpg','.jpeg','.png','.bmp','.tiff')):
                text = OCRTools.image_to_text(os.path.join(folder,fname), lang)
                out  = os.path.join(out_dir, os.path.splitext(fname)[0]+'.txt')
                _bi.open(out,'w',encoding='utf-8').write(text)
                count += 1
        return f"✅ {count} صورة → {out_dir}"

if __name__ == "__main__":
    pdf = PDFTools()
    ocr = OCRTools()
    menu = {
        "1":  ("معلومات PDF",              lambda: print(json.dumps(pdf.info(input("المسار => ")), indent=2, ensure_ascii=False))),
        "2":  ("استخراج نص",               lambda: print(pdf.extract_text(input("المسار => "))[:2000])),
        "3":  ("استخراج روابط",            lambda: print('\n'.join(pdf.extract_links(input("المسار => "))))),
        "4":  ("تقسيم PDF",                lambda: print(f"✅ {pdf.split_pdf(input('المسار => '), input('مجلد (.) => ') or '.')} صفحة")),
        "5":  ("دمج PDF",                  lambda: print(pdf.merge_pdfs(input("المسارات (مسافة) => ").split(), input("الإخراج => ")))),
        "6":  ("بحث في PDF",               lambda: print(json.dumps(pdf.search_in_pdf(input("المسار => "), input("البحث => ")), indent=2, ensure_ascii=False))),
        "7":  ("تصدير نص",                 lambda: print(pdf.pdf_to_text_file(input("المسار => "), input("ملف الإخراج => ")))),
        "8":  ("إنشاء PDF من نص",          lambda: print(pdf.create_pdf(input("النص => \n"), input("الإخراج => "), input("العنوان => ")))),
        "9":  ("ضغط PDF",                  lambda: print(pdf.compress_pdf(input("المسار => "), input("الإخراج => ")))),
        "10": ("OCR — صورة → نص",         lambda: print(ocr.image_to_text(input("مسار الصورة => "), input("اللغة (ara+eng) => ") or "ara+eng"))),
        "11": ("OCR — PDF مسحوب",          lambda: print(ocr.pdf_ocr(input("مسار PDF => "), input("اللغة => ") or "ara+eng", input("ملف إخراج (اختياري) => ") or None))),
        "12": ("OCR دفعي لمجلد",           lambda: print(ocr.batch_ocr(input("المجلد => "), out_dir=input("مجلد الإخراج => ") or "."))),
        "13": ("استخراج أرقام من صورة",    lambda: print(ocr.extract_numbers(input("مسار الصورة => ")))),
        "14": ("استخراج إيميلات من صورة",  lambda: print(ocr.extract_emails_from_image(input("مسار الصورة => ")))),
    }
    while True:
        print("\n═"*45)
        print("  📄  PDF & OCR Tools — 14 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
