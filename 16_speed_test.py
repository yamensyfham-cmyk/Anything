"""
اختبار سرعة الإنترنت
مكاتب: stdlib فقط (urllib, time, socket)
يعمل بدون روت وبدون speedtest-cli
"""
import urllib.request
import time
import socket
import json
import threading

class SpeedTest:

    TEST_SERVERS = [
        ("Cloudflare",    "https://speed.cloudflare.com/__down?bytes=10000000"),
        ("Fast.com CDN",  "https://api.fast.com/netflix/speedtest/v2?https=true&token=YXNkZmFzZGxmbnNkYWZoYXNk"),
        ("GitHub",        "https://github.githubassets.com/assets/app-icon-512-6b0064b6c5ba.png"),
    ]

    PING_HOSTS = [
        ("Cloudflare DNS", "1.1.1.1",    53),
        ("Google DNS",     "8.8.8.8",    53),
        ("OpenDNS",        "208.67.222.222", 53),
    ]

    @staticmethod
    def ping(host: str, port=53, count=5) -> dict:
        times = []
        for _ in range(count):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                t0 = time.time()
                s.connect((host, port))
                t1 = time.time()
                s.close()
                times.append((t1 - t0) * 1000)
            except Exception:
                pass
        if not times:
            return {"host": host, "min": None, "avg": None, "max": None, "loss": "100%"}
        return {
            "host": host,
            "min":  f"{min(times):.1f}ms",
            "avg":  f"{sum(times)/len(times):.1f}ms",
            "max":  f"{max(times):.1f}ms",
            "loss": f"{(count-len(times))/count*100:.0f}%",
        }

    @staticmethod
    def ping_all() -> list:
        results = []
        for name, host, port in SpeedTest.PING_HOSTS:
            r = SpeedTest.ping(host, port)
            r["name"] = name
            results.append(r)
        return results

    @staticmethod
    def download_speed(url: str, timeout=15) -> dict:
        """قياس سرعة التحميل"""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            t0  = time.time()
            downloaded = 0
            with urllib.request.urlopen(req, timeout=timeout) as r:
                while True:
                    chunk = r.read(65536)
                    if not chunk: break
                    downloaded += len(chunk)
                    elapsed = time.time() - t0
                    if elapsed >= 8:
                        break
            elapsed = time.time() - t0
            if elapsed == 0: return {"error": "لم يُحمَّل أي شيء"}
            speed_kbs   = downloaded / elapsed / 1024
            speed_mbps  = speed_kbs / 1024 * 8
            return {
                "downloaded":  f"{downloaded/1024/1024:.2f} MB",
                "time":        f"{elapsed:.1f}s",
                "speed_KBs":   f"{speed_kbs:.0f} KB/s",
                "speed_Mbps":  f"{speed_mbps:.2f} Mbps",
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def upload_speed(host="httpbin.org", size_kb=512) -> dict:
        """قياس سرعة الرفع"""
        try:
            data = os.urandom(size_kb * 1024)
            req  = urllib.request.Request(
                "https://httpbin.org/post",
                data=data,
                headers={"Content-Type": "application/octet-stream",
                         "User-Agent": "Mozilla/5.0"}
            )
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=20) as r:
                r.read()
            elapsed = time.time() - t0
            speed_kbs  = size_kb / elapsed
            speed_mbps = speed_kbs / 1024 * 8
            return {
                "uploaded":   f"{size_kb} KB",
                "time":       f"{elapsed:.1f}s",
                "speed_KBs":  f"{speed_kbs:.0f} KB/s",
                "speed_Mbps": f"{speed_mbps:.2f} Mbps",
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def full_test() -> dict:
        print("⏳ قياس Ping...")
        pings = SpeedTest.ping_all()
        best_ping = min((r for r in pings if r.get("avg")),
                        key=lambda x: float(x["avg"].replace("ms","")), default=pings[0])

        print("⬇  قياس سرعة التحميل...")
        dl = SpeedTest.download_speed(SpeedTest.TEST_SERVERS[0][1])

        print("⬆  قياس سرعة الرفع...")
        ul = SpeedTest.upload_speed()

        return {
            "ping":     best_ping,
            "download": dl,
            "upload":   ul,
            "all_pings": pings,
        }

import os

if __name__ == "__main__":
    menu = {
        "1": ("قياس كامل",        lambda: print(json.dumps(SpeedTest.full_test(),     indent=2, ensure_ascii=False))),
        "2": ("Ping فقط",         lambda: print(json.dumps(SpeedTest.ping_all(),      indent=2, ensure_ascii=False))),
        "3": ("سرعة التحميل",     lambda: print(json.dumps(SpeedTest.download_speed(SpeedTest.TEST_SERVERS[0][1]), indent=2))),
        "4": ("ping مخصص",        lambda: print(json.dumps(SpeedTest.ping(input("IP/Host => ").strip()), indent=2))),
    }
    while True:
        print("\n═"*40)
        print("  ⚡  Speed Test")
        print("═"*40)
        for k, (l, _) in menu.items(): print(f"  {k}. {l}")
        print("  0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except KeyboardInterrupt: pass
