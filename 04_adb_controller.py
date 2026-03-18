"""
ADB WiFi Controller — تحكم كامل بالأندرويد بدون روت
يتطلب: pkg install android-tools  (يثبت adb)
الجهاز يجب أن يكون في نفس الشبكة مع تفعيل تصحيح ADB لاسلكي
مكاتب: stdlib فقط (subprocess, os, re)
"""
import subprocess
import os
import re
import time
import sys

ADB = "adb"
_connected_device = None

def _adb(args: list, timeout=30, device=None) -> dict:
    """تنفيذ أمر ADB"""
    cmd = [ADB]
    if device:
        cmd += ["-s", device]
    cmd += args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = r.stdout.strip()
        err = r.stderr.strip()
        if r.returncode == 0 or out:
            return {"ok": True, "out": out, "err": err}
        return {"ok": False, "out": out, "err": err or "فشل الأمر."}
    except FileNotFoundError:
        return {"ok": False, "err": "ADB غير مثبت. نفّذ: pkg install android-tools"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "err": "انتهت المهلة."}
    except Exception as e:
        return {"ok": False, "err": str(e)}

class ADBConnection:
    @staticmethod
    def connect(ip: str, port: int = 5555):
        """الاتصال بجهاز عبر WiFi"""
        global _connected_device
        r = _adb(["connect", f"{ip}:{port}"])
        if r["ok"]:
            if "connected" in r["out"].lower() or "already" in r["out"].lower():
                _connected_device = f"{ip}:{port}"
                return f"✅ متصل بـ {ip}:{port}"
        return f"❌ فشل الاتصال: {r['err'] or r['out']}"

    @staticmethod
    def disconnect():
        global _connected_device
        r = _adb(["disconnect"])
        _connected_device = None
        return r["out"] if r["ok"] else r["err"]

    @staticmethod
    def list_devices():
        """قائمة الأجهزة المتصلة"""
        r = _adb(["devices", "-l"])
        return r["out"] if r["ok"] else r["err"]

    @staticmethod
    def pair(ip: str, port: int, code: str):
        """Pair عبر WiFi (Android 11+)"""
        r = _adb(["pair", f"{ip}:{port}", code])
        return r["out"] if r["ok"] else r["err"]

    @staticmethod
    def device_info():
        """معلومات الجهاز"""
        props = {
            "Brand":       ["getprop", "ro.product.brand"],
            "Model":       ["getprop", "ro.product.model"],
            "Android":     ["getprop", "ro.build.version.release"],
            "SDK":         ["getprop", "ro.build.version.sdk"],
            "Serial":      ["getprop", "ro.serialno"],
            "Resolution":  ["wm", "size"],
            "Battery":     ["dumpsys", "battery"],
        }
        result = {}
        for key, cmd in props.items():
            r = _adb(["shell"] + cmd, device=_connected_device)
            if r["ok"]:
                out = r["out"]
                if key == "Battery":
                    m = re.search(r"level: (\d+)", out)
                    result[key] = f"{m.group(1)}%" if m else out[:30]
                elif key == "Resolution":
                    result[key] = out.replace("Physical size: ", "")
                else:
                    result[key] = out
        return result

class ADBInput:
    @staticmethod
    def tap(x: int, y: int):
        """نقر على إحداثيات"""
        r = _adb(["shell", "input", "tap", str(x), str(y)], device=_connected_device)
        return "✅ تم النقر." if r["ok"] else r["err"]

    @staticmethod
    def swipe(x1, y1, x2, y2, duration_ms=300):
        """سحب من نقطة لأخرى"""
        r = _adb(["shell", "input", "swipe",
                  str(x1), str(y1), str(x2), str(y2), str(duration_ms)],
                 device=_connected_device)
        return "✅ تم السحب." if r["ok"] else r["err"]

    @staticmethod
    def type_text(text: str):
        """كتابة نص (يستبدل المسافات بـ %s)"""
        text_encoded = text.replace(" ", "%s")
        r = _adb(["shell", "input", "text", text_encoded], device=_connected_device)
        return "✅ تم الكتابة." if r["ok"] else r["err"]

    @staticmethod
    def key(keycode: str):
        """
        أحداث المفاتيح الشائعة:
        BACK, HOME, MENU, POWER, VOLUME_UP, VOLUME_DOWN,
        ENTER, DEL, TAB, SPACE, CAMERA, MEDIA_PLAY_PAUSE
        """
        r = _adb(["shell", "input", "keyevent", f"KEYCODE_{keycode.upper()}"],
                 device=_connected_device)
        return f"✅ KEYCODE_{keycode.upper()}" if r["ok"] else r["err"]

    @staticmethod
    def screenshot(save_path="screen.png"):
        """لقطة شاشة"""
        r = _adb(["shell", "screencap", "-p", "/sdcard/screen.png"], device=_connected_device)
        if not r["ok"]:
            return r["err"]
        r2 = _adb(["pull", "/sdcard/screen.png", save_path], device=_connected_device)
        return f"✅ محفوظة: {save_path}" if r2["ok"] else r2["err"]

    @staticmethod
    def record_screen(output="record.mp4", seconds=10):
        """تسجيل شاشة (Android 4.4+)"""
        print(f"⏺ جاري التسجيل لمدة {seconds} ثانية...")
        _adb(["shell", "screenrecord", "--time-limit", str(seconds), "/sdcard/record.mp4"],
             device=_connected_device, timeout=seconds + 10)
        r = _adb(["pull", "/sdcard/record.mp4", output], device=_connected_device)
        return f"✅ محفوظ: {output}" if r["ok"] else r["err"]

    @staticmethod
    def wake_screen():
        """إيقاظ الشاشة"""
        ADBInput.key("WAKEUP")
        return "✅ تم إيقاظ الشاشة."

    @staticmethod
    def lock_screen():
        ADBInput.key("SLEEP")
        return "✅ تم قفل الشاشة."

class ADBApps:
    @staticmethod
    def list_apps(include_system=False):
        """قائمة التطبيقات المثبتة"""
        flag = "" if include_system else "-3"
        cmd = ["shell", "pm", "list", "packages"]
        if flag: cmd.append(flag)
        r = _adb(cmd, device=_connected_device)
        if not r["ok"]: return r["err"]
        packages = [line.replace("package:", "").strip() for line in r["out"].split("\n") if line.strip()]
        return packages

    @staticmethod
    def install_apk(apk_path: str):
        """تثبيت APK"""
        if not os.path.exists(apk_path):
            return "الملف غير موجود."
        r = _adb(["install", "-r", apk_path], device=_connected_device, timeout=120)
        return r["out"] if r["ok"] else r["err"]

    @staticmethod
    def uninstall(package: str):
        """إزالة تطبيق"""
        r = _adb(["uninstall", package], device=_connected_device)
        return r["out"] if r["ok"] else r["err"]

    @staticmethod
    def backup_apk(package: str, output_dir="."):
        """استخراج APK من الجهاز"""
        r = _adb(["shell", "pm", "path", package], device=_connected_device)
        if not r["ok"]: return r["err"]
        apk_path = r["out"].replace("package:", "").strip()
        out_file  = os.path.join(output_dir, f"{package}.apk")
        r2 = _adb(["pull", apk_path, out_file], device=_connected_device)
        return f"✅ APK محفوظ: {out_file}" if r2["ok"] else r2["err"]

    @staticmethod
    def start_app(package: str):
        """فتح تطبيق"""
        r = _adb(["shell", "monkey", "-p", package, "-c",
                  "android.intent.category.LAUNCHER", "1"], device=_connected_device)
        return "✅ تم فتح التطبيق." if r["ok"] else r["err"]

    @staticmethod
    def force_stop(package: str):
        """إغلاق تطبيق قسراً"""
        r = _adb(["shell", "am", "force-stop", package], device=_connected_device)
        return "✅ تم الإغلاق." if r["ok"] else r["err"]

    @staticmethod
    def clear_data(package: str):
        """مسح بيانات تطبيق"""
        r = _adb(["shell", "pm", "clear", package], device=_connected_device)
        return r["out"] if r["ok"] else r["err"]

    @staticmethod
    def open_url(url: str):
        """فتح رابط في المتصفح"""
        r = _adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url],
                 device=_connected_device)
        return "✅ تم فتح الرابط." if r["ok"] else r["err"]

    @staticmethod
    def open_settings(screen=""):
        """فتح الإعدادات (اختياري: wifi/bluetooth/display/sound/apps)"""
        screens = {
            "wifi":      "android.settings.WIFI_SETTINGS",
            "bluetooth": "android.settings.BLUETOOTH_SETTINGS",
            "display":   "android.settings.DISPLAY_SETTINGS",
            "sound":     "android.settings.SOUND_SETTINGS",
            "apps":      "android.settings.APPLICATION_SETTINGS",
            "":          "android.settings.SETTINGS",
        }
        action = screens.get(screen.lower(), "android.settings.SETTINGS")
        r = _adb(["shell", "am", "start", "-a", action], device=_connected_device)
        return "✅ تم فتح الإعدادات." if r["ok"] else r["err"]

class ADBFiles:
    @staticmethod
    def push(local_path: str, device_path: str):
        r = _adb(["push", local_path, device_path], device=_connected_device, timeout=120)
        return r["out"] if r["ok"] else r["err"]

    @staticmethod
    def pull(device_path: str, local_path="."):
        r = _adb(["pull", device_path, local_path], device=_connected_device, timeout=120)
        return r["out"] if r["ok"] else r["err"]

    @staticmethod
    def list_dir(path="/sdcard"):
        r = _adb(["shell", "ls", "-la", path], device=_connected_device)
        return r["out"] if r["ok"] else r["err"]

    @staticmethod
    def delete(device_path: str):
        r = _adb(["shell", "rm", "-rf", device_path], device=_connected_device)
        return "✅ تم الحذف." if r["ok"] else r["err"]

    @staticmethod
    def mkdir(device_path: str):
        r = _adb(["shell", "mkdir", "-p", device_path], device=_connected_device)
        return "✅ تم إنشاء المجلد." if r["ok"] else r["err"]

class ADBMacro:
    """تشغيل سيناريوهات تلقائية متسلسلة"""
    def __init__(self):
        self.steps = []

    def add_tap(self, x, y, delay=0.5):
        self.steps.append(("tap", x, y, delay))
        return self

    def add_swipe(self, x1, y1, x2, y2, duration=300, delay=0.5):
        self.steps.append(("swipe", x1, y1, x2, y2, duration, delay))
        return self

    def add_type(self, text, delay=0.5):
        self.steps.append(("type", text, delay))
        return self

    def add_key(self, keycode, delay=0.5):
        self.steps.append(("key", keycode, delay))
        return self

    def add_wait(self, seconds):
        self.steps.append(("wait", seconds))
        return self

    def add_screenshot(self, path="macro_screen.png", delay=0.5):
        self.steps.append(("screenshot", path, delay))
        return self

    def run(self, repeat=1):
        results = []
        for i in range(repeat):
            if repeat > 1: print(f"\n▶ تكرار {i+1}/{repeat}")
            for step in self.steps:
                try:
                    action = step[0]
                    if action == "tap":
                        _, x, y, delay = step
                        r = ADBInput.tap(x, y)
                    elif action == "swipe":
                        _, x1, y1, x2, y2, dur, delay = step
                        r = ADBInput.swipe(x1, y1, x2, y2, dur)
                    elif action == "type":
                        _, text, delay = step
                        r = ADBInput.type_text(text)
                    elif action == "key":
                        _, keycode, delay = step
                        r = ADBInput.key(keycode)
                    elif action == "wait":
                        _, seconds = step
                        time.sleep(seconds)
                        r = f"⏳ انتظار {seconds}ث"
                        delay = 0
                    elif action == "screenshot":
                        _, path, delay = step
                        r = ADBInput.screenshot(path)
                    else:
                        r = "خطوة غير معروفة"
                        delay = 0

                    print(f"  [{action}] {r}")
                    results.append(r)
                    if delay: time.sleep(delay)
                except Exception as e:
                    results.append(f"خطأ: {e}")
        return results

    def clear(self):
        self.steps = []
        return self

if __name__ == "__main__":
    import json

    print("=" * 50)
    print("  🤖  ADB WiFi Controller")
    print("=" * 50)

    ip = input("IP الجهاز (فارغ لتخطي الاتصال) => ").strip()
    if ip:
        port = input("Port (5555) => ").strip() or "5555"
        print(ADBConnection.connect(ip, int(port)))
    else:
        print(ADBConnection.list_devices())

    menu = {
        "1":  ("معلومات الجهاز",         lambda: print(json.dumps(ADBConnection.device_info(), indent=2, ensure_ascii=False))),
        "2":  ("قائمة التطبيقات",        lambda: [print(p) for p in ADBApps.list_apps()]),
        "3":  ("تثبيت APK",              lambda: print(ADBApps.install_apk(input("مسار APK => ").strip()))),
        "4":  ("استخراج APK",            lambda: print(ADBApps.backup_apk(input("Package => ").strip(), input("مجلد الحفظ (.) => ").strip() or "."))),
        "5":  ("فتح تطبيق",              lambda: print(ADBApps.start_app(input("Package => ").strip()))),
        "6":  ("إغلاق تطبيق",           lambda: print(ADBApps.force_stop(input("Package => ").strip()))),
        "7":  ("فتح رابط",              lambda: print(ADBApps.open_url(input("URL => ").strip()))),
        "8":  ("لقطة شاشة",             lambda: print(ADBInput.screenshot(input("اسم الملف (screen.png) => ").strip() or "screen.png"))),
        "9":  ("تسجيل شاشة",            lambda: print(ADBInput.record_screen(input("اسم الملف (record.mp4) => ").strip() or "record.mp4", int(input("مدة (ثواني) => ") or 10)))),
        "10": ("نقر على إحداثيات",       lambda: print(ADBInput.tap(int(input("X => ")), int(input("Y => "))))),
        "11": ("كتابة نص",              lambda: print(ADBInput.type_text(input("النص => ").strip()))),
        "12": ("ضغط مفتاح",            lambda: print(ADBInput.key(input("المفتاح (HOME/BACK/ENTER/...) => ").strip()))),
        "13": ("رفع ملف للجهاز",         lambda: print(ADBFiles.push(input("المسار المحلي => ").strip(), input("المسار على الجهاز => ").strip()))),
        "14": ("سحب ملف من الجهاز",      lambda: print(ADBFiles.pull(input("المسار على الجهاز => ").strip(), input("حفظ في (.) => ").strip() or "."))),
        "15": ("مسح بيانات تطبيق",       lambda: print(ADBApps.clear_data(input("Package => ").strip()))),
        "16": ("Macro تلقائي",          _run_macro_demo),
        "17": ("إيقاظ الشاشة",           lambda: print(ADBInput.wake_screen())),
        "18": ("فتح إعدادات",            lambda: print(ADBApps.open_settings(input("(wifi/bluetooth/display/sound/apps/فارغ) => ").strip()))),
    }

    def _run_macro_demo():
        print("مثال Macro: فتح الهوم + انتظار + لقطة شاشة")
        macro = ADBMacro()
        macro.add_key("HOME")\
             .add_wait(1)\
             .add_screenshot("macro_result.png")
        macro.run()

    while True:
        print("\n" + "─"*45)
        for k, (label, _) in menu.items():
            print(f"  {k:>2}. {label}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except KeyboardInterrupt: pass
            except Exception as e: print(f"خطأ: {e}")
