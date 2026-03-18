"""
أدوات الأمان المتقدمة — 25 ميزة
مكاتب: stdlib فقط + requests اختياري
"""
import os, sys, re, json, hashlib, secrets, string, base64, socket
import urllib.request, urllib.parse, time, subprocess
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

class SecurityToolkit:

    @staticmethod
    def bulk_generate(count=10, length=16, symbols=True, numbers=True) -> list:
        pool = string.ascii_letters
        if numbers: pool += string.digits
        if symbols: pool += "!@#$%^&*()_+-="
        return [''.join(secrets.choice(pool) for _ in range(length)) for _ in range(count)]

    @staticmethod
    def check_pwned(password: str) -> dict:
        """التحقق من تسريب كلمة المرور عبر HaveIBeenPwned API"""
        sha1  = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix, suffix = sha1[:5], sha1[5:]
        try:
            url  = f"https://api.pwnedpasswords.com/range/{prefix}"
            resp = urllib.request.urlopen(url, timeout=10).read().decode()
            for line in resp.split('\n'):
                if line.startswith(suffix):
                    count = int(line.split(':')[1].strip())
                    return {"leaked": True, "times": count, "hash": sha1}
            return {"leaked": False, "hash": sha1}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def analyze_password_pattern(password: str) -> dict:
        """تحليل نمط كلمة المرور"""
        return {
            "length":       len(password),
            "uppercase":    sum(c.isupper() for c in password),
            "lowercase":    sum(c.islower() for c in password),
            "digits":       sum(c.isdigit() for c in password),
            "symbols":      sum(c in string.punctuation for c in password),
            "entropy_bits": round(len(password) * (len(set(password)) / len(password)) * 4.7, 1),
            "patterns":     SecurityToolkit._detect_patterns(password),
        }

    @staticmethod
    def _detect_patterns(pwd: str) -> list:
        issues = []
        if re.search(r'(.)\1{2,}', pwd): issues.append("تكرار حروف")
        if re.search(r'(012|123|234|345|456|567|678|789|890)', pwd): issues.append("تسلسل أرقام")
        if re.search(r'(abc|bcd|cde|def|efg)', pwd.lower()): issues.append("تسلسل أحرف")
        if len(set(pwd)) < len(pwd) * 0.5: issues.append("تنوع منخفض")
        common = ["password","123456","qwerty","admin","letmein","welcome","monkey"]
        if pwd.lower() in common: issues.append("كلمة مرور شائعة جداً!")
        return issues or ["لا أنماط واضحة ✅"]

    @staticmethod
    def caesar_brute(ciphertext: str) -> list:
        """كسر تشفير Caesar بكل الإزاحات"""
        results = []
        for shift in range(26):
            decoded = ""
            for c in ciphertext:
                if c.isalpha():
                    base = ord('A') if c.isupper() else ord('a')
                    decoded += chr((ord(c) - base - shift) % 26 + base)
                else:
                    decoded += c
            results.append({"shift": shift, "text": decoded})
        return results

    @staticmethod
    def vigenere_encrypt(text: str, key: str) -> str:
        key    = key.upper()
        result = []
        ki     = 0
        for c in text:
            if c.isalpha():
                shift = ord(key[ki % len(key)]) - ord('A')
                base  = ord('A') if c.isupper() else ord('a')
                result.append(chr((ord(c) - base + shift) % 26 + base))
                ki += 1
            else:
                result.append(c)
        return ''.join(result)

    @staticmethod
    def vigenere_decrypt(text: str, key: str) -> str:
        key    = key.upper()
        result = []
        ki     = 0
        for c in text:
            if c.isalpha():
                shift = ord(key[ki % len(key)]) - ord('A')
                base  = ord('A') if c.isupper() else ord('a')
                result.append(chr((ord(c) - base - shift) % 26 + base))
                ki += 1
            else:
                result.append(c)
        return ''.join(result)

    @staticmethod
    def xor_encrypt(data: bytes, key: str) -> bytes:
        kb = hashlib.sha256(key.encode()).digest()
        return bytes(b ^ kb[i % 32] for i, b in enumerate(data))

    @staticmethod
    def steganography_hide(text_to_hide: str, carrier_text: str) -> str:
        """إخفاء نص داخل نص باستخدام Unicode Zero-Width"""
        binary = ''.join(format(ord(c), '08b') for c in text_to_hide)
        zwc    = {'0': '\u200b', '1': '\u200c'}
        hidden = ''.join(zwc[b] for b in binary) + '\u200d'
        mid    = len(carrier_text) // 2
        return carrier_text[:mid] + hidden + carrier_text[mid:]

    @staticmethod
    def steganography_reveal(text: str) -> str:
        """استخراج نص مخفي"""
        zwc_rev = {'\u200b': '0', '\u200c': '1'}
        bits    = ''
        reading = False
        for c in text:
            if c in zwc_rev:
                bits += zwc_rev[c]
                reading = True
            elif c == '\u200d' and reading:
                break
        if not bits: return "لا يوجد نص مخفي."
        chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
        return ''.join(chr(int(b, 2)) for b in chars if len(b)==8)

    @staticmethod
    def virustotal_check(file_hash: str, api_key: str) -> dict:
        """فحص هاش على VirusTotal"""
        try:
            url  = f"https://www.virustotal.com/api/v3/files/{file_hash}"
            req  = urllib.request.Request(url, headers={"x-apikey": api_key})
            data = json.loads(urllib.request.urlopen(req, timeout=15).read())
            stats = data.get("data",{}).get("attributes",{}).get("last_analysis_stats",{})
            return stats
        except Exception as e: return {"error": str(e)}

    @staticmethod
    def check_email_breach(email: str) -> dict:
        """التحقق من تسريب بريد إلكتروني"""
        try:
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote(email)}"
            req = urllib.request.Request(url, headers={
                "hibp-api-key": "your_key",
                "User-Agent":   "UAS-Tool"
            })
            data = json.loads(urllib.request.urlopen(req, timeout=10).read())
            return {"breaches": len(data), "sites": [b.get("Name","") for b in data[:10]]}
        except urllib.request.HTTPError as e:
            if e.code == 404: return {"breaches": 0, "message": "✅ لا توجد تسريبات"}
            return {"error": f"HTTP {e.code}"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def port_vulnerability_check(host: str) -> list:
        """فحص الخدمات الشائعة وثغراتها"""
        risky_ports = {
            21:  "FTP — بيانات نصية غير مشفرة",
            23:  "Telnet — بروتوكول غير آمن",
            25:  "SMTP — قد يُستخدم للـ Spam",
            80:  "HTTP — غير مشفر",
            111: "RPC — ثغرات قديمة",
            135: "RPC/DCOM — هجمات Windows",
            139: "NetBIOS — مشاركة ملفات غير آمنة",
            445: "SMB — WannaCry/EternalBlue",
            1433:"MSSQL — قواعد بيانات",
            3306:"MySQL — قواعد بيانات",
            3389:"RDP — هجمات Brute Force",
            5900:"VNC — تحكم عن بعد",
            6379:"Redis — بدون مصادقة افتراضياً",
            27017:"MongoDB — بدون مصادقة افتراضياً",
        }
        results = []
        for port, risk in risky_ports.items():
            s = socket.socket()
            s.settimeout(0.5)
            if s.connect_ex((host, port)) == 0:
                results.append({"port": port, "risk": risk, "status": "⚠ مفتوح"})
            s.close()
        return results

    @staticmethod
    def scan_for_secrets(folder: str) -> list:
        """البحث عن مفاتيح API وكلمات مرور في الكود"""
        patterns = {
            "API Key":       r'(?:api[_-]?key|apikey)\s*[=:]\s*["\']?([A-Za-z0-9_\-]{20,})',
            "Secret":        r'(?:secret|token|passwd|password)\s*[=:]\s*["\']([^"\']{8,})',
            "AWS Key":       r'AKIA[0-9A-Z]{16}',
            "Private Key":   r'-----BEGIN.*PRIVATE KEY-----',
            "Google API":    r'AIza[0-9A-Za-z\-_]{35}',
            "GitHub Token":  r'gh[pousr]_[A-Za-z0-9_]{36}',
        }
        found = []
        for root, _, files in os.walk(folder):
            for fname in files:
                if fname.endswith(('.py','.js','.env','.json','.yaml','.yml','.txt','.sh')):
                    path = os.path.join(root, fname)
                    try:
                        content = open(path, errors='ignore').read()
                        for ptype, pat in patterns.items():
                            matches = re.findall(pat, content, re.I)
                            if matches:
                                found.append({"file":path,"type":ptype,"matches":matches[:3]})
                    except Exception: pass
        return found

    @staticmethod
    def jwt_decode(token: str) -> dict:
        """فك تشفير JWT (بدون التحقق)"""
        try:
            parts = token.split('.')
            if len(parts) != 3: return {"error": "ليس JWT صالح"}
            def decode_part(part):
                padding = 4 - len(part) % 4
                if padding != 4: part += '=' * padding
                return json.loads(base64.urlsafe_b64decode(part))
            return {
                "header":  decode_part(parts[0]),
                "payload": decode_part(parts[1]),
                "signature": parts[2][:20] + "...",
            }
        except Exception as e: return {"error": str(e)}

    @staticmethod
    def generate_secure_token(length=32, format="hex") -> str:
        if format == "hex":    return secrets.token_hex(length)
        if format == "base64": return secrets.token_urlsafe(length)
        if format == "uuid":
            import uuid; return str(uuid.uuid4())
        return secrets.token_hex(length)

    @staticmethod
    def hash_file_verify(path1: str, path2: str) -> dict:
        """مقارنة ملفين بالهاش"""
        def h(p):
            sha = hashlib.sha256()
            with open(p,'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''): sha.update(chunk)
            return sha.hexdigest()
        try:
            h1, h2 = h(path1), h(path2)
            return {"file1":path1,"file2":path2,"hash1":h1,"hash2":h2,"identical":h1==h2}
        except Exception as e: return {"error":str(e)}

    @staticmethod
    def brute_force_zip(zip_path: str, wordlist_path: str) -> str:
        """محاولة فتح ملف ZIP بقائمة كلمات"""
        import zipfile
        if not os.path.exists(zip_path):     return "❌ ملف ZIP غير موجود"
        if not os.path.exists(wordlist_path): return "❌ قائمة الكلمات غير موجودة"
        try:
            with zipfile.ZipFile(zip_path) as zf:
                with open(wordlist_path) as wl:
                    for line in wl:
                        pwd = line.strip()
                        try:
                            zf.extractall(pwd=pwd.encode())
                            return f"✅ كلمة المرور: {pwd}"
                        except Exception: pass
            return "❌ لم يُعثر على كلمة المرور"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def network_sniff_summary(iface="wlan0", duration=10) -> dict:
        """ملخص حزم الشبكة بدون scapy"""
        try:
            result = subprocess.run(
                ["tcpdump", "-i", iface, "-c", "100", "-q", f"--time-stamp-precision=milli"],
                capture_output=True, text=True, timeout=duration+5
            )
            lines = result.stderr.split('\n') + result.stdout.split('\n')
            ips   = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '\n'.join(lines))
            freq  = {}
            for ip in ips: freq[ip] = freq.get(ip,0) + 1
            return {"top_ips": sorted(freq.items(),key=lambda x:-x[1])[:10], "total_packets": len(lines)}
        except FileNotFoundError:
            return {"error": "tcpdump غير متاح. نفّذ: pkg install tcpdump"}
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    st = SecurityToolkit()
    menu = {
        "1":  ("توليد كلمات مرور دفعي",    lambda: [print(f"  {p}") for p in st.bulk_generate(int(input("العدد (10) => ") or 10), int(input("الطول (16) => ") or 16))]),
        "2":  ("فحص تسريب كلمة مرور",      lambda: print(json.dumps(st.check_pwned(input("كلمة المرور => ")), indent=2))),
        "3":  ("تحليل نمط كلمة مرور",      lambda: print(json.dumps(st.analyze_password_pattern(input("كلمة المرور => ")), indent=2, ensure_ascii=False))),
        "4":  ("كسر Caesar Brute Force",   lambda: [print(f"  {r['shift']:>2}: {r['text']}") for r in st.caesar_brute(input("النص المشفر => "))]),
        "5":  ("تشفير Vigenere",           lambda: print(st.vigenere_encrypt(input("النص => "), input("المفتاح => ")))),
        "6":  ("فك Vigenere",              lambda: print(st.vigenere_decrypt(input("النص => "), input("المفتاح => ")))),
        "7":  ("إخفاء نص (Steganography)", lambda: print(repr(st.steganography_hide(input("النص المخفي => "), input("النص الحامل => "))))),
        "8":  ("كشف نص مخفي",             lambda: print(st.steganography_reveal(input("النص => ")))),
        "9":  ("فك JWT",                   lambda: print(json.dumps(st.jwt_decode(input("JWT Token => ")), indent=2, ensure_ascii=False))),
        "10": ("توليد Token آمن",          lambda: print(st.generate_secure_token(int(input("الطول (32) => ") or 32), input("الصيغة (hex/base64/uuid) => ") or "hex"))),
        "11": ("فحص ثغرات المنافذ",        lambda: [print(f"  {r['port']:<6} {r['risk']}") for r in st.port_vulnerability_check(input("Host => "))]),
        "12": ("البحث عن أسرار في كود",    lambda: print(json.dumps(st.scan_for_secrets(input("المجلد => ")), indent=2, ensure_ascii=False))),
        "13": ("مقارنة ملفين بالهاش",      lambda: print(json.dumps(st.hash_file_verify(input("الملف 1 => "), input("الملف 2 => ")), indent=2))),
        "14": ("Brute Force ZIP",          lambda: print(st.brute_force_zip(input("ملف ZIP => "), input("قائمة الكلمات => ")))),
        "15": ("ملخص حزم الشبكة",          lambda: print(json.dumps(st.network_sniff_summary(input("واجهة (wlan0) => ") or "wlan0"), indent=2, ensure_ascii=False))),
    }
    while True:
        print("\n═"*45)
        print("  🔒  Security Toolkit — 15 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
