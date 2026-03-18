"""
فاحص الثغرات + مستخرج البيانات من الويب
مكاتب: stdlib فقط (urllib, re)
"""
import urllib.request
import urllib.parse
import re
import json

def _get(url, method="GET", timeout=8) -> tuple:
    """إرجاع (status_code, text, headers)"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', errors='ignore'), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, "", {}
    except Exception as e:
        return 0, "", {"error": str(e)}

class WebScanner:

    XSS_PAYLOADS = [
        "<script>alert(1)</script>",
        '"><img src=x onerror=alert(1)>',
        "';alert(1)//",
    ]
    SQLI_PAYLOADS = ["'", "\"", "' OR '1'='1", "' OR 1=1--", "1; DROP TABLE users--"]
    SQLI_ERRORS   = ["sql syntax","mysql_fetch","ora-","quoted string","you have an error in your sql","warning: mysql","unclosed quotation"]

    @staticmethod
    def scan_xss(url: str) -> str:
        for p in WebScanner.XSS_PAYLOADS:
            test_url = url + urllib.parse.quote(p)
            _, body, _ = _get(test_url)
            if p.lower() in body.lower() or "alert" in body.lower():
                return f"⚠️ XSS محتمل! Payload: {p}"
        return "✅ لا علامات XSS."

    @staticmethod
    def scan_sqli(url: str) -> str:
        for p in WebScanner.SQLI_PAYLOADS:
            test_url = url + urllib.parse.quote(p)
            _, body, _ = _get(test_url)
            for err in WebScanner.SQLI_ERRORS:
                if err in body.lower():
                    return f"⚠️ SQL Injection محتمل! Sign: {err}"
        return "✅ لا علامات SQLi."

    @staticmethod
    def check_security_headers(url: str) -> dict:
        _, _, headers = _get(url)
        important = ["X-Frame-Options","X-XSS-Protection","Content-Security-Policy",
                     "Strict-Transport-Security","X-Content-Type-Options","Referrer-Policy"]
        return {h: headers.get(h, "❌ غير موجود") for h in important}

    @staticmethod
    def check_ssl(host: str) -> dict:
        import ssl
        try:
            ctx = ssl.create_default_context()
            conn = ctx.wrap_socket(socket_module.socket(), server_hostname=host)
            conn.settimeout(5)
            conn.connect((host, 443))
            cert = conn.getpeercert()
            conn.close()
            return {
                "subject":  dict(x[0] for x in cert.get("subject", [])),
                "issuer":   dict(x[0] for x in cert.get("issuer", [])),
                "expires":  cert.get("notAfter", "N/A"),
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def full_scan(url: str) -> dict:
        return {
            "XSS":             WebScanner.scan_xss(url),
            "SQLi":            WebScanner.scan_sqli(url),
            "Security Headers":WebScanner.check_security_headers(url),
        }

import socket as socket_module

class WebScraper:

    @staticmethod
    def extract(url: str) -> dict:
        _, body, _ = _get(url)
        links  = list(set(re.findall(r'href=["\']?(https?://[^\s"\'<>]+)', body)))
        emails = list(set(re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', body)))
        phones = list(set(re.findall(r'[\+]?[\d\s\-\(\)]{9,15}', body)))

        titles = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', body, re.I|re.S)
        titles = [re.sub(r'<[^>]+>','',t).strip() for t in titles]
        return {
            "links":   links[:30],
            "emails":  emails,
            "phones":  [p.strip() for p in phones if len(re.sub(r'\D','',p)) >= 9][:20],
            "headings": titles[:10],
        }

    @staticmethod
    def download_text(url: str, save_path: str) -> str:
        """تحميل محتوى صفحة كنص"""
        _, body, _ = _get(url)
        clean = re.sub(r'<[^>]+>', ' ', body)
        clean = re.sub(r'\s+', ' ', clean).strip()
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(clean)
        return f"✅ محفوظ: {save_path} ({len(clean)} حرف)"

    @staticmethod
    def batch_extract(urls: list) -> list:
        results = []
        for url in urls:
            data = WebScraper.extract(url)
            data["url"] = url
            results.append(data)
        return results

if __name__ == "__main__":
    menu = {
        "1": ("فحص XSS",           lambda: print(WebScanner.scan_xss(input("URL => ").strip()))),
        "2": ("فحص SQLi",           lambda: print(WebScanner.scan_sqli(input("URL => ").strip()))),
        "3": ("Security Headers",   lambda: print(json.dumps(WebScanner.check_security_headers(input("URL => ").strip()), indent=2))),
        "4": ("فحص شامل",           lambda: print(json.dumps(WebScanner.full_scan(input("URL => ").strip()), indent=2, ensure_ascii=False))),
        "5": ("استخراج روابط/إيميلات", lambda: print(json.dumps(WebScraper.extract(input("URL => ").strip()), indent=2, ensure_ascii=False))),
        "6": ("تحميل نص الصفحة",    lambda: print(WebScraper.download_text(input("URL => ").strip(), input("ملف الحفظ => ").strip() or "page.txt"))),
    }
    while True:
        print("\n" + "═"*40)
        print("  🔒  Web Scanner / Scraper")
        print("═"*40)
        for k, (l, _) in menu.items(): print(f"  {k}. {l}")
        print("  0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"خطأ: {e}")
