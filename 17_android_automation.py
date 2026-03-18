"""
أتمتة أندرويد — ردود تلقائية، نصوص مجدولة، مهام متكررة
يعمل بالكامل بدون روت عبر Termux:API + ADB
مكاتب: stdlib فقط
"""
import subprocess
import json
import time
import os
import threading
import re

def _termux(cmd: list, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = r.stdout.strip()
        return json.loads(out) if out and out.startswith(("{","[")) else out
    except Exception as e:
        return f"خطأ: {e}"

def _adb(cmd: list, timeout=20):
    try:
        r = subprocess.run(["adb"] + cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception as e:
        return f"خطأ ADB: {e}"

class SMSAutoReply:
    """
    يراقب الرسائل الجديدة ويرد تلقائياً حسب القواعد
    يتطلب: termux-api
    """
    def __init__(self):
        self.rules    = {}
        self.seen_ids = set()
        self._running = False

    def add_rule(self, keyword: str, reply: str):
        self.rules[keyword.lower()] = reply
        return f"✅ قاعدة: '{keyword}' → '{reply}'"

    def remove_rule(self, keyword: str):
        self.rules.pop(keyword.lower(), None)
        return f"✅ حُذفت قاعدة '{keyword}'"

    def list_rules(self):
        return self.rules

    def _check_and_reply(self):
        msgs = _termux(["termux-sms-list", "-l", "5", "-b", "inbox"])
        if not isinstance(msgs, list): return
        for msg in msgs:
            msg_id = msg.get("_id") or msg.get("date","")
            if msg_id in self.seen_ids: continue
            self.seen_ids.add(msg_id)
            body   = msg.get("body", "").lower()
            sender = msg.get("address", "")
            for kw, reply in self.rules.items():
                if kw in body:
                    result = _termux(["termux-sms-send", "-n", sender, reply])
                    print(f"[AutoReply] → {sender}: {reply}")
                    break

    def start(self, interval=30):
        self._running = True
        def _loop():

            msgs = _termux(["termux-sms-list", "-l", "20", "-b", "inbox"])
            if isinstance(msgs, list):
                for m in msgs:
                    self.seen_ids.add(m.get("_id") or m.get("date",""))
            print(f"[AutoReply] يعمل — يفحص كل {interval}ث")
            while self._running:
                try: self._check_and_reply()
                except Exception as e: print(f"[AutoReply] خطأ: {e}")
                time.sleep(interval)
        threading.Thread(target=_loop, daemon=True).start()
        return "✅ بدأ مراقب الرد التلقائي."

    def stop(self):
        self._running = False
        return "⏹ توقف."

class BatteryMonitor:
    """
    يراقب البطارية ويرسل إشعار عند مستوى معين
    """
    def __init__(self):
        self._running = False

    @staticmethod
    def get_level() -> int:
        data = _termux(["termux-battery-status"])
        if isinstance(data, dict):
            return data.get("percentage", -1)
        return -1

    def watch(self, low=20, high=90, interval=120):
        """
        low  = أرسل إشعار عند نزول تحت X%
        high = أرسل إشعار عند الوصول لـ X%
        """
        self._running = True
        last_notif    = {"low": False, "high": False}

        def _loop():
            while self._running:
                lvl = BatteryMonitor.get_level()
                if lvl < 0:
                    time.sleep(interval); continue

                if lvl <= low and not last_notif["low"]:
                    _termux(["termux-notification",
                              "--title", f"🔋 بطارية منخفضة: {lvl}%",
                              "--content", "يرجى شحن الجهاز",
                              "--vibrate", "500,100,500"])
                    last_notif["low"] = True
                elif lvl > low + 5:
                    last_notif["low"] = False

                if lvl >= high and not last_notif["high"]:
                    _termux(["termux-notification",
                              "--title", f"🔋 البطارية {lvl}% — شحن كافٍ",
                              "--content", "يمكنك فصل الشاحن"])
                    last_notif["high"] = True
                elif lvl < high - 5:
                    last_notif["high"] = False

                print(f"[Battery] {lvl}%")
                time.sleep(interval)

        threading.Thread(target=_loop, daemon=True).start()
        return f"✅ مراقبة البطارية: تنبيه عند <{low}% أو >{high}%"

    def stop(self): self._running = False; return "⏹ توقف."

class GPSLogger:
    def __init__(self, log_file="gps_track.json"):
        self.log_file = log_file
        self.track    = []
        self._running = False

    def start(self, interval=60):
        self._running = True
        def _loop():
            while self._running:
                try:
                    r = subprocess.run(
                        ["termux-location", "-p", "network", "-r", "once"],
                        capture_output=True, text=True, timeout=30
                    )
                    data = json.loads(r.stdout.strip())
                    point = {
                        "lat":      data.get("latitude"),
                        "lng":      data.get("longitude"),
                        "accuracy": data.get("accuracy"),
                        "time":     time.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    self.track.append(point)
                    self._save()
                    print(f"[GPS] {point['lat']:.5f}, {point['lng']:.5f} ±{point['accuracy']}m")
                except Exception as e:
                    print(f"[GPS] خطأ: {e}")
                time.sleep(interval)
        threading.Thread(target=_loop, daemon=True).start()
        return f"✅ GPS Logger بدأ — كل {interval}ث → {self.log_file}"

    def stop(self): self._running = False; return "⏹ توقف GPS Logger."

    def _save(self):
        with open(self.log_file, 'w') as f:
            json.dump(self.track, f, indent=2)

    def export_kml(self, out="track.kml"):
        """تصدير المسار كـ KML لـ Google Earth"""
        coords = "\n".join(f"{p['lng']},{p['lat']},0" for p in self.track)
        kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document><Placemark><name>GPS Track</name>
<LineString><coordinates>{coords}</coordinates></LineString>
</Placemark></Document></kml>"""
        with open(out, 'w') as f: f.write(kml)
        return f"✅ KML محفوظ: {out} ({len(self.track)} نقطة)"

    def maps_link(self):
        if not self.track: return "لا توجد نقاط."
        last = self.track[-1]
        return f"https://maps.google.com/?q={last['lat']},{last['lng']}"

class AndroidMacro:
    """
    سيناريوهات تلقائية عبر ADB WiFi بدون روت
    """
    def __init__(self):
        self.steps = []

    def tap(self, x, y, delay=0.5):       self.steps.append(("tap",x,y,delay));          return self
    def swipe(self, x1,y1,x2,y2,ms=300,delay=0.5): self.steps.append(("swipe",x1,y1,x2,y2,ms,delay)); return self
    def text(self, t, delay=0.5):         self.steps.append(("text",t,delay));            return self
    def key(self, k, delay=0.5):          self.steps.append(("key",k,delay));             return self
    def wait(self, s):                    self.steps.append(("wait",s));                  return self
    def screenshot(self, path, delay=0.5):self.steps.append(("ss",path,delay));           return self
    def open_app(self, pkg, delay=1.5):   self.steps.append(("app",pkg,delay));           return self
    def notification(self, title, msg):   self.steps.append(("notif",title,msg));         return self

    def run(self, repeat=1):
        for i in range(repeat):
            if repeat > 1: print(f"\n▶ تكرار {i+1}/{repeat}")
            for step in self.steps:
                action = step[0]
                try:
                    if action == "tap":
                        _, x, y, d = step
                        _adb(["shell","input","tap",str(x),str(y)])
                        print(f"  👆 tap({x},{y})")
                    elif action == "swipe":
                        _, x1,y1,x2,y2,ms,d = step
                        _adb(["shell","input","swipe",str(x1),str(y1),str(x2),str(y2),str(ms)])
                        print(f"  👆 swipe({x1},{y1}→{x2},{y2})")
                    elif action == "text":
                        _, t, d = step
                        _adb(["shell","input","text",t.replace(" ","%s")])
                        print(f"  ⌨  text('{t}')")
                    elif action == "key":
                        _, k, d = step
                        _adb(["shell","input","keyevent",f"KEYCODE_{k.upper()}"])
                        print(f"  🔑 key({k})")
                    elif action == "wait":
                        _, s = step
                        print(f"  ⏳ انتظار {s}ث")
                        time.sleep(s); d = 0
                    elif action == "ss":
                        _, path, d = step
                        _adb(["shell","screencap","-p","/sdcard/_ss.png"])
                        _adb(["pull","/sdcard/_ss.png", path])
                        print(f"  📸 screenshot → {path}")
                    elif action == "app":
                        _, pkg, d = step
                        _adb(["shell","monkey","-p",pkg,"-c","android.intent.category.LAUNCHER","1"])
                        print(f"  📱 فتح {pkg}")
                    elif action == "notif":
                        _, title, msg = step
                        _termux(["termux-notification","--title",title,"--content",msg])
                        print(f"  🔔 إشعار: {title}")
                        d = 0
                    else:
                        d = 0
                    if d: time.sleep(d)
                except Exception as e:
                    print(f"  ❌ {e}")

    def clear(self): self.steps = []; return self
    def save(self, path):
        data = []
        for s in self.steps:
            data.append(list(s))
        with open(path,'w') as f: json.dump(data, f, indent=2)
        return f"✅ Macro محفوظ: {path}"

    @classmethod
    def load(cls, path):
        m = cls()
        with open(path) as f:
            m.steps = [tuple(s) for s in json.load(f)]
        return m

if __name__ == "__main__":
    import json

    sms_bot = SMSAutoReply()
    bat_mon = BatteryMonitor()
    gps_log = GPSLogger()

    menu = {
        "1": ("SMS رد تلقائي — إضافة قاعدة", lambda: print(sms_bot.add_rule(input("الكلمة => "), input("الرد => ")))),
        "2": ("SMS رد تلقائي — تشغيل",        lambda: print(sms_bot.start(int(input("الفحص كل (30ث) => ") or 30)))),
        "3": ("SMS رد تلقائي — إيقاف",        lambda: print(sms_bot.stop())),
        "4": ("SMS قواعد الرد",               lambda: print(json.dumps(sms_bot.list_rules(), indent=2, ensure_ascii=False))),
        "5": ("مراقب البطارية — تشغيل",       lambda: print(bat_mon.watch(
                                                    int(input("تنبيه عند نزول لـ% (20) => ") or 20),
                                                    int(input("تنبيه عند وصول لـ% (90) => ") or 90),
                                                ))),
        "6": ("GPS Logger — تشغيل",           lambda: print(gps_log.start(int(input("الفاصل (60ث) => ") or 60)))),
        "7": ("GPS Logger — إيقاف + تصدير",   lambda: (print(gps_log.stop()), print(gps_log.export_kml()), print(gps_log.maps_link()))),
        "8": ("Macro ADB — مثال جاهز",        _demo_macro),
    }

    def _demo_macro():
        macro = AndroidMacro()
        print("مثال: ضغط هوم + انتظار + لقطة شاشة")
        macro.key("HOME").wait(1).screenshot("demo.png").run()

    while True:
        print("\n═"*45)
        print("  ⚡  Android Automation")
        print("═"*45)
        for k, (l, _) in menu.items(): print(f"  {k}. {l}")
        print("  0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"خطأ: {e}")
