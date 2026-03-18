"""
مدير المهام — بديل psutil بـ /proc
مكاتب: stdlib فقط
"""
import os
import signal
import time

class TaskManager:

    @staticmethod
    def list_processes(sort_by="memory") -> list:
        procs = []
        total_ram = TaskManager._total_ram_kb()
        for pid_str in os.listdir('/proc'):
            if not pid_str.isdigit(): continue
            pid = int(pid_str)
            try:
                name = open(f'/proc/{pid}/comm').read().strip()
                stat = os.stat(f'/proc/{pid}')
                try:
                    import pwd; user = pwd.getpwuid(stat.st_uid).pw_name
                except Exception: user = str(stat.st_uid)

                mem_kb = 0
                for line in open(f'/proc/{pid}/status').readlines():
                    if line.startswith('VmRSS:'):
                        mem_kb = int(line.split()[1]); break
                mem_pct = round(mem_kb / total_ram * 100, 2) if total_ram else 0

                cmdline = open(f'/proc/{pid}/cmdline').read().replace('\x00',' ').strip()[:60]

                procs.append({"pid": pid, "name": name, "user": user,
                               "mem_pct": mem_pct, "mem_kb": mem_kb, "cmd": cmdline})
            except (PermissionError, FileNotFoundError, ProcessLookupError):
                pass

        key = {"memory": lambda x: -x["mem_kb"],
               "pid":    lambda x:  x["pid"],
               "name":   lambda x:  x["name"]}.get(sort_by, lambda x: -x["mem_kb"])
        return sorted(procs, key=key)

    @staticmethod
    def kill_process(pid: int) -> str:
        if not os.path.exists(f'/proc/{pid}'):
            return f"❌ العملية {pid} غير موجودة."
        try:
            os.kill(pid, signal.SIGTERM)
            return f"✅ تم إنهاء العملية {pid}."
        except PermissionError:
            return f"❌ لا يوجد إذن لإنهاء {pid}."
        except ProcessLookupError:
            return f"❌ العملية {pid} غير موجودة."

    @staticmethod
    def find_process(name: str) -> list:
        return [p for p in TaskManager.list_processes() if name.lower() in p["name"].lower()]

    @staticmethod
    def _total_ram_kb() -> int:
        try:
            for line in open('/proc/meminfo').readlines():
                if line.startswith('MemTotal:'):
                    return int(line.split()[1])
        except Exception: pass
        return 0

if __name__ == "__main__":
    tm = TaskManager()
    while True:
        print("\n1- عرض العمليات  2- بحث  3- إنهاء عملية  0- خروج")
        ch = input("=> ").strip()
        if ch == "0": break
        elif ch == "1":
            procs = tm.list_processes()[:25]
            print(f"{'PID':<7} {'الاسم':<22} {'المستخدم':<14} {'RAM%':<7}")
            print("─"*55)
            for p in procs:
                print(f"{p['pid']:<7} {p['name']:<22} {p['user']:<14} {p['mem_pct']:<7}")
        elif ch == "2":
            name = input("اسم => ").strip()
            for p in tm.find_process(name):
                print(f"  PID:{p['pid']} {p['name']} [{p['cmd']}]")
        elif ch == "3":
            try: print(tm.kill_process(int(input("PID => "))))
            except ValueError: print("PID غير صالح.")
