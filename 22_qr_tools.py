"""
أدوات QR Code والباركود — 15 ميزة
pip install qrcode[pil] Pillow
"""
import os, sys, json, urllib.parse, urllib.request
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

try:
    import qrcode
    from PIL import Image
    _QR = True
except ImportError:
    _QR = False

class QRTools:

    @staticmethod
    def _make_qr(data: str, error="M"):
        if not _QR:

            enc = urllib.parse.quote(data)
            return f"https://api.qrserver.com/v1/create-qr-code/?size=400x400&data={enc}"
        levels = {"L": qrcode.constants.ERROR_CORRECT_L,
                  "M": qrcode.constants.ERROR_CORRECT_M,
                  "H": qrcode.constants.ERROR_CORRECT_H}
        qr = qrcode.QRCode(error_correction=levels.get(error, levels["M"]), border=2)
        qr.add_data(data)
        qr.make(fit=True)
        return qr

    @staticmethod
    def generate(data: str, out="qr.png", color="black", bg="white") -> str:
        qr = QRTools._make_qr(data)
        if isinstance(qr, str): return f"رابط QR: {qr}"
        img = qr.make_image(fill_color=color, back_color=bg)
        img.save(out)
        return f"✅ QR محفوظ: {out}"

    @staticmethod
    def generate_with_logo(data: str, logo_path: str, out="qr_logo.png") -> str:
        """QR مع شعار في المنتصف"""
        if not _QR: return "❌ pip install qrcode[pil]"
        qr  = QRTools._make_qr(data, "H")
        img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
        try:
            logo = Image.open(logo_path).convert('RGBA')
            qr_w, qr_h = img.size
            logo_size   = qr_w // 4
            logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
            pos  = ((qr_w - logo_size) // 2, (qr_h - logo_size) // 2)
            img.paste(logo, pos, logo)
        except Exception as e:
            return f"❌ خطأ في الشعار: {e}"
        img.save(out)
        return f"✅ {out}"

    @staticmethod
    def generate_ascii(data: str) -> str:
        """QR كنص ASCII مباشرة في الطرفية"""
        if not _QR: return f"رابط: https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(data)}"
        import io
        qr = QRTools._make_qr(data)
        f  = io.StringIO()
        qr.print_ascii(out=f, invert=True)
        return f.getvalue()

    @staticmethod
    def batch_generate(data_list: list, folder=".") -> str:
        """توليد QR codes متعددة دفعة واحدة"""
        os.makedirs(folder, exist_ok=True)
        for i, item in enumerate(data_list):
            out = os.path.join(folder, f"qr_{i:03d}.png")
            QRTools.generate(item, out)
        return f"✅ تم توليد {len(data_list)} QR code"

    @staticmethod
    def wifi_qr(ssid: str, password: str, security="WPA", out="wifi_qr.png") -> str:
        data = f"WIFI:T:{security};S:{ssid};P:{password};;"
        return QRTools.generate(data, out)

    @staticmethod
    def contact_qr(name: str, phone="", email="", url="", out="contact_qr.png") -> str:
        data = f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\n"
        if phone: data += f"TEL:{phone}\n"
        if email: data += f"EMAIL:{email}\n"
        if url:   data += f"URL:{url}\n"
        data += "END:VCARD"
        return QRTools.generate(data, out)

    @staticmethod
    def url_qr(url: str, shorten=False, out="url_qr.png") -> str:
        if shorten:
            try:
                short = urllib.request.urlopen(f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(url)}", timeout=5).read().decode()
                url = short
            except Exception:
                pass
        return QRTools.generate(url, out)

    @staticmethod
    def text_qr(text: str, out="text_qr.png") -> str:
        return QRTools.generate(text, out)

    @staticmethod
    def email_qr(to: str, subject="", body="", out="email_qr.png") -> str:
        data = f"mailto:{to}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        return QRTools.generate(data, out)

    @staticmethod
    def sms_qr(number: str, message="", out="sms_qr.png") -> str:
        data = f"SMSTO:{number}:{message}"
        return QRTools.generate(data, out)

    @staticmethod
    def location_qr(lat: float, lng: float, out="location_qr.png") -> str:
        data = f"geo:{lat},{lng}"
        return QRTools.generate(data, out)

    @staticmethod
    def read_qr(image_path: str) -> str:
        """قراءة QR من صورة"""
        try:
            from pyzbar.pyzbar import decode
            from PIL import Image
            img   = Image.open(image_path)
            codes = decode(img)
            return [c.data.decode('utf-8') for c in codes] if codes else "لم يُعثر على QR"
        except ImportError:
            return "❌ pip install pyzbar"
        except Exception as e:
            return f"❌ {e}"

    @staticmethod
    def generate_colored(data: str, fill="#000000", back="#FFFFFF", out="colored_qr.png") -> str:
        return QRTools.generate(data, out, fill, back)

if __name__ == "__main__":
    qt = QRTools()
    menu = {
        "1":  ("QR عادي",               lambda: print(qt.generate(input("البيانات => "), input("الملف (qr.png) => ") or "qr.png"))),
        "2":  ("QR ASCII بالطرفية",     lambda: print(qt.generate_ascii(input("البيانات => ")))),
        "3":  ("QR WiFi",               lambda: print(qt.wifi_qr(input("SSID => "), input("كلمة المرور => ")))),
        "4":  ("QR جهة اتصال",          lambda: print(qt.contact_qr(input("الاسم => "), input("الهاتف => "), input("البريد => ")))),
        "5":  ("QR رابط",               lambda: print(qt.url_qr(input("URL => ")))),
        "6":  ("QR بريد إلكتروني",      lambda: print(qt.email_qr(input("البريد => "), input("الموضوع => "), input("الرسالة => ")))),
        "7":  ("QR SMS",                lambda: print(qt.sms_qr(input("الرقم => "), input("الرسالة => ")))),
        "8":  ("QR موقع جغرافي",        lambda: print(qt.location_qr(float(input("Lat => ")), float(input("Lng => "))))),
        "9":  ("QR ملون",               lambda: print(qt.generate_colored(input("البيانات => "), input("اللون (#000) => ") or "#000000", input("الخلفية (#fff) => ") or "#ffffff"))),
        "10": ("QR مع شعار",            lambda: print(qt.generate_with_logo(input("البيانات => "), input("مسار الشعار => ")))),
        "11": ("توليد دفعي",            lambda: print(qt.batch_generate(input("البيانات (سطر لكل قيمة) => \n").strip().split('\n'), input("المجلد (.) => ") or "."))),
        "12": ("قراءة QR من صورة",      lambda: print(qt.read_qr(input("مسار الصورة => ")))),
    }
    while True:
        print("\n═"*45)
        print("  📱  QR Code Tools — 12 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
