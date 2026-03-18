"""
أدوات الشبكة المتقدمة — 25 ميزة
مكاتب: stdlib فقط + requests اختياري
"""
import os, sys, socket, subprocess, struct, time, threading, json, re
import urllib.request, urllib.parse
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

try:
    import requests as _req
    _REQ = True
except ImportError:
    _REQ = False

def _get(url, timeout=10):
    try:
        if _REQ: return _req.get(url, timeout=timeout, headers={"User-Agent":"Mozilla/5.0"})
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            class Resp:
                text = r.read().decode('utf-8','replace')
                status_code = r.status
                def json(self): return json.loads(self.text)
            return Resp()
    except Exception as e:
        class Err:
            text=""; status_code=0
            def json(self): return {}
            error = str(e)
        return Err()

class NetworkAdvanced:

    @staticmethod
    def full_port_scan(host: str, start=1, end=1024, timeout=0.3) -> list:
        """مسح شامل للمنافذ مع إخفاء الخدمة"""
        open_ports = []
        def scan(port):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                if s.connect_ex((host,port)) == 0:
                    try: svc = socket.getservbyport(port)
                    except Exception: svc = "?"
                    banner = ""
                    try:
                        s.send(b'HEAD / HTTP/1.0\r\n\r\n')
                        banner = s.recv(64).decode('utf-8','replace').split('\n')[0][:50]
                    except Exception: pass
                    open_ports.append({"port":port,"service":svc,"banner":banner})
                s.close()
            except Exception: pass

        threads = []
        for port in range(start, end+1):
            t = threading.Thread(target=scan, args=(port,))
            threads.append(t); t.start()
            if len(threads) >= 100:
                for t in threads: t.join()
                threads = []
        for t in threads: t.join()
        return sorted(open_ports, key=lambda x: x["port"])

    @staticmethod
    def udp_scan(host: str, ports=None) -> list:
        """فحص UDP"""
        if ports is None: ports = [53,67,68,69,123,161,162,514]
        open_ports = []
        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(2)
                s.sendto(b'\x00', (host, port))
                s.recvfrom(1024)
                open_ports.append(port)
                s.close()
            except socket.timeout:
                open_ports.append(port)
            except Exception: pass
        return open_ports

    @staticmethod
    def scan_lan(subnet="192.168.1") -> list:
        """فحص كل أجهزة الـ LAN"""
        live = []
        def ping_host(ip):
            ret = os.system(f"ping -c 1 -W 1 {ip} > /dev/null 2>&1")
            if ret == 0:
                try: host = socket.gethostbyaddr(ip)[0]
                except Exception: host = ""
                live.append({"ip":ip, "hostname":host})

        threads = []
        for i in range(1, 255):
            ip = f"{subnet}.{i}"
            t  = threading.Thread(target=ping_host, args=(ip,))
            threads.append(t); t.start()
        for t in threads: t.join()
        return sorted(live, key=lambda x: int(x["ip"].split(".")[-1]))

    @staticmethod
    def my_network_info() -> dict:
        """معلومات شبكة الجهاز الحالي"""
        info = {}

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info["local_ip"] = s.getsockname()[0]
            s.close()
        except Exception: info["local_ip"] = "N/A"

        info["hostname"] = socket.gethostname()

        info["interfaces"] = {}
        try:
            for iface in os.listdir("/sys/class/net"):
                mac_path = f"/sys/class/net/{iface}/address"
                rx_path  = f"/sys/class/net/{iface}/statistics/rx_bytes"
                try:
                    mac = open(mac_path).read().strip()
                    rx  = int(open(rx_path).read().strip())
                    info["interfaces"][iface] = {"mac":mac, "rx_mb": round(rx/1024/1024,2)}
                except Exception: pass
        except Exception: pass
        return info

    @staticmethod
    def http_request(method: str, url: str, headers=None, body=None, timeout=15) -> dict:
        """طلب HTTP مخصص"""
        try:
            req = urllib.request.Request(url, method=method.upper(),
                                         headers=headers or {"User-Agent":"Mozilla/5.0"},
                                         data=body.encode() if body else None)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return {
                    "status":   r.status,
                    "headers":  dict(r.headers),
                    "body":     r.read(4096).decode('utf-8','replace'),
                }
        except urllib.request.HTTPError as e:
            return {"status": e.code, "error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def check_sites(urls: list) -> list:
        """فحص حالة مواقع متعددة"""
        results = []
        for url in urls:
            t0 = time.time()
            try:
                req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    results.append({"url":url,"status":r.status,"ms":round((time.time()-t0)*1000),"up":True})
            except Exception as e:
                results.append({"url":url,"status":0,"ms":round((time.time()-t0)*1000),"up":False,"error":str(e)[:50]})
        return results

    @staticmethod
    def ssl_info(host: str, port=443) -> dict:
        """معلومات شهادة SSL"""
        import ssl
        try:
            ctx  = ssl.create_default_context()
            conn = ctx.wrap_socket(socket.socket(), server_hostname=host)
            conn.settimeout(10)
            conn.connect((host, port))
            cert = conn.getpeercert()
            conn.close()
            return {
                "subject":  dict(x[0] for x in cert.get("subject",[])),
                "issuer":   dict(x[0] for x in cert.get("issuer",[])),
                "valid_from":  cert.get("notBefore",""),
                "valid_until": cert.get("notAfter",""),
                "san":      cert.get("subjectAltName",[]),
            }
        except Exception as e: return {"error":str(e)}

    @staticmethod
    def trace_route(host: str, max_hops=20) -> list:
        """Traceroute بسيط"""
        result = []
        try:
            output = subprocess.run(
                ["traceroute", "-m", str(max_hops), host],
                capture_output=True, text=True, timeout=60
            )
            for line in output.stdout.split('\n')[1:]:
                if line.strip(): result.append(line.strip())
        except FileNotFoundError:
            try:
                output = subprocess.run(
                    ["tracepath", host],
                    capture_output=True, text=True, timeout=60
                )
                result = output.stdout.strip().split('\n')
            except Exception as e:
                result = [f"❌ {e}"]
        return result

    @staticmethod
    def dns_records(domain: str) -> dict:
        """استعلام سجلات DNS عبر DoH (DNS over HTTPS)"""
        records = {}
        types   = ["A","AAAA","MX","NS","TXT","CNAME","SOA"]
        for rtype in types:
            try:
                url = f"https://dns.google/resolve?name={domain}&type={rtype}"
                data = json.loads(urllib.request.urlopen(url, timeout=5).read())
                answers = data.get("Answer",[])
                records[rtype] = [a.get("data","") for a in answers]
            except Exception:
                records[rtype] = []
        return {k:v for k,v in records.items() if v}

    @staticmethod
    def check_blacklist(ip: str) -> dict:
        """التحقق من قوائم الحظر الشائعة"""
        bl_zones = [
            "zen.spamhaus.org","bl.spamcop.net",
            "dnsbl.sorbs.net","b.barracudacentral.org"
        ]
        rev_ip = '.'.join(reversed(ip.split('.')))
        results = {}
        for bl in bl_zones:
            try:
                socket.gethostbyname(f"{rev_ip}.{bl}")
                results[bl] = "🚫 محظور"
            except socket.gaierror:
                results[bl] = "✅ نظيف"
        return results

    @staticmethod
    def bandwidth_monitor(iface="wlan0", duration=10) -> dict:
        """قياس استهلاك البيانات خلال فترة"""
        def _read(iface):
            rx_path = f"/sys/class/net/{iface}/statistics/rx_bytes"
            tx_path = f"/sys/class/net/{iface}/statistics/tx_bytes"
            try: return int(open(rx_path).read()), int(open(tx_path).read())
            except Exception: return 0, 0

        rx1,tx1 = _read(iface)
        time.sleep(duration)
        rx2,tx2 = _read(iface)
        return {
            "interface": iface,
            "duration_s": duration,
            "downloaded": f"{(rx2-rx1)/1024:.1f} KB",
            "uploaded":   f"{(tx2-tx1)/1024:.1f} KB",
            "dl_speed":   f"{(rx2-rx1)/duration/1024:.1f} KB/s",
            "ul_speed":   f"{(tx2-tx1)/duration/1024:.1f} KB/s",
        }

    @staticmethod
    def port_knock(host: str, ports: list) -> str:
        """Port Knocking — طرق متسلسلة على منافذ"""
        for port in ports:
            try:
                s = socket.socket()
                s.settimeout(0.5)
                s.connect_ex((host, port))
                s.close()
                time.sleep(0.1)
            except Exception: pass
        return f"✅ Knock على {len(ports)} منفذ"

    @staticmethod
    def simple_http_server(port=8080, folder=".") -> str:
        """سيرفر HTTP بسيط"""
        import http.server
        os.chdir(folder)
        handler = http.server.SimpleHTTPRequestHandler
        httpd   = http.server.HTTPServer(("0.0.0.0", port), handler)
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        return f"✅ سيرفر يعمل على http://0.0.0.0:{port} | Ctrl+C للإيقاف"

    @staticmethod
    def network_calculator(ip: str, cidr: int) -> dict:
        """حاسبة الشبكة"""
        try:
            import ipaddress
            net = ipaddress.IPv4Network(f"{ip}/{cidr}", strict=False)
            return {
                "network":   str(net.network_address),
                "broadcast": str(net.broadcast_address),
                "netmask":   str(net.netmask),
                "hosts":     net.num_addresses - 2,
                "first_host":str(list(net.hosts())[0]) if net.num_addresses > 2 else "N/A",
                "last_host": str(list(net.hosts())[-1]) if net.num_addresses > 2 else "N/A",
            }
        except Exception as e: return {"error":str(e)}

    @staticmethod
    def email_lookup(email: str) -> dict:
        """التحقق من صحة ونطاق بريد إلكتروني"""
        if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email):
            return {"valid": False, "error": "صيغة غير صحيحة"}
        domain = email.split('@')[1]
        info = {"email": email, "domain": domain, "valid": True}
        try:
            info["ip"] = socket.gethostbyname(domain)
            info["mx"] = NetworkAdvanced.dns_records(domain).get("MX",[])
        except Exception: info["domain_reachable"] = False
        return info

    @staticmethod
    def mac_vendor(mac: str) -> str:
        """معرفة الشركة المصنعة من MAC Address"""
        try:
            mac_clean = mac.upper().replace(':','').replace('-','')[:6]
            url = f"https://api.macvendors.com/{mac}"
            return urllib.request.urlopen(url, timeout=5).read().decode()
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def ip_geolocation_bulk(ips: list) -> list:
        """معلومات جغرافية لقائمة IPs"""
        results = []
        for ip in ips:
            try:
                data = json.loads(urllib.request.urlopen(f"http://ip-api.com/json/{ip}",timeout=5).read())
                results.append({"ip":ip,"country":data.get("country",""),"city":data.get("city",""),"isp":data.get("isp","")})
            except Exception:
                results.append({"ip":ip,"error":"فشل"})
        return results

if __name__ == "__main__":
    na = NetworkAdvanced()
    menu = {
        "1":  ("مسح منافذ شامل",         lambda: [print(f"  ✅ {p['port']}/{p['service']} {p['banner']}") for p in na.full_port_scan(input("Host => "), int(input("من (1) => ") or 1), int(input("إلى (1024) => ") or 1024))]),
        "2":  ("فحص UDP",               lambda: print(na.udp_scan(input("Host => ")))),
        "3":  ("مسح LAN",               lambda: [print(f"  {h['ip']:<18} {h['hostname']}") for h in na.scan_lan(input("Subnet (192.168.1) => ") or "192.168.1")]),
        "4":  ("معلومات الشبكة",         lambda: print(json.dumps(na.my_network_info(), indent=2, ensure_ascii=False))),
        "5":  ("طلب HTTP مخصص",          lambda: print(json.dumps(na.http_request(input("Method (GET) => ") or "GET", input("URL => ")), indent=2))),
        "6":  ("فحص حالة مواقع",         lambda: [print(f"  {'✅' if r['up'] else '❌'} {r['url']} [{r['status']}] {r['ms']}ms") for r in na.check_sites(input("URLs (مسافة) => ").split())]),
        "7":  ("SSL Certificate",       lambda: print(json.dumps(na.ssl_info(input("Host => ")), indent=2, ensure_ascii=False))),
        "8":  ("Traceroute",            lambda: [print(f"  {h}") for h in na.trace_route(input("Host => "))]),
        "9":  ("سجلات DNS",             lambda: print(json.dumps(na.dns_records(input("Domain => ")), indent=2))),
        "10": ("فحص Blacklist",         lambda: print(json.dumps(na.check_blacklist(input("IP => ")), indent=2, ensure_ascii=False))),
        "11": ("مراقبة البيانات",        lambda: print(json.dumps(na.bandwidth_monitor(input("واجهة (wlan0) => ") or "wlan0", int(input("مدة (10ث) => ") or 10)), indent=2))),
        "12": ("حاسبة الشبكة",          lambda: print(json.dumps(na.network_calculator(input("IP => "), int(input("CIDR (24) => ") or 24)), indent=2))),
        "13": ("فحص بريد إلكتروني",     lambda: print(json.dumps(na.email_lookup(input("البريد => ")), indent=2, ensure_ascii=False))),
        "14": ("MAC Vendor",            lambda: print(na.mac_vendor(input("MAC => ")))),
        "15": ("GeoIP متعدد",           lambda: print(json.dumps(na.ip_geolocation_bulk(input("IPs (مسافة) => ").split()), indent=2, ensure_ascii=False))),
        "16": ("سيرفر HTTP بسيط",       lambda: print(na.simple_http_server(int(input("Port (8080) => ") or 8080), input("المجلد (.) => ") or "."))),
    }
    while True:
        print("\n═"*45)
        print("  🌐  Network Advanced — 16 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
