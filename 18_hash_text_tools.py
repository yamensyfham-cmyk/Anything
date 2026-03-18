"""
أدوات النصوص والهاش
بدون أي مكاتب خارجية — stdlib فقط
"""
import hashlib
import base64
import os
import re
import json
import string

class HashTools:
    ALGOS = ["md5","sha1","sha256","sha512","sha3_256","blake2b"]

    @staticmethod
    def hash_text(text: str) -> dict:
        enc = text.encode('utf-8')
        return {alg: hashlib.new(alg, enc).hexdigest() for alg in HashTools.ALGOS}

    @staticmethod
    def hash_file(path: str, algo="sha256") -> str:
        if not os.path.exists(path): return "❌ الملف غير موجود."
        h = hashlib.new(algo)
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''): h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def hash_file_all(path: str) -> dict:
        if not os.path.exists(path): return {"error": "الملف غير موجود."}
        results = {}
        data = open(path, 'rb').read()
        for alg in HashTools.ALGOS:
            results[alg] = hashlib.new(alg, data).hexdigest()
        return results

    @staticmethod
    def verify_file(path: str, expected_hash: str, algo="sha256") -> str:
        actual = HashTools.hash_file(path, algo)
        if actual.lower() == expected_hash.lower():
            return f"✅ الملف سليم — {algo}: {actual}"
        return f"❌ الهاش لا يتطابق!\nالمتوقع:  {expected_hash}\nالفعلي:   {actual}"

class TextTools:

    @staticmethod
    def encode_base64(text: str) -> str:
        return base64.b64encode(text.encode()).decode()

    @staticmethod
    def decode_base64(encoded: str) -> str:
        try: return base64.b64decode(encoded.encode()).decode('utf-8', errors='replace')
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def encode_url(text: str) -> str:
        import urllib.parse
        return urllib.parse.quote(text)

    @staticmethod
    def decode_url(text: str) -> str:
        import urllib.parse
        return urllib.parse.unquote(text)

    @staticmethod
    def rot13(text: str) -> str:
        return text.translate(str.maketrans(
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
            'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
        ))

    @staticmethod
    def to_hex(text: str) -> str:
        return text.encode().hex()

    @staticmethod
    def from_hex(hex_str: str) -> str:
        try: return bytes.fromhex(hex_str).decode('utf-8', errors='replace')
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def extract_emails(text: str) -> list:
        return list(set(re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)))

    @staticmethod
    def extract_urls(text: str) -> list:
        return list(set(re.findall(r'https?://[^\s"\'<>]+', text)))

    @staticmethod
    def extract_phones(text: str) -> list:
        phones = re.findall(r'[\+]?[\d\s\-\(\)]{9,15}', text)
        return list(set(p.strip() for p in phones if len(re.sub(r'\D','',p)) >= 9))

    @staticmethod
    def extract_ips(text: str) -> list:
        return list(set(re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text)))

    @staticmethod
    def word_count(text: str) -> dict:
        words = text.split()
        chars = len(text)
        lines = text.count('\n') + 1
        return {"words": len(words), "chars": chars, "lines": lines,
                "chars_no_space": len(text.replace(' ','').replace('\n',''))}

    @staticmethod
    def caesar_cipher(text: str, shift: int, decrypt=False) -> str:
        if decrypt: shift = -shift
        result = []
        for c in text:
            if c.isalpha():
                base  = ord('A') if c.isupper() else ord('a')
                result.append(chr((ord(c) - base + shift) % 26 + base))
            else:
                result.append(c)
        return ''.join(result)

    @staticmethod
    def binary_encode(text: str) -> str:
        return ' '.join(format(ord(c), '08b') for c in text)

    @staticmethod
    def binary_decode(binary: str) -> str:
        try:
            parts = binary.strip().split()
            return ''.join(chr(int(b, 2)) for b in parts)
        except Exception as e:
            return f"❌ {e}"

class QRGenerator:
    """
    مولد QR Code نصي (ASCII) بدون مكاتب خارجية
    """
    @staticmethod
    def to_text_art(data: str) -> str:
        """يولد رابط QR Code جاهز للفتح في المتصفح — stdlib فقط"""
        import urllib.parse
        encoded = urllib.parse.quote(data)
        return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded}"

    @staticmethod
    def wifi_qr(ssid: str, password: str, security="WPA") -> str:
        data = f"WIFI:T:{security};S:{ssid};P:{password};;"
        return QRGenerator.to_text_art(data)

    @staticmethod
    def contact_qr(name: str, phone: str, email="") -> str:
        data = f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}\nTEL:{phone}\nEMAIL:{email}\nEND:VCARD"
        return QRGenerator.to_text_art(data)

if __name__ == "__main__":
    menu = {
        "1":  ("هاش نص",              lambda: print(json.dumps(HashTools.hash_text(input("النص => ")), indent=2))),
        "2":  ("هاش ملف",             lambda: print(json.dumps(HashTools.hash_file_all(input("المسار => ")), indent=2))),
        "3":  ("التحقق من ملف",       lambda: print(HashTools.verify_file(input("المسار => "), input("الهاش المتوقع => "), input("الخوارزمية (sha256) => ") or "sha256"))),
        "4":  ("Base64 تشفير",        lambda: print(TextTools.encode_base64(input("النص => ")))),
        "5":  ("Base64 فك",           lambda: print(TextTools.decode_base64(input("المشفر => ")))),
        "6":  ("URL Encode",           lambda: print(TextTools.encode_url(input("النص => ")))),
        "7":  ("URL Decode",           lambda: print(TextTools.decode_url(input("النص => ")))),
        "8":  ("Hex تحويل",           lambda: print(TextTools.to_hex(input("النص => ")))),
        "9":  ("Hex عكس",             lambda: print(TextTools.from_hex(input("Hex => ")))),
        "10": ("Binary تحويل",        lambda: print(TextTools.binary_encode(input("النص => ")))),
        "11": ("Binary عكس",          lambda: print(TextTools.binary_decode(input("Binary => ")))),
        "12": ("Caesar Cipher",        lambda: print(TextTools.caesar_cipher(input("النص => "), int(input("الإزاحة => ")), input("فك؟ (نعم/لا) => ").lower()=="نعم"))),
        "13": ("استخراج IPs/روابط/إيميلات", lambda: _extract_all()),
        "14": ("QR Code — رابط",      lambda: print(QRGenerator.to_text_art(input("النص/الرابط => ")))),
        "15": ("QR Code — WiFi",      lambda: print(QRGenerator.wifi_qr(input("SSID => "), input("كلمة المرور => ")))),
        "16": ("إحصاء الكلمات",       lambda: print(json.dumps(TextTools.word_count(input("النص => ")), indent=2, ensure_ascii=False))),
    }

    def _extract_all():
        text = input("النص => ")
        print("IPs:    ", TextTools.extract_ips(text))
        print("URLs:   ", TextTools.extract_urls(text))
        print("Emails: ", TextTools.extract_emails(text))
        print("Phones: ", TextTools.extract_phones(text))

    while True:
        print("\n═"*45)
        print("  🔧  Hash & Text Tools")
        print("═"*45)
        for k, (l, _) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"خطأ: {e}")
