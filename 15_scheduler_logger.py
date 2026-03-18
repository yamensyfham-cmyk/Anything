"""
جدولة المهام + نظام السجلات
مكاتب: stdlib فقط (threading, logging)
"""
import threading
import time
import logging
import sys
import os
import json
from datetime import datetime

class Scheduler:
    def __init__(self):
        self.tasks    = {}
        self._running = False
        self._lock    = threading.Lock()

    def add(self, name: str, interval_sec: int, func, *args, **kwargs) -> str:
        with self._lock:
            self.tasks[name] = {
                "interval":  interval_sec,
                "func":      func,
                "args":      args,
                "kwargs":    kwargs,
                "last_run":  0,
                "runs":      0,
                "enabled":   True,
            }
        return f"✅ مهمة '{name}' مضافة (كل {interval_sec}ث)"

    def remove(self, name: str) -> str:
        with self._lock:
            if name in self.tasks:
                del self.tasks[name]
                return f"✅ حُذفت '{name}'"
        return "❌ المهمة غير موجودة."

    def enable(self, name: str, enabled=True) -> str:
        with self._lock:
            if name in self.tasks:
                self.tasks[name]["enabled"] = enabled
                return f"✅ '{name}' {'مفعّلة' if enabled else 'معطّلة'}"
        return "❌ غير موجودة."

    def run_once(self):
        now = time.time()
        with self._lock:
            tasks = list(self.tasks.items())
        for name, t in tasks:
            if not t["enabled"]: continue
            if now - t["last_run"] >= t["interval"]:
                try:
                    t["func"](*t["args"], **t["kwargs"])
                    t["runs"] += 1
                except Exception as e:
                    print(f"[Scheduler] خطأ في '{name}': {e}")
                t["last_run"] = now

    def start(self) -> str:
        if self._running: return "الجدولة تعمل مسبقاً."
        self._running = True
        def _loop():
            while self._running:
                self.run_once()
                time.sleep(1)
        threading.Thread(target=_loop, daemon=True, name="Scheduler").start()
        return "✅ بدأت الجدولة في الخلفية."

    def stop(self) -> str:
        self._running = False
        return "⏹ توقفت الجدولة."

    def status(self) -> list:
        with self._lock:
            return [{"name":n,"interval":t["interval"],"runs":t["runs"],"enabled":t["enabled"]}
                    for n, t in self.tasks.items()]

class Logger:
    def __init__(self, log_file="uas.log", level=logging.DEBUG):
        self.log_file = log_file
        self.logger   = logging.getLogger("UAS")
        self.logger.setLevel(level)
        if not self.logger.handlers:
            fmt = logging.Formatter('[%(asctime)s] %(levelname)-8s %(message)s', datefmt='%H:%M:%S')

            fh = logging.FileHandler(log_file, encoding='utf-8')
            fh.setFormatter(fmt)
            fh.setLevel(logging.DEBUG)

            ch = logging.StreamHandler(sys.stdout)
            ch.setFormatter(fmt)
            ch.setLevel(logging.INFO)
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

    def info(self, msg):    self.logger.info(msg)
    def warning(self, msg): self.logger.warning(msg)
    def error(self, msg):   self.logger.error(msg)
    def debug(self, msg):   self.logger.debug(msg)

    def tail(self, lines=20) -> str:
        if not os.path.exists(self.log_file): return "لا يوجد ملف سجل."
        with open(self.log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        return "".join(all_lines[-lines:])

    def search_log(self, keyword: str) -> list:
        if not os.path.exists(self.log_file): return []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            return [l.strip() for l in f if keyword.lower() in l.lower()]

    def clear(self) -> str:
        open(self.log_file, 'w').close()
        return "✅ تم مسح السجل."

if __name__ == "__main__":
    logger = Logger()
    sched  = Scheduler()

    def sample_task():
        logger.info("المهمة التجريبية تعمل!")

    sched.add("sample", 5, sample_task)
    sched.start()
    logger.info("تم تشغيل الجدولة")

    while True:
        print("\n1-حالة المهام  2-إضافة مهمة  3-إيقاف مهمة  4-عرض السجل  5-بحث سجل  0-خروج")
        ch = input("=> ").strip()
        if ch == "0": sched.stop(); break
        elif ch == "1": print(json.dumps(sched.status(), indent=2, ensure_ascii=False))
        elif ch == "2":
            name = input("اسم المهمة => ").strip()
            ivl  = int(input("كل كم ثانية => ") or 10)
            sched.add(name, ivl, lambda: logger.info(f"مهمة: {name}"))
            print(f"✅ تمت الإضافة")
        elif ch == "3":
            name = input("اسم المهمة => ").strip()
            print(sched.enable(name, False))
        elif ch == "4": print(logger.tail(30))
        elif ch == "5":
            kw = input("كلمة البحث => ").strip()
            for line in logger.search_log(kw): print(f"  {line}")
