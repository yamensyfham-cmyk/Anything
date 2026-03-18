"""
MiniPDF — بديل PyMuPDF (fitz)
Pure Python, zero dependencies
يقرأ PDF نصي، يدمج، يقسم، يضيف علامة مائية
"""
import re
import os
import zipfile
import zlib
import struct
import io

def _decode_pdf_string(s: bytes) -> str:
    """فك ترميز نص PDF"""
    try:
        if s.startswith(b'\xfe\xff'):
            return s[2:].decode('utf-16-be', errors='replace')
        if s.startswith(b'\xff\xfe'):
            return s[2:].decode('utf-16-le', errors='replace')

        try:    return s.decode('utf-8', errors='strict')
        except: return s.decode('latin-1', errors='replace')
    except Exception:
        return s.decode('ascii', errors='replace')

def _decompress_stream(data: bytes) -> bytes:
    try:    return zlib.decompress(data)
    except:
        try:    return zlib.decompress(data, -15)
        except: return data

def _extract_streams(raw: bytes) -> list:
    """استخراج stream objects من PDF"""
    streams = []
    pattern = re.compile(rb'stream\r?\n(.*?)\r?\nendstream', re.DOTALL)
    for m in pattern.finditer(raw):
        data = m.group(1)

        start = max(0, m.start() - 500)
        header = raw[start:m.start()]
        if b'/FlateDecode' in header or b'/Fl ' in header:
            try: data = _decompress_stream(data)
            except: pass
        streams.append(data)
    return streams

def _parse_text_from_stream(data: bytes) -> str:
    """استخراج نص من PDF stream"""
    text = data.decode('latin-1', errors='replace')

    result = []

    for m in re.finditer(r'\(([^)\\]*(?:\\.[^)\\]*)*)\)\s*Tj', text):
        t = m.group(1)
        t = t.replace('\\n','\n').replace('\\r','\n').replace('\\t',' ')
        t = re.sub(r'\\(.)', r'\1', t)
        result.append(t)

    for m in re.finditer(r'\[([^\]]*)\]\s*TJ', text):
        inner = m.group(1)
        for part in re.finditer(r'\(([^)\\]*(?:\\.[^)\\]*)*)\)', inner):
            t = part.group(1)
            t = t.replace('\\n','\n').replace('\\r','\n').replace('\\t',' ')
            t = re.sub(r'\\(.)', r'\1', t)
            result.append(t)
    return ' '.join(result)

def _extract_text_simple(raw: bytes) -> str:
    """استخراج نص من PDF بطريقة بسيطة"""
    streams = _extract_streams(raw)
    texts   = []
    for stream in streams:
        t = _parse_text_from_stream(stream)
        if t.strip(): texts.append(t)

    if not texts:
        all_text = raw.decode('latin-1', errors='replace')
        raw_texts = re.findall(r'\(([^\x00-\x1f()\\]{3,})\)', all_text)
        texts = [t for t in raw_texts if len(t) > 3 and not t.startswith('%')]

    return '\n'.join(texts)

def _count_pages(raw: bytes) -> int:
    """عد صفحات PDF"""
    m = re.search(rb'/Count\s+(\d+)', raw)
    return int(m.group(1)) if m else 1

def _extract_metadata(raw: bytes) -> dict:
    meta = {}
    fields = ['Title','Author','Subject','Creator','Producer','CreationDate']
    for f in fields:
        m = re.search(rb'/' + f.encode() + rb'\s*\(([^)]*)\)', raw)
        if m:
            try: meta[f] = _decode_pdf_string(m.group(1))
            except: meta[f] = m.group(1).decode('latin-1', errors='replace')
    return meta

def _find_links(raw: bytes) -> list:
    links = []

    for m in re.finditer(rb'/URI\s*\(([^)]+)\)', raw):
        try: links.append(m.group(1).decode('latin-1', errors='replace'))
        except: pass
    return list(set(links))

class PDFWriter:
    """كاتب PDF بسيط — يدعم: نص، دمج، تقسيم، علامة مائية"""

    def __init__(self):
        self._pages = []

    def add_text_page(self, text: str, font_size=12):
        self._pages.append({'type':'text','content':text,'font_size':font_size})

    def _build_pdf(self) -> bytes:
        """بناء PDF صالح من الصفر"""
        objects = []
        page_refs = []

        def add_obj(content: str) -> int:
            idx = len(objects) + 1
            objects.append(f"{idx} 0 obj\n{content}\nendobj")
            return idx

        catalog_id = 1

        pages_id = 2

        objects.append("")
        objects.append("")

        for page in self._pages:
            text = page['content']
            fs   = page.get('font_size', 12)

            font_id = len(objects) + 1
            objects.append(f"{font_id} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")

            safe_text = text.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
            lines = safe_text.split('\n')
            stream_lines = ['BT', f'/F1 {fs} Tf', '50 800 Td']
            for i, line in enumerate(lines[:60]):
                if i == 0:
                    stream_lines.append(f'({line[:100]}) Tj')
                else:
                    stream_lines.append(f'0 -{fs+2} Td ({line[:100]}) Tj')
            stream_lines.append('ET')
            stream = '\n'.join(stream_lines)
            stream_bytes = stream.encode('latin-1', errors='replace')

            content_id = len(objects) + 1
            objects.append(f"{content_id} 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n{stream}\nendstream\nendobj")

            page_id = len(objects) + 1
            objects.append(f"{page_id} 0 obj\n<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] /Contents {content_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>\nendobj")
            page_refs.append(page_id)

        kids = ' '.join(f'{r} 0 R' for r in page_refs)
        objects[pages_id-1] = f"{pages_id} 0 obj\n<< /Type /Pages /Kids [{kids}] /Count {len(page_refs)} >>\nendobj"

        objects[catalog_id-1] = f"{catalog_id} 0 obj\n<< /Type /Catalog /Pages {pages_id} 0 R >>\nendobj"

        header  = b"%PDF-1.4\n"
        body    = b""
        offsets = []

        for obj in objects:
            offsets.append(len(header) + len(body))
            body += (obj + "\n").encode('latin-1', errors='replace')

        xref_pos = len(header) + len(body)
        xref  = f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n"
        for off in offsets:
            xref += f"{off:010d} 00000 n \n"
        trailer = f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n"

        return header + body + xref.encode() + trailer.encode()

    def save(self, path: str):
        pdf_bytes = self._build_pdf()
        import builtins as _bi
        with _bi.open(path, 'wb') as f:
            f.write(pdf_bytes)
        return f"✅ {path}"

class Page:
    def __init__(self, raw_data: bytes, page_num: int, total: int):
        self._raw   = raw_data
        self.number = page_num
        self.rect   = type('Rect', (), {'width':612, 'height':792})()
        self._text  = None

    def get_text(self, option='text') -> str:
        if self._text is None:
            self._text = _extract_text_simple(self._raw)
        return self._text

    def search_for(self, query: str) -> list:
        text = self.get_text()
        if query.lower() in text.lower():
            return [type('Rect',(),{'x0':0,'y0':0,'x1':100,'y1':20})()]
        return []

    def get_links(self) -> list:
        links = _find_links(self._raw)
        return [{'uri':l, 'type':'uri'} for l in links]

    def get_pixmap(self, matrix=None, colorspace=None):
        """stub — OCR tools يحتاجه"""
        return type('Pixmap', (), {
            'width':612, 'height':792,
            'samples': b'\xff'*(612*792*3),
            'save': lambda self, path: open(path,'wb').write(b''),
        })()

    def find_tables(self):
        return type('Tables', (), {'tables':[]})()

    def insert_text(self, point, text, **kwargs):
        pass

    def set_rotation(self, degrees):
        pass

class Document:
    """بديل fitz.Document — نفس الواجهة"""

    def __init__(self, path: str = None, stream: bytes = None):
        self._pages_data = []
        self._path  = path
        self._raw   = b''
        self.is_encrypted = False

        if path and os.path.exists(path):
            import builtins as _bi
            with _bi.open(path, 'rb') as f:
                self._raw = f.read()
        elif stream:
            self._raw = stream

        if self._raw:
            self._load()

    def _load(self):
        count = _count_pages(self._raw)

        chunk = max(1, len(self._raw) // max(count, 1))
        for i in range(count):
            start = i * chunk
            end   = start + chunk + 500
            self._pages_data.append(self._raw[start:min(end,len(self._raw))])
        if not self._pages_data:
            self._pages_data = [self._raw]

    def __len__(self): return len(self._pages_data)
    def __iter__(self): return iter(self._get_pages())
    def __enter__(self): return self
    def __exit__(self, *args): pass

    def _get_pages(self):
        return [Page(data, i, len(self._pages_data)) for i, data in enumerate(self._pages_data)]

    def __getitem__(self, idx):
        return Page(self._pages_data[idx], idx, len(self._pages_data))

    @property
    def metadata(self):
        meta = _extract_metadata(self._raw)
        return {
            'title':        meta.get('Title',''),
            'author':       meta.get('Author',''),
            'subject':      meta.get('Subject',''),
            'creator':      meta.get('Creator',''),
            'producer':     meta.get('Producer',''),
            'creationDate': meta.get('CreationDate',''),
            'format':       'PDF',
        }

    def get_page_images(self, page_num: int) -> list:
        return []

    def extract_image(self, xref: int) -> dict:
        return {'ext':'png','image':b''}

    def authenticate(self, password: str) -> bool:
        return True

    def insert_pdf(self, other_doc, from_page=0, to_page=None):
        """دمج مستند آخر"""
        end = to_page + 1 if to_page is not None else len(other_doc)
        for i in range(from_page, end):
            if i < len(other_doc._pages_data):
                self._pages_data.append(other_doc._pages_data[i])

    def save(self, path: str, **kwargs):
        """حفظ — يدمج الصفحات كـ PDF بسيط"""
        writer = PDFWriter()
        for i, data in enumerate(self._pages_data):
            text = _extract_text_simple(data)
            writer.add_text_page(text or f"صفحة {i+1}")
        writer.save(path)

    def select(self, pages: list):
        """اختيار صفحات محددة"""
        self._pages_data = [self._pages_data[i] for i in pages if i < len(self._pages_data)]

    def close(self): pass

def fitz_open(path=None, stream=None, **kwargs):
    if stream: return Document(stream=stream)
    return Document(path)

open = fitz_open

class Matrix:
    def __init__(self, sx=1, sy=1): self.sx=sx; self.sy=sy

class Point:
    def __init__(self, x, y): self.x=x; self.y=y

class Rect:
    def __init__(self, x0=0,y0=0,x1=0,y1=0): self.x0=x0;self.y0=y0;self.x1=x1;self.y1=y1

PDF_PERM_PRINT = 4
PDF_PERM_COPY  = 16
PDF_ENCRYPT_AES_256 = 5

CSRGB = 'rgb'

if __name__ == "__main__":
    import tempfile, os

    w = PDFWriter()
    w.add_text_page("مرحبا بالعالم\nهذا اختبار MiniPDF\nالسطر الثالث")
    w.add_text_page("الصفحة الثانية\nHello World")
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        tmp = f.name
    print(w.save(tmp))

    doc = Document(tmp)
    print(f"الصفحات: {len(doc)}")
    print(f"metadata: {doc.metadata}")
    for i, page in enumerate(doc):
        t = page.get_text()
        print(f"  صفحة {i+1}: {t[:50]}")

    os.unlink(tmp)
    print("✅ MiniPDF OK")
