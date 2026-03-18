"""
أدوات CTF واختبار الاختراق — 30 ميزة
مكاتب: stdlib فقط
"""
import os, sys, re, json, hashlib, base64, string, itertools, socket
import urllib.request, urllib.parse, subprocess, time, threading
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

class CTFTools:

    @staticmethod
    def decode_all(text: str) -> dict:
        """محاولة فك كل التشفيرات الشائعة"""
        results = {}

        try:
            padded = text + "=" * (4 - len(text) % 4)
            results["base64"] = base64.b64decode(padded).decode("utf-8","replace")
        except Exception: pass

        try:
            results["base32"] = base64.b32decode(text.upper() + "=" * ((8 - len(text) % 8) % 8)).decode("utf-8","replace")
        except Exception: pass

        try:
            results["hex"] = bytes.fromhex(text.replace(" ","")).decode("utf-8","replace")
        except Exception: pass

        results["rot13"] = text.translate(str.maketrans(
            'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
            'NOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZnopqrstuvwxyzabcdefghijklm'))

        try:
            parts = text.strip().split()
            if all(set(p) <= {"0","1"} for p in parts):
                results["binary"] = ''.join(chr(int(p,2)) for p in parts)
        except Exception: pass

        results["url_decode"] = urllib.parse.unquote(text)

        results["html_decode"] = text.replace("&amp;","&").replace("&lt;","<").replace("&gt;",">").replace("&quot;",'"').replace("&#39;","'")

        try:
            parts = text.strip().split()
            if all(set(p) <= set("01234567") for p in parts):
                results["octal"] = ''.join(chr(int(p,8)) for p in parts)
        except Exception: pass
        return {k:v for k,v in results.items() if v and v != text}

    @staticmethod
    def encode_all(text: str) -> dict:
        return {
            "base64":  base64.b64encode(text.encode()).decode(),
            "base32":  base64.b32encode(text.encode()).decode(),
            "base16":  text.encode().hex(),
            "binary":  ' '.join(format(ord(c),'08b') for c in text),
            "octal":   ' '.join(format(ord(c),'o')   for c in text),
            "decimal": ' '.join(str(ord(c))           for c in text),
            "url":     urllib.parse.quote(text),
            "html":    ''.join(f"&#{ord(c)};" for c in text),
            "rot13":   text.translate(str.maketrans(
                'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
                'NOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZnopqrstuvwxyzabcdefghijklm')),
            "morse":   ' '.join(CTFTools._to_morse(c) for c in text.upper()),
        }

    MORSE = {'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....','I':'..','J':'.---',
             'K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-',
             'U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..','0':'-----','1':'.----','2':'..---',
             '3':'...--','4':'....-','5':'.....','6':'-....','7':'--...','8':'---..','9':'----.'}

    @staticmethod
    def _to_morse(c):
        return CTFTools.MORSE.get(c, '?')

    @staticmethod
    def morse_decode(morse: str) -> str:
        inv = {v:k for k,v in CTFTools.MORSE.items()}
        return ''.join(inv.get(w,'?') for w in morse.strip().split())

    @staticmethod
    def atbash(text: str) -> str:
        result = []
        for c in text:
            if c.isalpha():
                base = ord('A') if c.isupper() else ord('a')
                result.append(chr(base + 25 - (ord(c) - base)))
            else: result.append(c)
        return ''.join(result)

    @staticmethod
    def caesar_all(text: str) -> list:
        results = []
        for shift in range(1,26):
            decoded = ""
            for c in text:
                if c.isalpha():
                    base = ord('A') if c.isupper() else ord('a')
                    decoded += chr((ord(c)-base+shift)%26+base)
                else: decoded += c
            results.append({"shift":shift,"text":decoded})
        return results

    @staticmethod
    def identify_hash(h: str) -> list:
        """تحديد نوع الهاش"""
        types = []
        l = len(h.replace(" ",""))
        if re.match(r'^[a-f0-9]+$', h.lower()):
            if   l == 32:  types.append("MD5")
            elif l == 40:  types.append("SHA1")
            elif l == 56:  types.append("SHA224")
            elif l == 64:  types.append("SHA256")
            elif l == 96:  types.append("SHA384")
            elif l == 128: types.append("SHA512")
        if h.startswith("$2"): types.append("bcrypt")
        if h.startswith("$1"): types.append("MD5-crypt")
        if h.startswith("$5"): types.append("SHA256-crypt")
        if h.startswith("$6"): types.append("SHA512-crypt")
        return types or ["unknown"]

    @staticmethod
    def crack_hash(target_hash: str, wordlist_path: str, algo="md5") -> str:
        """كسر هاش بقائمة كلمات"""
        if not os.path.exists(wordlist_path):
            return "❌ قائمة الكلمات غير موجودة"
        target = target_hash.lower()
        try:
            with open(wordlist_path, errors="ignore") as f:
                for line in f:
                    word = line.strip()
                    h = hashlib.new(algo, word.encode()).hexdigest()
                    if h == target:
                        return f"✅ كلمة المرور: {word}"
            return "❌ لم يُعثر في القائمة"
        except Exception as e:
            return f"❌ {e}"

    @staticmethod
    def rainbow_table(words: list, algos=None) -> dict:
        """إنشاء جدول radbow"""
        algos = algos or ["md5","sha1","sha256"]
        table = {}
        for word in words:
            table[word] = {algo: hashlib.new(algo,word.encode()).hexdigest() for algo in algos}
        return table

    @staticmethod
    def crack_with_mutations(target: str, base_word: str, algo="md5") -> str:
        """كسر هاش مع تحورات"""
        mutations = [
            base_word,
            base_word.lower(), base_word.upper(), base_word.capitalize(),
            base_word + "123", base_word + "!", base_word + "1",
            base_word + "2023", base_word + "2024",
            "123" + base_word, base_word[::-1],
            base_word.replace("a","@").replace("e","3").replace("i","1").replace("o","0"),
        ]
        for m in mutations:
            if hashlib.new(algo, m.encode()).hexdigest() == target.lower():
                return f"✅ {m}"
        return "❌ لم يُعثر"

    @staticmethod
    def banner_grab(host: str, port: int) -> str:
        """جمع Banner من خدمة"""
        try:
            s = socket.socket()
            s.settimeout(5)
            s.connect((host, port))
            s.send(b"HEAD / HTTP/1.0\r\n\r\n")
            banner = s.recv(1024).decode("utf-8","replace")
            s.close()
            return banner[:500]
        except Exception as e:
            return f"❌ {e}"

    @staticmethod
    def directory_bruteforce(url: str, wordlist_path=None) -> list:
        """فحص مسارات مخفية"""
        common = ["admin","login","panel","dashboard","wp-admin","api","backup",
                  "config","test","dev","staging","phpmyadmin","upload","uploads",
                  "files","docs","robots.txt","sitemap.xml",".git","wp-login.php"]
        if wordlist_path and os.path.exists(wordlist_path):
            with open(wordlist_path, errors="ignore") as f:
                paths = [l.strip() for l in f.readlines()[:500]]
        else:
            paths = common
        found = []
        for path in paths:
            target = url.rstrip("/") + "/" + path.lstrip("/")
            try:
                req = urllib.request.Request(target, headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=5) as r:
                    if r.status < 400:
                        found.append({"url":target,"status":r.status})
            except urllib.request.HTTPError as e:
                if e.code not in (404,403): found.append({"url":target,"status":e.code})
            except Exception: pass
        return found

    @staticmethod
    def subdomain_bruteforce(domain: str, wordlist=None) -> list:
        if wordlist is None:
            wordlist = ["www","mail","ftp","admin","api","dev","test","staging",
                        "blog","shop","portal","vpn","remote","m","mobile","app",
                        "beta","cdn","static","img","media","login","secure","auth"]
        found = []
        for sub in wordlist:
            target = f"{sub}.{domain}"
            try:
                ip = socket.gethostbyname(target)
                found.append({"subdomain":target,"ip":ip})
            except Exception: pass
        return found

    @staticmethod
    def detect_waf(url: str) -> dict:
        """كشف WAF"""
        headers = {}
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                headers = dict(r.headers)
        except urllib.request.HTTPError as e:
            headers = dict(e.headers)
        except Exception: pass
        waf_signs = {
            "Cloudflare":   ["cf-ray","cloudflare"],
            "AWS WAF":      ["awselb","x-amzn"],
            "Akamai":       ["akamai","x-check-cacheable"],
            "Sucuri":       ["x-sucuri","sucuri"],
            "ModSecurity":  ["mod_security","modsecurity"],
        }
        detected = []
        headers_str = json.dumps(headers).lower()
        for waf, signs in waf_signs.items():
            if any(s in headers_str for s in signs):
                detected.append(waf)
        return {"waf":detected or ["لم يُكتشف"],"headers":headers}

    @staticmethod
    def file_magic(path: str) -> dict:
        """تحديد نوع الملف من الـ Magic Bytes"""
        magic = {
            b'\xff\xd8\xff': "JPEG",
            b'\x89PNG':      "PNG",
            b'GIF8':         "GIF",
            b'PK\x03\x04':  "ZIP/XLSX/DOCX/APK",
            b'%PDF':         "PDF",
            b'\x7fELF':      "ELF Executable",
            b'MZ':           "Windows PE/EXE",
            b'OggS':         "OGG Audio",
            b'ID3':          "MP3",
            b'\xff\xfb':     "MP3",
            b'ftyp':         "MP4",
            b'RIFF':         "WAV/AVI",
            b'<!DOCTYPE':    "HTML",
            b'<?xml':        "XML",
            b'{"':           "JSON",
            b'#!/':          "Shell Script",
        }
        try:
            with open(path,'rb') as f:
                header = f.read(16)
            for sig, ftype in magic.items():
                if header[:len(sig)] == sig or sig in header[:16]:
                    return {"type":ftype,"hex":header.hex(),"path":path}
            return {"type":"unknown","hex":header.hex(),"path":path}
        except Exception as e:
            return {"error":str(e)}

    @staticmethod
    def strings_extract(path: str, min_len=4) -> list:
        """استخراج النصوص من ملف ثنائي"""
        try:
            with open(path,'rb') as f: data = f.read()
            pattern = re.compile(rb'[\x20-\x7e]{' + str(min_len).encode() + rb',}')
            return [m.decode('ascii') for m in pattern.findall(data)][:100]
        except Exception as e:
            return [f"❌ {e}"]

    @staticmethod
    def xor_brute(data: bytes, sample_text=b"flag") -> list:
        """كسر XOR بـ single byte"""
        results = []
        for key in range(256):
            decoded = bytes(b ^ key for b in data)
            if sample_text in decoded:
                results.append({"key":key,"hex":hex(key),"text":decoded.decode('utf-8','replace')[:100]})
        return results

    @staticmethod
    def find_flags(text: str, patterns=None) -> list:
        """البحث عن flags في نص"""
        patterns = patterns or [
            r'flag\{[^}]+\}',
            r'CTF\{[^}]+\}',
            r'[A-Z]+\{[^}]+\}',
            r'[a-f0-9]{32}',
            r'[a-f0-9]{64}',
        ]
        found = []
        for pat in patterns:
            matches = re.findall(pat, text, re.I)
            found.extend(matches)
        return list(set(found))

    @staticmethod
    def lsb_steganography_detect(image_path: str) -> str:
        """كشف إخفاء LSB في صورة"""
        try:
            from PIL import Image
            img    = Image.open(image_path).convert('RGB')
            pixels = list(img.getdata())
            bits   = ""
            for r,g,b in pixels[:1000]:
                bits += str(r&1)+str(g&1)+str(b&1)
            chars = [bits[i:i+8] for i in range(0,len(bits)-7,8)]
            text  = ''.join(chr(int(c,2)) for c in chars if int(c,2) > 31)
            printable = ''.join(c for c in text if c in string.printable)
            return printable[:200] if printable.strip() else "لا يوجد نص مخفي واضح"
        except ImportError:
            return "❌ pip install Pillow"
        except Exception as e:
            return f"❌ {e}"

if __name__ == "__main__":
    ct = CTFTools()
    menu = {
        "1":  ("فك كل التشفيرات",           lambda: print(json.dumps(ct.decode_all(input("النص => ")), indent=2, ensure_ascii=False))),
        "2":  ("تشفير بكل الطرق",            lambda: print(json.dumps(ct.encode_all(input("النص => ")), indent=2, ensure_ascii=False))),
        "3":  ("كل Caesar shifts",          lambda: [print(f"  {r['shift']:>2}: {r['text']}") for r in ct.caesar_all(input("النص => "))]),
        "4":  ("Atbash Cipher",             lambda: print(ct.atbash(input("النص => ")))),
        "5":  ("Morse — تشفير",             lambda: print(ct.encode_all(input("النص => ")).get("morse",""))),
        "6":  ("Morse — فك",                lambda: print(ct.morse_decode(input("Morse => ")))),
        "7":  ("تحديد نوع الهاش",            lambda: print(ct.identify_hash(input("الهاش => ")))),
        "8":  ("كسر هاش بقائمة كلمات",      lambda: print(ct.crack_hash(input("الهاش => "), input("قائمة الكلمات => "), input("الخوارزمية (md5) => ") or "md5"))),
        "9":  ("كسر هاش بتحورات",           lambda: print(ct.crack_with_mutations(input("الهاش => "), input("الكلمة الأساس => ")))),
        "10": ("إنشاء Rainbow Table",       lambda: print(json.dumps(ct.rainbow_table(input("كلمات (مسافة) => ").split()), indent=2))),
        "11": ("Banner Grab",               lambda: print(ct.banner_grab(input("Host => "), int(input("Port => "))))),
        "12": ("فحص مسارات مخفية",          lambda: [print(f"  [{r['status']}] {r['url']}") for r in ct.directory_bruteforce(input("URL => "))]),
        "13": ("Subdomain Bruteforce",      lambda: [print(f"  {r['subdomain']} → {r['ip']}") for r in ct.subdomain_bruteforce(input("Domain => "))]),
        "14": ("كشف WAF",                   lambda: print(json.dumps(ct.detect_waf(input("URL => ")), indent=2, ensure_ascii=False))),
        "15": ("نوع الملف (Magic Bytes)",    lambda: print(json.dumps(ct.file_magic(input("المسار => ")), indent=2))),
        "16": ("استخراج نصوص من ملف",        lambda: [print(f"  {s}") for s in ct.strings_extract(input("المسار => "))]),
        "17": ("XOR Brute Force",           lambda: print(json.dumps(ct.xor_brute(open(input("مسار الملف => "),'rb').read(), input("النص المتوقع => ").encode()), indent=2))),
        "18": ("بحث عن Flags",             lambda: print(ct.find_flags(input("النص => ")))),
        "19": ("كشف إخفاء LSB",             lambda: print(ct.lsb_steganography_detect(input("مسار الصورة => ")))),
    }
    while True:
        print("\n═"*45)
        print("  🏴  CTF Tools — 19 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
