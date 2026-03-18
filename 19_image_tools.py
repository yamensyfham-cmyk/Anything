"""
أدوات الصور المتقدمة — 25 ميزة
pip install Pillow
"""
import os, sys, json, hashlib
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont, ImageOps, ExifTags
    _PIL = True
except ImportError:
    _PIL = False
    print("❌ pip install Pillow")

def _need_pil():
    if not _PIL: print("❌ pip install Pillow"); return False
    return True

class ImageTools:

    @staticmethod
    def convert(src, fmt):
        """تحويل صورة لصيغة أخرى PNG/JPG/WEBP/BMP/TIFF"""
        if not _need_pil(): return
        out = os.path.splitext(src)[0] + f".{fmt.lower()}"
        with Image.open(src) as img:
            img.convert('RGB').save(out)
        return f"✅ {out}"

    @staticmethod
    def batch_convert(folder, fmt):
        """تحويل كل صور مجلد دفعة واحدة"""
        if not _need_pil(): return
        results = []
        for f in os.listdir(folder):
            if f.lower().endswith(('.jpg','.jpeg','.png','.webp','.bmp')):
                r = ImageTools.convert(os.path.join(folder,f), fmt)
                results.append(r)
        return f"✅ تم تحويل {len(results)} صورة"

    @staticmethod
    def resize(src, width, height=0, keep_ratio=True):
        """تغيير حجم صورة"""
        if not _need_pil(): return
        with Image.open(src) as img:
            if keep_ratio and height == 0:
                ratio = width / img.width
                height = int(img.height * ratio)
            img = img.resize((width, height), Image.LANCZOS)
            img.save(src)
        return f"✅ {width}x{height}"

    @staticmethod
    def compress(src, quality=60, out=None):
        """ضغط صورة مع تقليل الجودة"""
        if not _need_pil(): return
        out = out or src
        with Image.open(src) as img:
            img.convert('RGB').save(out, optimize=True, quality=quality)
        size = os.path.getsize(out)
        return f"✅ {out} — {size/1024:.1f} KB"

    @staticmethod
    def batch_compress(folder, quality=60):
        """ضغط كل صور مجلد"""
        if not _need_pil(): return
        count = 0
        saved = 0
        for f in os.listdir(folder):
            if f.lower().endswith(('.jpg','.jpeg')):
                path = os.path.join(folder,f)
                before = os.path.getsize(path)
                ImageTools.compress(path, quality)
                after = os.path.getsize(path)
                saved += before - after
                count += 1
        return f"✅ {count} صورة — وفّرت {saved/1024/1024:.2f} MB"

    @staticmethod
    def apply_filter(src, flt):
        """
        الفلاتر: blur, sharpen, emboss, edge, smooth, detail,
                 grayscale, sepia, invert, vintage
        """
        if not _need_pil(): return
        with Image.open(src) as img:
            if flt == "blur":       img = img.filter(ImageFilter.BLUR)
            elif flt == "sharpen":  img = img.filter(ImageFilter.SHARPEN)
            elif flt == "emboss":   img = img.filter(ImageFilter.EMBOSS)
            elif flt == "edge":     img = img.filter(ImageFilter.FIND_EDGES)
            elif flt == "smooth":   img = img.filter(ImageFilter.SMOOTH_MORE)
            elif flt == "detail":   img = img.filter(ImageFilter.DETAIL)
            elif flt == "grayscale":img = ImageOps.grayscale(img)
            elif flt == "invert":   img = ImageOps.invert(img.convert('RGB'))
            elif flt == "sepia":
                img = ImageOps.grayscale(img).convert('RGB')
                r,g,b = img.split()
                r = r.point(lambda i: min(255, i + 60))
                g = g.point(lambda i: min(255, i + 30))
                img = Image.merge('RGB',(r,g,b))
            elif flt == "vintage":
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.5)
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(0.8)
            out = os.path.splitext(src)[0] + f"_{flt}.jpg"
            img.save(out)
            return f"✅ {out}"

    @staticmethod
    def adjust(src, brightness=1.0, contrast=1.0, saturation=1.0, sharpness=1.0):
        """تعديل الإضاءة والتباين والألوان"""
        if not _need_pil(): return
        with Image.open(src) as img:
            img = ImageEnhance.Brightness(img).enhance(brightness)
            img = ImageEnhance.Contrast(img).enhance(contrast)
            img = ImageEnhance.Color(img).enhance(saturation)
            img = ImageEnhance.Sharpness(img).enhance(sharpness)
            img.save(src)
        return "✅ تم التعديل"

    @staticmethod
    def rotate(src, degrees, out=None):
        if not _need_pil(): return
        out = out or src
        with Image.open(src) as img:
            img.rotate(degrees, expand=True).save(out)
        return f"✅ مُدار {degrees}°"

    @staticmethod
    def flip(src, direction="horizontal"):
        if not _need_pil(): return
        with Image.open(src) as img:
            if direction == "horizontal": img = ImageOps.mirror(img)
            else:                         img = ImageOps.flip(img)
            img.save(src)
        return "✅ تم القلب"

    @staticmethod
    def crop(src, left, top, right, bottom, out=None):
        if not _need_pil(): return
        out = out or src
        with Image.open(src) as img:
            img.crop((left,top,right,bottom)).save(out)
        return f"✅ {out}"

    @staticmethod
    def crop_center(src, width, height, out=None):
        """قص من المنتصف"""
        if not _need_pil(): return
        out = out or src
        with Image.open(src) as img:
            w,h = img.size
            l = (w-width)//2; t = (h-height)//2
            img.crop((l,t,l+width,t+height)).save(out)
        return f"✅ {out}"

    @staticmethod
    def add_text(src, text, x=10, y=10, color=(255,255,255), size=30, out=None):
        if not _need_pil(): return
        out = out or src
        with Image.open(src) as img:
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("/system/fonts/Roboto-Regular.ttf", size)
            except Exception:
                font = ImageFont.load_default()
            draw.text((x,y), text, fill=color, font=font)
            img.save(out)
        return f"✅ {out}"

    @staticmethod
    def watermark(src, text="© UAS", out=None):
        """علامة مائية شفافة"""
        if not _need_pil(): return
        out = out or os.path.splitext(src)[0] + "_wm.png"
        with Image.open(src).convert('RGBA') as img:
            overlay = Image.new('RGBA', img.size, (0,0,0,0))
            draw    = ImageDraw.Draw(overlay)
            try:
                font = ImageFont.truetype("/system/fonts/Roboto-Regular.ttf", 40)
            except Exception:
                font = ImageFont.load_default()
            w,h = img.size
            draw.text((w//2-50, h//2), text, fill=(255,255,255,80), font=font)
            img = Image.alpha_composite(img, overlay)
            img.save(out)
        return f"✅ {out}"

    @staticmethod
    def merge_horizontal(images: list, out="merged.jpg"):
        """دمج صور جنباً لجنب"""
        if not _need_pil(): return
        imgs  = [Image.open(p) for p in images]
        total = sum(i.width for i in imgs)
        maxh  = max(i.height for i in imgs)
        res   = Image.new('RGB', (total, maxh))
        x = 0
        for img in imgs:
            res.paste(img, (x,0)); x += img.width; img.close()
        res.save(out)
        return f"✅ {out}"

    @staticmethod
    def collage(images: list, cols=2, out="collage.jpg"):
        """إنشاء كولاج"""
        if not _need_pil(): return
        imgs = [Image.open(p).resize((400,400)) for p in images]
        rows = (len(imgs)+cols-1)//cols
        res  = Image.new('RGB', (cols*400, rows*400), (255,255,255))
        for i, img in enumerate(imgs):
            x = (i%cols)*400; y = (i//cols)*400
            res.paste(img, (x,y)); img.close()
        res.save(out)
        return f"✅ {out}"

    @staticmethod
    def info(src) -> dict:
        if not _need_pil(): return {}
        with Image.open(src) as img:
            info = {
                "الملف":    src,
                "الحجم":   f"{os.path.getsize(src)/1024:.1f} KB",
                "الأبعاد": f"{img.width}x{img.height}",
                "الوضع":   img.mode,
                "الصيغة":  img.format,
            }
            try:
                exif = img._getexif()
                if exif:
                    info["EXIF"] = {ExifTags.TAGS.get(k,k): str(v)[:50]
                                    for k,v in list(exif.items())[:10]}
            except Exception:
                pass
        return info

    @staticmethod
    def extract_colors(src, count=5) -> list:
        """استخراج الألوان الأكثر شيوعاً في الصورة"""
        if not _need_pil(): return []
        with Image.open(src) as img:
            img = img.convert('RGB').resize((100,100))
            pixels = list(img.getdata())
            freq = {}
            for p in pixels:
                r,g,b = p[0]//32*32, p[1]//32*32, p[2]//32*32
                key = f"#{r:02x}{g:02x}{b:02x}"
                freq[key] = freq.get(key,0) + 1
            return sorted(freq.items(), key=lambda x:-x[1])[:count]

    @staticmethod
    def hash_image(src) -> str:
        """بصمة الصورة (perceptual hash)"""
        if not _need_pil(): return ""
        with Image.open(src) as img:
            img = img.convert('L').resize((8,8), Image.LANCZOS)
            pixels = list(img.getdata())
            avg = sum(pixels)//len(pixels)
            bits = ''.join('1' if p>avg else '0' for p in pixels)
            return hex(int(bits,2))[2:].zfill(16)

    @staticmethod
    def compare_images(src1, src2) -> dict:
        """مقارنة صورتين"""
        if not _need_pil(): return {}
        h1 = ImageTools.hash_image(src1)
        h2 = ImageTools.hash_image(src2)
        diff = bin(int(h1,16)^int(h2,16)).count('1')
        return {"hash1":h1,"hash2":h2,"difference":diff,
                "similar": diff < 10}

    @staticmethod
    def create_thumbnail(src, size=128, out=None):
        if not _need_pil(): return
        out = out or os.path.splitext(src)[0] + f"_thumb.jpg"
        with Image.open(src) as img:
            img.thumbnail((size,size))
            img.save(out)
        return f"✅ {out}"

    @staticmethod
    def remove_metadata(src, out=None):
        """إزالة EXIF وبيانات الخصوصية من الصورة"""
        if not _need_pil(): return
        out = out or src
        with Image.open(src) as img:
            clean = Image.new(img.mode, img.size)
            clean.putdata(list(img.getdata()))
            clean.save(out)
        return f"✅ تم حذف البيانات الوصفية: {out}"

    @staticmethod
    def split_gif(src, out_folder="."):
        """تقسيم GIF لإطارات"""
        if not _need_pil(): return
        os.makedirs(out_folder, exist_ok=True)
        frames = 0
        with Image.open(src) as img:
            try:
                while True:
                    img.save(os.path.join(out_folder, f"frame_{frames:03d}.png"))
                    frames += 1
                    img.seek(img.tell()+1)
            except EOFError:
                pass
        return f"✅ {frames} إطار"

if __name__ == "__main__":
    import json
    it = ImageTools()
    menu = {
        "1":  ("معلومات صورة",         lambda: print(json.dumps(it.info(input("المسار => ")), indent=2, ensure_ascii=False))),
        "2":  ("تحويل صيغة",           lambda: print(it.convert(input("المسار => "), input("الصيغة (jpg/png/webp) => ")))),
        "3":  ("تغيير حجم",            lambda: print(it.resize(input("المسار => "), int(input("العرض => "))))),
        "4":  ("ضغط صورة",             lambda: print(it.compress(input("المسار => "), int(input("الجودة 1-95 (60) => ") or 60)))),
        "5":  ("فلتر",                 lambda: print(it.apply_filter(input("المسار => "), input("الفلتر (blur/sharpen/grayscale/sepia/invert/vintage/emboss/edge) => ")))),
        "6":  ("تعديل إضاءة/تباين",    lambda: print(it.adjust(input("المسار => "), float(input("إضاءة (1.0) => ") or 1), float(input("تباين (1.0) => ") or 1)))),
        "7":  ("دوران",                lambda: print(it.rotate(input("المسار => "), int(input("الزاوية => "))))),
        "8":  ("قلب أفقي/عمودي",       lambda: print(it.flip(input("المسار => "), input("(horizontal/vertical) => ")))),
        "9":  ("قص",                   lambda: print(it.crop(input("المسار => "), *[int(input(f"{x} => ")) for x in ["left","top","right","bottom"]]))),
        "10": ("إضافة نص",             lambda: print(it.add_text(input("المسار => "), input("النص => ")))),
        "11": ("علامة مائية",          lambda: print(it.watermark(input("المسار => "), input("النص => ")))),
        "12": ("دمج صور أفقياً",        lambda: print(it.merge_horizontal(input("المسارات (مفصولة بمسافة) => ").split()))),
        "13": ("كولاج",                lambda: print(it.collage(input("المسارات (مفصولة بمسافة) => ").split(), int(input("أعمدة (2) => ") or 2)))),
        "14": ("استخراج الألوان",       lambda: print(it.extract_colors(input("المسار => ")))),
        "15": ("تصغير (Thumbnail)",     lambda: print(it.create_thumbnail(input("المسار => "), int(input("الحجم (128) => ") or 128)))),
        "16": ("حذف EXIF",             lambda: print(it.remove_metadata(input("المسار => ")))),
        "17": ("مقارنة صورتين",        lambda: print(json.dumps(it.compare_images(input("الصورة 1 => "), input("الصورة 2 => ")), indent=2))),
        "18": ("ضغط كل مجلد",          lambda: print(it.batch_compress(input("المجلد => "), int(input("الجودة (60) => ") or 60)))),
        "19": ("تحويل كل مجلد",        lambda: print(it.batch_convert(input("المجلد => "), input("الصيغة => ")))),
        "20": ("تقسيم GIF",            lambda: print(it.split_gif(input("المسار => "), input("مجلد الإخراج (.) => ") or "."))),
    }
    while True:
        print("\n═"*45)
        print("  🖼  Image Tools — 20 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
