"""
مراقبة موارد النظام
مكاتب: stdlib فقط (shutil, /proc)
"""
import os
import shutil
import time
import json

class ResourceMonitor:

    @staticmethod
    def get_system_stats() -> dict:
        return {
            "CPU%":        ResourceMonitor.cpu_percent(),
            "RAM Total":   ResourceMonitor._ram("total"),
            "RAM Used":    ResourceMonitor._ram("used"),
            "RAM Free":    ResourceMonitor._ram("free"),
            "RAM%":        ResourceMonitor._ram("percent"),
            "Disk Total":  ResourceMonitor._disk("total"),
            "Disk Used":   ResourceMonitor._disk("used"),
            "Disk Free":   ResourceMonitor._disk("free"),
            "Disk%":       ResourceMonitor._disk("percent"),
            "Load Avg":    ResourceMonitor.load_avg(),
            "Uptime":      ResourceMonitor.uptime(),
        }

    @staticmethod
    def _cpu_times():
        try:
            line = open('/proc/stat').readline()
            vals = list(map(int, line.split()[1:]))
            return vals[3], sum(vals)
        except Exception: return 0, 1

    @staticmethod
    def cpu_percent(interval=0.5) -> str:
        i1, t1 = ResourceMonitor._cpu_times()
        time.sleep(interval)
        i2, t2 = ResourceMonitor._cpu_times()
        dt = t2 - t1
        if not dt: return "0.0%"
        return f"{(1 - (i2-i1)/dt)*100:.1f}%"

    @staticmethod
    def _meminfo() -> dict:
        m = {}
        try:
            for line in open('/proc/meminfo').readlines():
                p = line.split()
                if len(p) >= 2: m[p[0].rstrip(':')] = int(p[1])
        except Exception: pass
        return m

    @staticmethod
    def _ram(field) -> str:
        m   = ResourceMonitor._meminfo()
        tot = m.get('MemTotal', 0)
        avl = m.get('MemAvailable', m.get('MemFree', 0))
        use = tot - avl
        gb  = 1024**2
        if field == "total":   return f"{tot/gb:.2f} GB"
        if field == "used":    return f"{use/gb:.2f} GB"
        if field == "free":    return f"{avl/gb:.2f} GB"
        if field == "percent": return f"{use/tot*100:.1f}%" if tot else "N/A"
        return "N/A"

    @staticmethod
    def _disk(field) -> str:
        try:
            u   = shutil.disk_usage('/')
            gb  = 1024**3
            if field == "total":   return f"{u.total/gb:.2f} GB"
            if field == "used":    return f"{u.used/gb:.2f} GB"
            if field == "free":    return f"{u.free/gb:.2f} GB"
            if field == "percent": return f"{u.used/u.total*100:.1f}%" if u.total else "N/A"
        except Exception as e: return str(e)
        return "N/A"

    @staticmethod
    def load_avg() -> str:
        try:
            return open('/proc/loadavg').read().split()[:3]
        except Exception: return "N/A"

    @staticmethod
    def uptime() -> str:
        try:
            secs = float(open('/proc/uptime').read().split()[0])
            h, r = divmod(int(secs), 3600)
            m, s = divmod(r, 60)
            return f"{h}h {m}m {s}s"
        except Exception: return "N/A"

    @staticmethod
    def watch(interval=3, rounds=0):
        """مراقبة مستمرة (rounds=0 = لا نهائي)"""
        i = 0
        try:
            while rounds == 0 or i < rounds:
                os.system('clear')
                s = ResourceMonitor.get_system_stats()
                print("═"*40)
                print("  📊  System Monitor")
                print("═"*40)
                for k, v in s.items():
                    print(f"  {k:<15} {v}")
                print("\n  [Ctrl+C للإيقاف]")
                time.sleep(interval)
                i += 1
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    print("1- لقطة واحدة  |  2- مراقبة مستمرة")
    ch = input("=> ").strip()
    if ch == "1":
        print(json.dumps(ResourceMonitor.get_system_stats(), indent=2, ensure_ascii=False))
    elif ch == "2":
        ResourceMonitor.watch()
