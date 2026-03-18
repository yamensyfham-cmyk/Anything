"""
أدوات OSINT وفحص الشبكة
مكاتب: stdlib فقط (socket, urllib)
"""
import socket
import json
import urllib.request
import urllib.parse
import re
import os

def _get_json(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

class OSINTTools:

    @staticmethod
    def ip_info(ip: str) -> dict:
        return _get_json(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,lat,lon,query,timezone")

    @staticmethod
    def my_ip_info() -> dict:
        return OSINTTools.ip_info("")

    @staticmethod
    def port_scan(host: str, ports=None, timeout=0.5) -> list:
        if ports is None:
            ports = [21,22,23,25,53,80,110,143,443,3306,5432,6379,8080,8443,27017]
        open_ports = []
        for p in ports:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            if s.connect_ex((host, p)) == 0:
                try: svc = socket.getservbyport(p)
                except Exception: svc = "?"
                open_ports.append({"port": p, "service": svc})
            s.close()
        return open_ports

    @staticmethod
    def dns_lookup(domain: str) -> dict:
        try:
            ips = socket.getaddrinfo(domain, None)
            return {"domain": domain, "ips": list(set(i[4][0] for i in ips))}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def reverse_dns(ip: str) -> str:
        try: return socket.gethostbyaddr(ip)[0]
        except Exception as e: return str(e)

    @staticmethod
    def whois(domain: str) -> str:
        try:
            result = _get_json(f"https://api.hackertarget.com/whois/?q={domain}")
            return result if isinstance(result, str) else json.dumps(result)
        except Exception as e: return str(e)

    @staticmethod
    def headers(url: str) -> dict:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                return dict(r.headers)
        except Exception as e: return {"error": str(e)}

    @staticmethod
    def subdomains_check(domain: str, wordlist=None) -> list:
        """فحص subdomain شائعة"""
        if wordlist is None:
            wordlist = ["www","mail","ftp","api","admin","dev","test","staging",
                        "app","portal","vpn","remote","shop","blog","m","mobile"]
        found = []
        for sub in wordlist:
            target = f"{sub}.{domain}"
            try:
                ip = socket.gethostbyname(target)
                found.append({"subdomain": target, "ip": ip})
            except Exception: pass
        return found

if __name__ == "__main__":
    menu = {
        "1": ("معلومات IP",        lambda: print(json.dumps(OSINTTools.ip_info(input("IP => ").strip()), indent=2, ensure_ascii=False))),
        "2": ("IP الخاص بي",       lambda: print(json.dumps(OSINTTools.my_ip_info(), indent=2, ensure_ascii=False))),
        "3": ("فحص المنافذ",       lambda: [print(f"  ✅ {r['port']}/{r['service']}") for r in OSINTTools.port_scan(input("الهدف => ").strip())]),
        "4": ("DNS Lookup",         lambda: print(json.dumps(OSINTTools.dns_lookup(input("النطاق => ").strip()), indent=2))),
        "5": ("Reverse DNS",        lambda: print(OSINTTools.reverse_dns(input("IP => ").strip()))),
        "6": ("HTTP Headers",       lambda: print(json.dumps(OSINTTools.headers(input("URL => ").strip()), indent=2))),
        "7": ("Subdomain فحص",      lambda: print(json.dumps(OSINTTools.subdomains_check(input("النطاق => ").strip()), indent=2, ensure_ascii=False))),
    }
    while True:
        print("\n" + "═"*40)
        print("  🔍  OSINT Tools")
        print("═"*40)
        for k, (l, _) in menu.items(): print(f"  {k}. {l}")
        print("  0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"خطأ: {e}")
