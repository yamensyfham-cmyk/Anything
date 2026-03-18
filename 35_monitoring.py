"""
نظام المراقبة والتنبيهات — 20 ميزة
مكاتب: stdlib فقط
"""
import os, sys, json, time, threading, socket, sqlite3, subprocess
import urllib.request, urllib.parse
from datetime import datetime
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

MONITOR_DB = os.path.join(BASE_DIR, "monitor.db")

def _db():
    conn = sqlite3.connect(MONITOR_DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY, type TEXT, target TEXT, message TEXT,
        level TEXT, timestamp TEXT, resolved INTEGER DEFAULT 0)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS checks (
        id INTEGER PRIMARY KEY, name TEXT, type TEXT, target TEXT,
        config TEXT, enabled INTEGER DEFAULT 1, last_check TEXT,
        last_status TEXT, failures INTEGER DEFAULT 0)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY, name TEXT, value REAL,
        unit TEXT, timestamp TEXT)""")
    conn.commit()
    return conn

def _add_alert(type_, target, message, level="warning"):
    with _db() as db:
        db.execute("INSERT INTO alerts (type,target,message,level,timestamp) VALUES (?,?,?,?,?)",
                   (type_,target,message,level,datetime.now().isoformat()))

def _add_metric(name, value, unit=""):
    with _db() as db:
        db.execute("INSERT INTO metrics (name,value,unit,timestamp) VALUES (?,?,?,?)",
                   (name,value,unit,datetime.now().isoformat()))

def _notify(message: str):
    """إرسال إشعار Termux"""
    try:
        subprocess.run(["termux-notification","--title","⚠ UAS Monitor","--content",message,
                       "--vibrate","300,100,300"], timeout=5)
    except Exception: pass
    print(f"\n🔔 ALERT: {message}")

class MonitoringSystem:

    @staticmethod
    def check_url(url: str, timeout=10) -> dict:
        t0 = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"UAS-Monitor/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return {"url":url,"status":r.status,"ms":round((time.time()-t0)*1000),"up":True}
        except Exception as e:
            return {"url":url,"status":0,"ms":round((time.time()-t0)*1000),"up":False,"error":str(e)[:50]}

    @staticmethod
    def check_port(host: str, port: int, timeout=3) -> dict:
        t0 = time.time()
        s  = socket.socket()
        s.settimeout(timeout)
        result = s.connect_ex((host,port))
        s.close()
        return {"host":host,"port":port,"open":result==0,"ms":round((time.time()-t0)*1000)}

    @staticmethod
    def check_ssl_expiry(host: str, days_warn=30) -> dict:
        import ssl
        try:
            ctx  = ssl.create_default_context()
            conn = ctx.wrap_socket(socket.socket(), server_hostname=host)
            conn.settimeout(10)
            conn.connect((host,443))
            cert = conn.getpeercert()
            conn.close()
            expiry = datetime.strptime(cert['notAfter'],'%b %d %H:%M:%S %Y %Z')
            days   = (expiry - datetime.now()).days
            return {"host":host,"expires":str(expiry)[:10],"days_left":days,
                    "warning":days<days_warn,"expired":days<0}
        except Exception as e: return {"error":str(e)}

    @staticmethod
    def check_dns(domain: str) -> dict:
        t0 = time.time()
        try:
            ip = socket.gethostbyname(domain)
            return {"domain":domain,"ip":ip,"ms":round((time.time()-t0)*1000),"ok":True}
        except Exception as e:
            return {"domain":domain,"error":str(e),"ok":False}

    @staticmethod
    def system_health() -> dict:
        import shutil
        health = {"timestamp":datetime.now().strftime("%H:%M:%S")}

        try:
            line = open('/proc/stat').readline()
            vals = list(map(int,line.split()[1:]))
            health["cpu_percent"] = round((1-vals[3]/sum(vals))*100,1)
        except Exception: health["cpu_percent"] = -1

        try:
            m = {}
            for line in open('/proc/meminfo'):
                p=line.split()
                if len(p)>=2: m[p[0].rstrip(':')]=int(p[1])
            health["ram_percent"] = round((1-m.get('MemAvailable',0)/m.get('MemTotal',1))*100,1)
            health["ram_free_mb"] = round(m.get('MemAvailable',0)/1024,0)
        except Exception: health["ram_percent"] = -1

        try:
            u = shutil.disk_usage('/')
            health["disk_percent"] = round(u.used/u.total*100,1)
            health["disk_free_gb"] = round(u.free/1024**3,2)
        except Exception: health["disk_percent"] = -1

        try:
            bat = subprocess.run(["termux-battery-status"],capture_output=True,text=True,timeout=5)
            if bat.returncode == 0:
                data = json.loads(bat.stdout)
                health["battery"] = data.get("percentage",-1)
        except Exception: pass
        return health

    @staticmethod
    def collect_metrics(duration=60, interval=5) -> list:
        """جمع مقاييس لفترة"""
        metrics = []
        end = time.time() + duration
        while time.time() < end:
            h = MonitoringSystem.system_health()
            metrics.append(h)
            _add_metric("cpu", h.get("cpu_percent",0), "%")
            _add_metric("ram", h.get("ram_percent",0), "%")
            time.sleep(interval)
        return metrics

    @staticmethod
    def watch_urls(urls: list, interval=60, alert_threshold=3):
        """مراقبة URLs وإرسال تنبيه عند الفشل"""
        failures = {url:0 for url in urls}
        print(f"👀 مراقبة {len(urls)} URL — Ctrl+C للإيقاف")
        try:
            while True:
                for url in urls:
                    result = MonitoringSystem.check_url(url)
                    if not result["up"]:
                        failures[url] += 1
                        if failures[url] >= alert_threshold:
                            _add_alert("url_down",url,f"URL فشل {failures[url]} مرات")
                            _notify(f"🔴 {url} غير متاح!")
                    else:
                        if failures[url] >= alert_threshold:
                            _notify(f"🟢 {url} عاد للعمل!")
                        failures[url] = 0
                    status = "✅" if result["up"] else "❌"
                    print(f"  {status} {url[:50]} [{result.get('status',0)}] {result['ms']}ms")
                print(f"  ─── {datetime.now().strftime('%H:%M:%S')} ───")
                time.sleep(interval)
        except KeyboardInterrupt: pass

    @staticmethod
    def watch_system(cpu_threshold=80, ram_threshold=85, disk_threshold=90, interval=30):
        """مراقبة موارد النظام"""
        print(f"📊 مراقبة النظام — Ctrl+C للإيقاف")
        try:
            while True:
                h = MonitoringSystem.system_health()
                print(f"  CPU:{h.get('cpu_percent',0):.1f}% RAM:{h.get('ram_percent',0):.1f}% "
                      f"Disk:{h.get('disk_percent',0):.1f}%")
                if h.get("cpu_percent",0) > cpu_threshold:
                    _notify(f"CPU مرتفع: {h['cpu_percent']}%")
                if h.get("ram_percent",0) > ram_threshold:
                    _notify(f"RAM مرتفع: {h['ram_percent']}%")
                if h.get("disk_percent",0) > disk_threshold:
                    _notify(f"Disk ممتلئ: {h['disk_percent']}%")
                time.sleep(interval)
        except KeyboardInterrupt: pass

    @staticmethod
    def watch_file(path: str, interval=10):
        """مراقبة تغيير ملف"""
        import hashlib
        def _hash(p):
            try: return hashlib.md5(open(p,'rb').read()).hexdigest()
            except Exception: return ""
        prev = _hash(path)
        print(f"👀 مراقبة {path} — Ctrl+C للإيقاف")
        try:
            while True:
                curr = _hash(path)
                if curr != prev and curr:
                    _notify(f"تغيّر الملف: {path}")
                    _add_alert("file_changed",path,"تغيّر محتوى الملف")
                    prev = curr
                time.sleep(interval)
        except KeyboardInterrupt: pass

    @staticmethod
    def watch_process(process_name: str, restart_cmd=None, interval=30):
        """مراقبة عملية وإعادة تشغيلها عند الإيقاف"""
        print(f"⚙ مراقبة {process_name} — Ctrl+C للإيقاف")
        try:
            while True:
                alive = False
                for pid in os.listdir('/proc'):
                    if pid.isdigit():
                        try:
                            if process_name.lower() in open(f'/proc/{pid}/comm').read().lower():
                                alive = True; break
                        except Exception: pass
                if not alive:
                    _notify(f"العملية {process_name} توقفت!")
                    _add_alert("process_down",process_name,"توقفت العملية")
                    if restart_cmd:
                        subprocess.Popen(restart_cmd.split())
                        print(f"  ↩ إعادة تشغيل...")
                else:
                    print(f"  ✅ {process_name} تعمل")
                time.sleep(interval)
        except KeyboardInterrupt: pass

    @staticmethod
    def get_alerts(limit=20, unresolved_only=False) -> list:
        with _db() as db:
            if unresolved_only:
                rows = db.execute("SELECT * FROM alerts WHERE resolved=0 ORDER BY timestamp DESC LIMIT ?",(limit,)).fetchall()
            else:
                rows = db.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?",(limit,)).fetchall()
        return [{"id":r[0],"type":r[1],"target":r[2],"message":r[3],"level":r[4],"time":r[5][:16]} for r in rows]

    @staticmethod
    def resolve_alert(alert_id: int) -> str:
        with _db() as db:
            db.execute("UPDATE alerts SET resolved=1 WHERE id=?",(alert_id,))
        return f"✅ تم حل التنبيه {alert_id}"

    @staticmethod
    def metrics_summary(name: str, hours=24) -> dict:
        from datetime import timedelta
        since = (datetime.now()-timedelta(hours=hours)).isoformat()
        with _db() as db:
            rows = db.execute("SELECT value FROM metrics WHERE name=? AND timestamp>?",
                              (name,since)).fetchall()
        values = [r[0] for r in rows]
        if not values: return {"name":name,"no_data":True}
        return {"name":name,"count":len(values),"avg":round(sum(values)/len(values),2),
                "min":round(min(values),2),"max":round(max(values),2)}

    @staticmethod
    def export_report(out="monitoring_report.json") -> str:
        report = {
            "generated":   datetime.now().isoformat(),
            "system_health": MonitoringSystem.system_health(),
            "alerts":      MonitoringSystem.get_alerts(50),
            "cpu_24h":     MonitoringSystem.metrics_summary("cpu"),
            "ram_24h":     MonitoringSystem.metrics_summary("ram"),
        }
        json.dump(report, open(out,'w',encoding='utf-8'), indent=2, ensure_ascii=False)
        return f"✅ {out}"

    @staticmethod
    def uptime_history(url: str, checks=10, interval=5) -> dict:
        """سجل uptime لـ URL"""
        results = []
        for i in range(checks):
            r = MonitoringSystem.check_url(url)
            results.append({"time":datetime.now().strftime("%H:%M:%S"),"up":r["up"],"ms":r.get("ms",0)})
            if i < checks-1: time.sleep(interval)
        up_count = sum(r["up"] for r in results)
        avg_ms   = sum(r["ms"] for r in results) / len(results)
        return {"url":url,"uptime":f"{up_count/checks*100:.0f}%","avg_ms":round(avg_ms),"history":results}

if __name__ == "__main__":
    ms = MonitoringSystem()
    menu = {
        "1":  ("فحص URL",                  lambda: print(json.dumps(ms.check_url(input("URL => ")), indent=2))),
        "2":  ("فحص منفذ",                 lambda: print(json.dumps(ms.check_port(input("Host => "), int(input("Port => "))), indent=2))),
        "3":  ("فحص SSL",                  lambda: print(json.dumps(ms.check_ssl_expiry(input("Host => ")), indent=2, ensure_ascii=False))),
        "4":  ("فحص DNS",                  lambda: print(json.dumps(ms.check_dns(input("Domain => ")), indent=2))),
        "5":  ("صحة النظام",               lambda: print(json.dumps(ms.system_health(), indent=2, ensure_ascii=False))),
        "6":  ("مراقبة URLs",              lambda: ms.watch_urls(input("URLs (مسافة) => ").split(), int(input("كل (60ث) => ") or 60))),
        "7":  ("مراقبة النظام",            lambda: ms.watch_system()),
        "8":  ("مراقبة ملف",              lambda: ms.watch_file(input("مسار الملف => "))),
        "9":  ("مراقبة عملية",            lambda: ms.watch_process(input("اسم العملية => "), input("أمر إعادة التشغيل (اختياري) => ") or None)),
        "10": ("جمع مقاييس",              lambda: ms.collect_metrics(int(input("المدة (60ث) => ") or 60), int(input("كل (5ث) => ") or 5))),
        "11": ("التنبيهات",               lambda: [print(f"  [{a['id']}] [{a['level']}] {a['time']} {a['type']}: {a['message']}") for a in ms.get_alerts()]),
        "12": ("حل تنبيه",               lambda: print(ms.resolve_alert(int(input("ID => "))))),
        "13": ("ملخص مقاييس",             lambda: print(json.dumps(ms.metrics_summary(input("الاسم (cpu/ram) => ")), indent=2))),
        "14": ("تصدير تقرير",             lambda: print(ms.export_report())),
        "15": ("سجل Uptime",              lambda: print(json.dumps(ms.uptime_history(input("URL => "), int(input("عدد الفحوصات (10) => ") or 10)), indent=2, ensure_ascii=False))),
    }
    while True:
        print("\n═"*45)
        print("  📡  Monitoring System — 15 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
