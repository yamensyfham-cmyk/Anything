"""
أدوات PDF والمستندات — 25 ميزة
pip install pypdf2 reportlab
"""
import os, sys, json, re
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

try:
    import PyPDF2
    _PDF = True
except ImportError:
    try:
        import pypdf as PyPDF2
        _PDF = True
    except ImportError:
        _PDF = False

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.pdfgen        import canvas
    from reportlab.lib.styles    import getSampleStyleSheet
    from reportlab.platypus      import SimpleDocTemplate, Paragraph, Spacer, Table
    from reportlab.lib           import colors
    _RL = True
except ImportError:
    _RL = False

class PDFTools:

    @staticmethod
    def info(path: str) -> dict:
        if not _PDF: return {"error":"pip install pypdf2"}
        try:
            with open(path,'rb') as f:
                r   = PyPDF2.PdfReader(f)
                meta = r.metadata or {}
                return {
                    "الصفحات":  len(r.pages),
                    "العنوان":  meta.get("/Title",""),
                    "المؤلف":  meta.get("/Author",""),
                    "الموضوع": meta.get("/Subject",""),
                    "مشفر":    r.is_encrypted,
                }
        except Exception as e: return {"error":str(e)}

    @staticmethod
    def extract_text(path: str, pages=None) -> str:
        if not _PDF: return "❌ pip install pypdf2"
        try:
            with open(path,'rb') as f:
                r    = PyPDF2.PdfReader(f)
                text = ""
                target = pages or range(len(r.pages))
                for i in target:
                    text += r.pages[i].extract_text() + "\n"
            return text
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def extract_all_text(path: str, out: str = None) -> str:
        text = PDFTools.extract_text(path)
        out  = out or path.replace(".pdf",".txt")
        with open(out,'w',encoding='utf-8') as f: f.write(text)
        return f"✅ {out} ({len(text)} حرف)"

    @staticmethod
    def merge(paths: list, out: str) -> str:
        if not _PDF: return "❌ pip install pypdf2"
        try:
            writer = PyPDF2.PdfWriter()
            for path in paths:
                with open(path,'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        writer.add_page(page)
            with open(out,'wb') as f: writer.write(f)
            return f"✅ {out} ({len(paths)} ملف)"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def split(path: str, out_dir=".") -> str:
        if not _PDF: return "❌ pip install pypdf2"
        os.makedirs(out_dir, exist_ok=True)
        try:
            with open(path,'rb') as f:
                r = PyPDF2.PdfReader(f)
                for i, page in enumerate(r.pages):
                    w = PyPDF2.PdfWriter()
                    w.add_page(page)
                    out = os.path.join(out_dir, f"page_{i+1:03d}.pdf")
                    with open(out,'wb') as fo: w.write(fo)
            return f"✅ {len(r.pages)} صفحة → {out_dir}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def extract_pages(path: str, pages: list, out: str) -> str:
        if not _PDF: return "❌ pip install pypdf2"
        try:
            with open(path,'rb') as f:
                r = PyPDF2.PdfReader(f)
                w = PyPDF2.PdfWriter()
                for i in pages:
                    if 0 <= i < len(r.pages): w.add_page(r.pages[i])
            with open(out,'wb') as f: w.write(f)
            return f"✅ {out}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def rotate_pages(path: str, degrees=90, out=None) -> str:
        if not _PDF: return "❌ pip install pypdf2"
        out = out or path
        try:
            with open(path,'rb') as f:
                r = PyPDF2.PdfReader(f)
                w = PyPDF2.PdfWriter()
                for page in r.pages:
                    page.rotate(degrees)
                    w.add_page(page)
            with open(out,'wb') as f: w.write(f)
            return f"✅ {out} (مُدار {degrees}°)"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def encrypt(path: str, password: str, out=None) -> str:
        if not _PDF: return "❌ pip install pypdf2"
        out = out or path.replace(".pdf","_enc.pdf")
        try:
            with open(path,'rb') as f:
                r = PyPDF2.PdfReader(f)
                w = PyPDF2.PdfWriter()
                for page in r.pages: w.add_page(page)
                w.encrypt(password)
            with open(out,'wb') as f: w.write(f)
            return f"✅ مشفر: {out}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def decrypt(path: str, password: str, out=None) -> str:
        if not _PDF: return "❌ pip install pypdf2"
        out = out or path.replace(".pdf","_dec.pdf")
        try:
            with open(path,'rb') as f:
                r = PyPDF2.PdfReader(f)
                if r.is_encrypted: r.decrypt(password)
                w = PyPDF2.PdfWriter()
                for page in r.pages: w.add_page(page)
            with open(out,'wb') as f: w.write(f)
            return f"✅ فُك التشفير: {out}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def crack_pdf(path: str, wordlist_path: str) -> str:
        """محاولة كسر كلمة مرور PDF"""
        if not _PDF: return "❌ pip install pypdf2"
        if not os.path.exists(wordlist_path): return "❌ قائمة الكلمات غير موجودة"
        try:
            with open(path,'rb') as f:
                r = PyPDF2.PdfReader(f)
                if not r.is_encrypted: return "الملف غير مشفر."
                with open(wordlist_path, errors='ignore') as wl:
                    for line in wl:
                        pwd = line.strip()
                        try:
                            if r.decrypt(pwd): return f"✅ كلمة المرور: {pwd}"
                        except Exception: pass
            return "❌ لم يُعثر"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def create_simple(content: str, out="output.pdf", title="") -> str:
        if not _RL: return "❌ pip install reportlab"
        try:
            c = canvas.Canvas(out, pagesize=A4)
            width, height = A4
            c.setFont("Helvetica-Bold", 16)
            if title: c.drawString(50, height-50, title)
            c.setFont("Helvetica", 11)
            y = height - 90
            for line in content.split('\n'):
                if y < 50: c.showPage(); y = height - 50
                c.drawString(50, y, line[:100])
                y -= 18
            c.save()
            return f"✅ {out}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def create_report(data: dict, out="report.pdf") -> str:
        """إنشاء تقرير PDF"""
        if not _RL: return "❌ pip install reportlab"
        try:
            doc    = SimpleDocTemplate(out, pagesize=A4)
            styles = getSampleStyleSheet()
            story  = []
            story.append(Paragraph(data.get("title","تقرير"), styles['Title']))
            story.append(Spacer(1,12))
            for key, value in data.items():
                if key != "title":
                    story.append(Paragraph(f"<b>{key}:</b> {value}", styles['Normal']))
                    story.append(Spacer(1,6))
            doc.build(story)
            return f"✅ {out}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def create_table_pdf(headers: list, rows: list, out="table.pdf") -> str:
        if not _RL: return "❌ pip install reportlab"
        try:
            doc   = SimpleDocTemplate(out, pagesize=A4)
            data  = [headers] + rows
            table = Table(data)
            table.setStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.grey),
                ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                ('GRID',(0,0),(-1,-1),0.5,colors.black),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.lightgrey]),
            ])
            doc.build([table])
            return f"✅ {out}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def add_watermark_text(path: str, text: str, out=None) -> str:
        if not _RL or not _PDF: return "❌ pip install reportlab pypdf2"
        import io
        out = out or path.replace(".pdf","_wm.pdf")
        try:

            pkt  = io.BytesIO()
            c    = canvas.Canvas(pkt, pagesize=A4)
            c.setFillColorRGB(0.5,0.5,0.5,alpha=0.3)
            c.setFont("Helvetica-Bold", 50)
            c.saveState()
            c.translate(300, 420)
            c.rotate(45)
            c.drawCentredString(0, 0, text)
            c.restoreState()
            c.save()
            pkt.seek(0)
            wm_reader = PyPDF2.PdfReader(pkt)
            wm_page   = wm_reader.pages[0]
            with open(path,'rb') as f:
                reader = PyPDF2.PdfReader(f)
                writer = PyPDF2.PdfWriter()
                for page in reader.pages:
                    page.merge_page(wm_page)
                    writer.add_page(page)
            with open(out,'wb') as f: writer.write(f)
            return f"✅ {out}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def search_in_pdf(path: str, keyword: str) -> list:
        if not _PDF: return ["❌ pip install pypdf2"]
        try:
            with open(path,'rb') as f:
                r = PyPDF2.PdfReader(f)
                results = []
                for i, page in enumerate(r.pages):
                    text = page.extract_text()
                    if keyword.lower() in text.lower():
                        idx = text.lower().find(keyword.lower())
                        snippet = text[max(0,idx-50):idx+100]
                        results.append({"صفحة":i+1,"نص":snippet})
            return results
        except Exception as e: return [{"error":str(e)}]

    @staticmethod
    def compress_pdf(path: str, out=None) -> str:
        """ضغط PDF عبر إعادة الكتابة"""
        if not _PDF: return "❌ pip install pypdf2"
        out = out or path.replace(".pdf","_compressed.pdf")
        try:
            with open(path,'rb') as f:
                r = PyPDF2.PdfReader(f)
                w = PyPDF2.PdfWriter()
                for page in r.pages:
                    page.compress_content_streams()
                    w.add_page(page)
            with open(out,'wb') as f: w.write(f)
            b = os.path.getsize(path); a = os.path.getsize(out)
            return f"✅ {b//1024}KB → {a//1024}KB (وفّر {(b-a)//1024}KB)"
        except Exception as e: return f"❌ {e}"

if __name__ == "__main__":
    pt = PDFTools()
    menu = {
        "1":  ("معلومات PDF",            lambda: print(json.dumps(pt.info(input("المسار => ")), indent=2, ensure_ascii=False))),
        "2":  ("استخراج النص",           lambda: print(pt.extract_text(input("المسار => "))[:1000])),
        "3":  ("حفظ النص كـ .txt",        lambda: print(pt.extract_all_text(input("المسار => ")))),
        "4":  ("دمج PDFs",               lambda: print(pt.merge(input("المسارات (مسافة) => ").split(), input("الإخراج => ")))),
        "5":  ("تقسيم لصفحات",           lambda: print(pt.split(input("المسار => "), input("المجلد (.) => ") or "."))),
        "6":  ("استخراج صفحات معينة",    lambda: print(pt.extract_pages(input("المسار => "), [int(x)-1 for x in input("أرقام الصفحات (مسافة) => ").split()], input("الإخراج => ")))),
        "7":  ("تدوير الصفحات",          lambda: print(pt.rotate_pages(input("المسار => "), int(input("الزاوية (90) => ") or 90)))),
        "8":  ("تشفير PDF",              lambda: print(pt.encrypt(input("المسار => "), input("كلمة المرور => ")))),
        "9":  ("فك تشفير PDF",           lambda: print(pt.decrypt(input("المسار => "), input("كلمة المرور => ")))),
        "10": ("كسر كلمة مرور PDF",      lambda: print(pt.crack_pdf(input("المسار => "), input("قائمة الكلمات => ")))),
        "11": ("بحث في PDF",             lambda: [print(f"  صفحة {r['صفحة']}: {r['نص'][:80]}") for r in pt.search_in_pdf(input("المسار => "), input("الكلمة => "))]),
        "12": ("علامة مائية",            lambda: print(pt.add_watermark_text(input("المسار => "), input("النص => ")))),
        "13": ("ضغط PDF",                lambda: print(pt.compress_pdf(input("المسار => ")))),
        "14": ("إنشاء PDF من نص",         lambda: print(pt.create_simple(input("النص (أسطر متعددة، Enter مرتين للإنهاء):\n"), input("الإخراج => ") or "output.pdf", input("العنوان => ")))),
    }
    while True:
        print("\n═"*45)
        print("  📄  PDF Tools — 14 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
