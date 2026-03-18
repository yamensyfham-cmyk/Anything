"""
أدوات Termux:API — تحكم كامل بالأندرويد بدون روت
يتطلب: تطبيق Termux:API من F-Droid + pkg install termux-api
مكاتب: stdlib فقط (subprocess, json)
"""
import subprocess
import json
import os
import sys

def _run(cmd: list, timeout=15) -> dict:
    """تنفيذ أمر termux وإرجاع النتيجة"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        stdout = result.stdout.strip()
        if stdout:
            try:
                return {"ok": True, "data": json.loads(stdout)}
            except json.JSONDecodeError:
                return {"ok": True, "data": stdout}
        if result.returncode == 0:
            return {"ok": True, "data": "تم التنفيذ بنجاح."}
        return {"ok": False, "error": result.stderr.strip() or "فشل الأمر."}
    except FileNotFoundError:
        return {"ok": False, "error": "termux-api غير مثبت. نفّذ: pkg install termux-api"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "انتهت مهلة الأمر."}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class SMSTools:
    @staticmethod
    def list_sms(limit=20, box="inbox"):
        """قراءة الرسائل (inbox/sent/draft)"""
        r = _run(["termux-sms-list", "-l", str(limit), "-b", box])
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def send_sms(number: str, message: str):
        """إرسال رسالة نصية"""
        r = _run(["termux-sms-send", "-n", number, message])
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def search_sms(keyword: str, box="inbox"):
        """البحث في الرسائل"""
        messages = SMSTools.list_sms(limit=100, box=box)
        if isinstance(messages, str):
            return messages
        return [m for m in messages if keyword.lower() in str(m).lower()]

class NotificationTools:
    @staticmethod
    def send(title: str, content: str, priority="default", vibrate=True):
        """إرسال إشعار"""
        cmd = ["termux-notification",
               "--title", title,
               "--content", content,
               "--priority", priority]
        if vibrate:
            cmd += ["--vibrate", "500,100,200"]
        r = _run(cmd)
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def send_with_button(title: str, content: str, btn_text: str, btn_action: str):
        """إشعار مع زر قابل للنقر"""
        cmd = ["termux-notification",
               "--title", title,
               "--content", content,
               "--button1", btn_text,
               "--button1-action", btn_action]
        r = _run(cmd)
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def remove_all():
        r = _run(["termux-notification-remove", "all"])
        return r["data"] if r["ok"] else r["error"]

class DeviceInfo:
    @staticmethod
    def battery():
        """معلومات البطارية"""
        r = _run(["termux-battery-status"])
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def device_info():
        """معلومات الجهاز"""
        r = _run(["termux-telephony-deviceinfo"])
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def call_log(limit=10):
        """سجل المكالمات"""
        r = _run(["termux-call-log", "-l", str(limit)])
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def contacts():
        """قائمة جهات الاتصال من الهاتف"""
        r = _run(["termux-contact-list"])
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def vibrate(ms=500):
        """اهتزاز الجهاز"""
        r = _run(["termux-vibrate", "-d", str(ms)])
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def torch(on=True):
        """تشغيل/إيقاف الفلاش"""
        r = _run(["termux-torch", "on" if on else "off"])
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def volume(stream="music", volume=50):
        """ضبط الصوت (music/ring/alarm/notification)"""
        r = _run(["termux-volume", stream, str(volume)])
        return r["data"] if r["ok"] else r["error"]

class LocationTools:
    @staticmethod
    def get_location(provider="gps"):
        """الحصول على الموقع (gps/network/passive)"""
        r = _run(["termux-location", "-p", provider], timeout=30)
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def format_location():
        """موقع مُنسَّق مع خرائط Google"""
        loc = LocationTools.get_location()
        if isinstance(loc, dict) and "latitude" in loc:
            lat = loc["latitude"]
            lng = loc["longitude"]
            link = f"https://maps.google.com/?q={lat},{lng}"
            return {
                "latitude":  lat,
                "longitude": lng,
                "accuracy":  loc.get("accuracy", "N/A"),
                "maps_link": link
            }
        return loc

class CameraTools:
    @staticmethod
    def list_cameras():
        r = _run(["termux-camera-info"])
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def take_photo(output_path="photo.jpg", camera_id=0):
        """التقاط صورة"""
        r = _run(["termux-camera-photo", "-c", str(camera_id), output_path])
        if r["ok"] and os.path.exists(output_path):
            size = os.path.getsize(output_path)
            return f"تم التقاط الصورة: {output_path} ({size/1024:.1f} KB)"
        return r.get("error", "فشل التقاط الصورة.")

class ClipboardTools:
    @staticmethod
    def get():
        r = _run(["termux-clipboard-get"])
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def set(text: str):
        r = _run(["termux-clipboard-set", text])
        return r["data"] if r["ok"] else r["error"]

class WifiTools:
    @staticmethod
    def scan():
        """مسح شبكات WiFi المتاحة"""
        r = _run(["termux-wifi-scaninfo"])
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def connection_info():
        """معلومات الاتصال الحالي"""
        r = _run(["termux-wifi-connectioninfo"])
        return r["data"] if r["ok"] else r["error"]

    @staticmethod
    def find_networks_by_security():
        """تصنيف الشبكات حسب نوع التشفير"""
        networks = WifiTools.scan()
        if not isinstance(networks, list):
            return networks
        result = {"open": [], "WEP": [], "WPA": [], "WPA2": [], "other": []}
        for n in networks:
            cap = n.get("capabilities", "").upper()
            ssid = n.get("SSID", "Hidden")
            if not cap or cap == "[]":
                result["open"].append(ssid)
            elif "WPA2" in cap:
                result["WPA2"].append(ssid)
            elif "WPA" in cap:
                result["WPA"].append(ssid)
            elif "WEP" in cap:
                result["WEP"].append(ssid)
            else:
                result["other"].append(ssid)
        return result

if __name__ == "__main__":
    menu = {
        "1": ("SMS - قراءة",          lambda: print(json.dumps(SMSTools.list_sms(), indent=2, ensure_ascii=False, default=str))),
        "2": ("SMS - إرسال",          lambda: print(SMSTools.send_sms(input("الرقم => "), input("الرسالة => ")))),
        "3": ("إشعار",               lambda: print(NotificationTools.send(input("العنوان => "), input("المحتوى => ")))),
        "4": ("البطارية",            lambda: print(json.dumps(DeviceInfo.battery(), indent=2, ensure_ascii=False))),
        "5": ("الموقع",              lambda: print(json.dumps(LocationTools.format_location(), indent=2, ensure_ascii=False))),
        "6": ("التقاط صورة",         lambda: print(CameraTools.take_photo(input("اسم الملف (photo.jpg) => ") or "photo.jpg"))),
        "7": ("الحافظة - قراءة",     lambda: print(ClipboardTools.get())),
        "8": ("الحافظة - كتابة",     lambda: print(ClipboardTools.set(input("النص => ")))),
        "9": ("WiFi - مسح",          lambda: print(json.dumps(WifiTools.find_networks_by_security(), indent=2, ensure_ascii=False))),
        "10":("WiFi - اتصال حالي",   lambda: print(json.dumps(WifiTools.connection_info(), indent=2, ensure_ascii=False))),
        "11":("مصباح الفلاش",        lambda: print(DeviceInfo.torch(input("تشغيل؟ (نعم/لا) => ").strip() != "لا"))),
        "12":("اهتزاز",              lambda: print(DeviceInfo.vibrate(int(input("مدة (ms) => ") or 500)))),
        "13":("الصوت",               lambda: print(DeviceInfo.volume(input("النوع (music/ring/alarm) => ") or "music", int(input("المستوى 0-100 => ") or 50)))),
        "14":("جهات اتصال الهاتف",   lambda: print(json.dumps(DeviceInfo.contacts(), indent=2, ensure_ascii=False))),
        "15":("سجل المكالمات",       lambda: print(json.dumps(DeviceInfo.call_log(), indent=2, ensure_ascii=False))),
    }
    while True:
        print("\n" + "═"*45)
        print("  📱  Termux API Tools")
        print("═"*45)
        for k, (label, _) in menu.items():
            print(f"  {k:>2}. {label}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except KeyboardInterrupt: pass
            except Exception as e: print(f"خطأ: {e}")
        else:
            print("اختيار غير صالح.")
