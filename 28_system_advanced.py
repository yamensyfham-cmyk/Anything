"""
أدوات النظام المتقدمة — 20 ميزة
مكاتب: stdlib فقط
"""
import os, sys, subprocess, json, time, threading, shutil, platform
import hashlib, glob, re, sqlite3
from datetime import datetime
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

class SystemAdvanced:

    @staticmethod
    def full_info() -> dict:
        info = {
            "platform":   platform.system(),
            "release":    platform.release(),
            "machine":    platform.machine(),
            "python":     platform.python_version(),
            "hostname":   platform.node(),
        }
        try:
            info["cpu_cores"] = os.cpu_count()
            info["cpu_arch"]  = platform.processor() or platform.machine()
        except Exception: pass

        for prop in ["ro.product.model","ro.build.version.release","ro.product.brand"]:
            try:
                r = subprocess.run(["getprop",prop], capture_output=True, text=True, timeout=3)
                if r.stdout.strip(): info[prop] = r.stdout.strip()
            except Exception: pass
        return info

    @staticmethod
    def memory_detail() -> dict:
        try:
            m = {}
            for line in open('/proc/meminfo').readlines():
                parts = line.split()
                if len(parts)>=2: m[parts[0].rstrip(':')] = int(parts[1])
            gb = 1024**2
            return {
                "MemTotal":     f"{m.get('MemTotal',0)/gb:.2f} GB",
                "MemAvailable": f"{m.get('MemAvailable',0)/gb:.2f} GB",
                "MemUsed":      f"{(m.get('MemTotal',0)-m.get('MemAvailable',0))/gb:.2f} GB",
                "SwapTotal":    f"{m.get('SwapTotal',0)/gb:.2f} GB",
                "SwapFree":     f"{m.get('SwapFree',0)/gb:.2f} GB",
                "Cached":       f"{m.get('Cached',0)/gb:.2f} GB",
                "Buffers":      f"{m.get('Buffers',0)/gb:.2f} GB",
            }
        except Exception: return {"error": "تعذر قراءة /proc/meminfo"}

    @staticmethod
    def cpu_detail() -> dict:
        try:
            info = {}
            for line in open('/proc/cpuinfo').readlines():
                if ':' in line:
                    k,v = line.split(':',1)
                    info[k.strip()] = v.strip()
            return {
                "model":    info.get("model name", info.get("Hardware","Unknown")),
                "cores":    os.cpu_count(),
                "governor": SystemAdvanced._read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"),
                "max_freq": SystemAdvanced._read("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq"),
                "cur_freq": SystemAdvanced._read("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"),
            }
        except Exception as e: return {"error": str(e)}

    @staticmethod
    def _read(path):
        try: return open(path).read().strip()
        except Exception: return "N/A"

    @staticmethod
    def storage_detail() -> list:
        result = []
        try:
            r = subprocess.run(["df","-h"], capture_output=True, text=True)
            lines = r.stdout.strip().split('\n')[1:]
            for line in lines:
                parts = line.split()
                if len(parts)>=6:
                    result.append({"filesystem":parts[0],"size":parts[1],"used":parts[2],
                                   "avail":parts[3],"use%":parts[4],"mount":parts[5]})
        except Exception: pass
        return result

    @staticmethod
    def temperature() -> dict:
        temps = {}
        thermal_dir = "/sys/class/thermal"
        if os.path.exists(thermal_dir):
            for zone in os.listdir(thermal_dir):
                if zone.startswith("thermal_zone"):
                    try:
                        temp = int(open(f"{thermal_dir}/{zone}/temp").read()) / 1000
                        type_ = open(f"{thermal_dir}/{zone}/type").read().strip()
                        temps[type_] = f"{temp:.1f}°C"
                    except Exception: pass
        return temps or {"error": "بيانات الحرارة غير متاحة"}

    @staticmethod
    def live_monitor(interval=3):
        """مراقبة مستمرة للنظام"""
        import shutil as sh
        def _cpu_pct():
            try:
                line = open('/proc/stat').readline()
                vals = list(map(int, line.split()[1:]))
                return vals[3], sum(vals)
            except Exception: return 0, 1

        i1,t1 = _cpu_pct()
        try:
            while True:
                time.sleep(interval)
                i2,t2 = _cpu_pct()
                dt = t2-t1; di = i2-i1
                cpu = (1-di/dt)*100 if dt else 0
                i1,t1 = i2,t2

                mem = {}
                try:
                    for line in open('/proc/meminfo'):
                        p = line.split()
                        if len(p)>=2: mem[p[0].rstrip(':')] = int(p[1])
                except Exception: pass
                ram_pct = (1-mem.get('MemAvailable',0)/mem.get('MemTotal',1))*100

                disk = sh.disk_usage('/')
                disk_pct = disk.used/disk.total*100

                os.system('clear')
                print(f"{'─'*40}")
                print(f"  📊 Live Monitor — {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'─'*40}")
                bar = lambda p: "█"*int(p/5) + "░"*(20-int(p/5))
                print(f"  CPU  [{bar(cpu)}] {cpu:.1f}%")
                print(f"  RAM  [{bar(ram_pct)}] {ram_pct:.1f}%")
                print(f"  Disk [{bar(disk_pct)}] {disk_pct:.1f}%")
                print(f"\n  [Ctrl+C للإيقاف]")
        except KeyboardInterrupt: pass

    @staticmethod
    def process_tree() -> str:
        try:
            r = subprocess.run(["pstree", "-p"], capture_output=True, text=True)
            return r.stdout if r.returncode==0 else "❌ pstree غير متاح"
        except FileNotFoundError:
            return "❌ pstree غير مثبت"

    @staticmethod
    def find_memory_hogs(top=10) -> list:
        """أكثر العمليات استهلاكاً للذاكرة"""
        procs = []
        total = 0
        try:
            for line in open('/proc/meminfo'):
                if 'MemTotal' in line: total = int(line.split()[1])
        except Exception: pass

        for pid_str in os.listdir('/proc'):
            if not pid_str.isdigit(): continue
            try:
                name   = open(f'/proc/{pid_str}/comm').read().strip()
                status = open(f'/proc/{pid_str}/status').read()
                vmrss  = next((int(l.split()[1]) for l in status.split('\n') if 'VmRSS:' in l), 0)
                procs.append({"pid":int(pid_str),"name":name,"rss_kb":vmrss,
                              "pct":round(vmrss/total*100,2) if total else 0})
            except Exception: pass
        return sorted(procs, key=lambda x:-x["rss_kb"])[:top]

    @staticmethod
    def kill_by_name(name: str) -> str:
        import signal
        killed = 0
        for pid_str in os.listdir('/proc'):
            if not pid_str.isdigit(): continue
            try:
                pname = open(f'/proc/{pid_str}/comm').read().strip()
                if name.lower() in pname.lower():
                    os.kill(int(pid_str), signal.SIGTERM)
                    killed += 1
            except Exception: pass
        return f"✅ أُنهيت {killed} عملية"

    @staticmethod
    def largest_files(folder="/", count=20, min_mb=10) -> list:
        """أكبر الملفات في النظام"""
        files = []
        for root, _, fnames in os.walk(folder):
            for fname in fnames:
                path = os.path.join(root, fname)
                try:
                    size = os.path.getsize(path)
                    if size >= min_mb*1024*1024:
                        files.append({"path":path,"size_mb":round(size/1024/1024,1)})
                except Exception: pass
        return sorted(files, key=lambda x:-x["size_mb"])[:count]

    @staticmethod
    def old_files(folder="/sdcard", days=30) -> list:
        """ملفات لم تُستخدم منذ مدة"""
        threshold = time.time() - days*86400
        old = []
        for root, _, files in os.walk(folder):
            for f in files:
                path = os.path.join(root, f)
                try:
                    atime = os.path.getatime(path)
                    if atime < threshold:
                        old.append({"path":path,"days":round((time.time()-atime)/86400)})
                except Exception: pass
        return sorted(old, key=lambda x:-x["days"])[:50]

    @staticmethod
    def clean_empty_dirs(folder: str) -> int:
        count = 0
        for root, dirs, files in os.walk(folder, topdown=False):
            for d in dirs:
                path = os.path.join(root, d)
                try:
                    if not os.listdir(path):
                        os.rmdir(path); count += 1
                except Exception: pass
        return count

    @staticmethod
    def integrity_check(folder: str, manifest_path="manifest.json", create=False) -> dict:
        """تحقق من سلامة الملفات"""
        if create:
            manifest = {}
            for root, _, files in os.walk(folder):
                for f in files:
                    path = os.path.join(root, f)
                    try:
                        h = hashlib.sha256(open(path,'rb').read()).hexdigest()
                        manifest[os.path.relpath(path,folder)] = h
                    except Exception: pass
            json.dump(manifest, open(manifest_path,'w'), indent=2)
            return {"created": len(manifest), "manifest": manifest_path}
        else:
            try: manifest = json.load(open(manifest_path))
            except Exception: return {"error": "لا يوجد manifest"}
            changed = []; missing = []
            for rel, expected in manifest.items():
                path = os.path.join(folder, rel)
                if not os.path.exists(path): missing.append(rel); continue
                actual = hashlib.sha256(open(path,'rb').read()).hexdigest()
                if actual != expected: changed.append(rel)
            return {"changed":changed,"missing":missing,
                    "ok": len(manifest)-len(changed)-len(missing)}

    @staticmethod
    def auto_backup(src: str, dest: str, compress=True) -> str:
        ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = os.path.join(dest, f"backup_{os.path.basename(src)}_{ts}")
        os.makedirs(dest, exist_ok=True)
        if compress:
            shutil.make_archive(out, 'zip', src)
            return f"✅ {out}.zip ({os.path.getsize(out+'.zip')/1024/1024:.1f} MB)"
        else:
            shutil.copytree(src, out)
            return f"✅ {out}"

if __name__ == "__main__":
    sa = SystemAdvanced()
    menu = {
        "1":  ("معلومات النظام الكاملة",    lambda: print(json.dumps(sa.full_info(), indent=2, ensure_ascii=False))),
        "2":  ("تفاصيل الذاكرة",            lambda: print(json.dumps(sa.memory_detail(), indent=2, ensure_ascii=False))),
        "3":  ("تفاصيل المعالج",            lambda: print(json.dumps(sa.cpu_detail(), indent=2, ensure_ascii=False))),
        "4":  ("تفاصيل التخزين",            lambda: [print(f"  {s['filesystem']:<25} {s['size']:>6} {s['use%']:>5} {s['mount']}") for s in sa.storage_detail()]),
        "5":  ("درجات الحرارة",             lambda: print(json.dumps(sa.temperature(), indent=2, ensure_ascii=False))),
        "6":  ("مراقبة مستمرة",            lambda: sa.live_monitor()),
        "7":  ("أكثر العمليات ذاكرة",       lambda: [print(f"  {p['pid']:<7} {p['name']:<25} {p['rss_kb']/1024:.1f} MB ({p['pct']}%)") for p in sa.find_memory_hogs()]),
        "8":  ("إنهاء عمليات باسم",         lambda: print(sa.kill_by_name(input("اسم العملية => ")))),
        "9":  ("أكبر الملفات",              lambda: [print(f"  {f['size_mb']:>8.1f} MB  {f['path']}") for f in sa.largest_files(input("المجلد (/) => ") or "/", int(input("العدد (20) => ") or 20), int(input("الحد الأدنى MB (10) => ") or 10))]),
        "10": ("ملفات قديمة",              lambda: [print(f"  {f['days']}يوم  {f['path']}") for f in sa.old_files(input("المجلد => ") or "/sdcard", int(input("الأيام (30) => ") or 30))]),
        "11": ("حذف مجلدات فارغة",         lambda: print(f"✅ حُذف {sa.clean_empty_dirs(input('المجلد => '))} مجلد")),
        "12": ("نسخ احتياطي تلقائي",        lambda: print(sa.auto_backup(input("المصدر => "), input("الوجهة => ")))),
        "13": ("إنشاء Manifest للملفات",    lambda: print(json.dumps(sa.integrity_check(input("المجلد => "), create=True), indent=2))),
        "14": ("التحقق من سلامة الملفات",   lambda: print(json.dumps(sa.integrity_check(input("المجلد => "), input("Manifest path => ") or "manifest.json"), indent=2, ensure_ascii=False))),
    }
    while True:
        print("\n═"*45)
        print("  🖥  System Advanced — 14 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
