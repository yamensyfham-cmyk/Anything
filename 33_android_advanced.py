"""
أدوات أندرويد المتقدمة — 30 ميزة
مكاتب: stdlib فقط (subprocess)
"""
import os, sys, subprocess, json, time, re, threading
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

def _adb(args, timeout=30, device=None):
    cmd = ["adb"]
    if device: cmd += ["-s", device]
    cmd += args if isinstance(args, list) else args.split()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() or r.stderr.strip()
    except FileNotFoundError: return "❌ adb غير مثبت: pkg install android-tools"
    except Exception as e:    return f"❌ {e}"

def _shell(cmd, **kwargs): return _adb(["shell"] + (cmd if isinstance(cmd, list) else cmd.split()), **kwargs)

class AndroidAdvanced:

    @staticmethod
    def app_info(package: str) -> dict:
        """معلومات تفصيلية عن تطبيق"""
        dump = _shell(f"dumpsys package {package}")
        info = {}
        for pattern, key in [
            (r"versionName=(.+)", "الإصدار"),
            (r"versionCode=(\d+)", "كود الإصدار"),
            (r"firstInstallTime=(.+)", "تاريخ التثبيت"),
            (r"lastUpdateTime=(.+)",  "آخر تحديث"),
            (r"userId=(\d+)",         "User ID"),
            (r"dataDir=(.+)",         "مجلد البيانات"),
            (r"flags=(.+)",           "الأعلام"),
        ]:
            m = re.search(pattern, dump)
            if m: info[key] = m.group(1).strip()
        info["الحزمة"] = package
        return info

    @staticmethod
    def list_permissions(package: str) -> list:
        """أذونات تطبيق"""
        dump = _shell(f"dumpsys package {package}")
        return re.findall(r'android\.permission\.[A-Z_]+', dump)

    @staticmethod
    def app_activities(package: str) -> list:
        """قائمة Activities"""
        dump = _shell(f"dumpsys package {package}")
        return re.findall(r'[a-zA-Z0-9.]+Activity', dump)[:20]

    @staticmethod
    def app_size(package: str) -> dict:
        """حجم التطبيق"""
        dump = _shell(f"dumpsys package {package}")
        path = re.search(r'path: (.+)', dump)
        if path:
            size_out = _shell(f"du -sh {path.group(1).strip()}")
            return {"package":package, "path":path.group(1).strip(), "size":size_out.split()[0] if size_out else "N/A"}
        return {"error": "لم يُعثر على المسار"}

    @staticmethod
    def running_apps() -> list:
        """التطبيقات الجارية حالياً"""
        out = _shell("am stack list 2>/dev/null || dumpsys activity | grep 'Running activities'")
        pkgs = re.findall(r'([a-zA-Z][a-zA-Z0-9_]*\.[a-zA-Z][a-zA-Z0-9_.]+)', out)
        return list(set(pkgs))[:20]

    @staticmethod
    def force_stop_all_bg() -> str:
        """إيقاف كل التطبيقات في الخلفية"""
        apps = AndroidAdvanced.running_apps()
        count = 0
        for app in apps:
            if app not in ("android", "com.android.systemui"):
                _shell(f"am force-stop {app}")
                count += 1
        return f"✅ أُوقفت {count} تطبيق"

    @staticmethod
    def open_activity(package: str, activity: str) -> str:
        return _shell(f"am start -n {package}/{activity}")

    @staticmethod
    def deep_link(url: str) -> str:
        return _adb(["shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url])

    @staticmethod
    def send_intent(action: str, extra_key="", extra_val="") -> str:
        cmd = ["shell", "am", "broadcast", "-a", action]
        if extra_key: cmd += ["--es", extra_key, extra_val]
        return _adb(cmd)

    @staticmethod
    def record_input(duration=10, out="input_record.txt") -> str:
        """تسجيل أحداث اللمس"""
        cmd = f"adb shell getevent -lt /dev/input/event0"
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=duration+5)
        with open(out,"w") as f: f.write(result.stdout)
        return f"✅ {out}"

    @staticmethod
    def swipe_pattern(pattern: list, delay=0.2) -> str:
        """سحب متعدد النقاط"""
        for x1,y1,x2,y2 in pattern:
            _adb(["shell","input","swipe",str(x1),str(y1),str(x2),str(y2),"200"])
            time.sleep(delay)
        return "✅ اكتمل"

    @staticmethod
    def tap_multiple(coords: list, delay=0.5) -> str:
        """نقر على نقاط متعددة"""
        for x,y in coords:
            _adb(["shell","input","tap",str(x),str(y)])
            time.sleep(delay)
        return "✅ اكتمل"

    @staticmethod
    def set_brightness(value: int) -> str:
        """ضبط السطوع 0-255"""
        _shell(f"settings put system screen_brightness {max(0,min(255,value))}")
        return f"✅ السطوع: {value}"

    @staticmethod
    def set_volume(stream: str, value: int) -> str:
        streams = {"music":"3","ring":"2","alarm":"4","notification":"5"}
        _shell(f"media volume --stream {streams.get(stream,'3')} --set {value}")
        return f"✅ {stream}: {value}"

    @staticmethod
    def screen_rotation(mode: str) -> str:
        """mode: landscape / portrait / auto"""
        if mode == "landscape":
            _shell("settings put system accelerometer_rotation 0")
            _shell("settings put system user_rotation 1")
        elif mode == "portrait":
            _shell("settings put system accelerometer_rotation 0")
            _shell("settings put system user_rotation 0")
        else:
            _shell("settings put system accelerometer_rotation 1")
        return f"✅ {mode}"

    @staticmethod
    def screenshot_interval(count=5, interval=2, folder=".") -> str:
        """لقطات متعددة بفاصل زمني"""
        os.makedirs(folder, exist_ok=True)
        for i in range(count):
            ts  = int(time.time())
            out = os.path.join(folder, f"screen_{ts}.png")
            _adb(["shell","screencap","-p",f"/sdcard/_{ts}.png"])
            _adb(["pull",f"/sdcard/_{ts}.png", out])
            _shell(f"rm /sdcard/_{ts}.png")
            if i < count-1: time.sleep(interval)
        return f"✅ {count} لقطة → {folder}"

    @staticmethod
    def wifi_info() -> dict:
        """معلومات WiFi الحالي"""
        out = _shell("dumpsys wifi | head -50")
        info = {}
        for pat, key in [(r'SSID: (.+?),','"SSID"'),(r'BSSID: (.+?),','"BSSID"'),(r'IP: (\S+)','"IP"')]:
            m = re.search(pat, out)
            if m: info[key.strip('"')] = m.group(1).strip()
        return info

    @staticmethod
    def mobile_data_usage() -> dict:
        """استهلاك البيانات"""
        out = _shell("dumpsys netstats | grep -E 'uid=|rx_bytes|tx_bytes' | head -30")
        return {"raw": out[:500]}

    @staticmethod
    def proxy_set(host: str, port: int) -> str:
        _shell(f"settings put global http_proxy {host}:{port}")
        return f"✅ Proxy: {host}:{port}"

    @staticmethod
    def proxy_clear() -> str:
        _shell("settings delete global http_proxy")
        return "✅ Proxy محذوف"

    @staticmethod
    def get_wifi_password() -> str:
        """محاولة استخراج كلمة مرور WiFi (تتطلب صلاحيات على بعض الأجهزة)"""
        paths = ["/data/misc/wifi/WifiConfigStore.xml",
                 "/data/misc/wifi/wpa_supplicant.conf"]
        for path in paths:
            out = _shell(f"cat {path}")
            if "psk" in out.lower() or "password" in out.lower():
                return out[:1000]
        return "❌ يتطلب صلاحيات إضافية"

    @staticmethod
    def get_logcat(count=50, tag="") -> str:
        cmd = ["shell","logcat","-d","-t",str(count)]
        if tag: cmd += [f"{tag}:D","*:S"]
        return _adb(cmd, timeout=15)

    @staticmethod
    def clear_logcat() -> str:
        return _adb(["shell","logcat","-c"])

    @staticmethod
    def get_properties() -> dict:
        """كل خصائص النظام"""
        out = _shell("getprop")
        props = {}
        for line in out.split('\n'):
            m = re.match(r'\[(.+?)\]:\s*\[(.*)?\]', line)
            if m: props[m.group(1)] = m.group(2)
        return props

    @staticmethod
    def set_property(key: str, value: str) -> str:
        return _shell(f"setprop {key} {value}")

    @staticmethod
    def cpu_governor(governor="performance") -> str:
        """تغيير حاكم المعالج"""
        cores = _shell("ls /sys/devices/system/cpu/").split()
        count = 0
        for core in cores:
            if re.match(r'cpu\d+$', core):
                path = f"/sys/devices/system/cpu/{core}/cpufreq/scaling_governor"
                _shell(f"echo {governor} > {path}")
                count += 1
        return f"✅ {governor} → {count} core"

    @staticmethod
    def battery_detail() -> dict:
        out = _shell("dumpsys battery")
        info = {}
        for line in out.split('\n'):
            if ':' in line:
                k,v = line.split(':',1)
                info[k.strip()] = v.strip()
        return info

    @staticmethod
    def reboot(mode="") -> str:
        if mode == "recovery": return _adb(["reboot","recovery"])
        if mode == "bootloader": return _adb(["reboot","bootloader"])
        if mode == "fastboot": return _adb(["reboot","fastboot"])
        return _adb(["reboot"])

    @staticmethod
    def sideload(zip_path: str) -> str:
        """تثبيت OTA عبر ADB Sideload"""
        return _adb(["sideload", zip_path], timeout=300)

if __name__ == "__main__":
    menu = {
        "1":  ("معلومات تطبيق",            lambda: print(json.dumps(AndroidAdvanced.app_info(input("Package => ")), indent=2, ensure_ascii=False))),
        "2":  ("أذونات تطبيق",             lambda: [print(f"  {p}") for p in AndroidAdvanced.list_permissions(input("Package => "))]),
        "3":  ("التطبيقات الجارية",         lambda: [print(f"  {a}") for a in AndroidAdvanced.running_apps()]),
        "4":  ("إيقاف الخلفية كلها",        lambda: print(AndroidAdvanced.force_stop_all_bg())),
        "5":  ("فتح رابط Deep Link",        lambda: print(AndroidAdvanced.deep_link(input("URL => ")))),
        "6":  ("لقطات متعددة",              lambda: print(AndroidAdvanced.screenshot_interval(int(input("عدد (5) => ") or 5), int(input("فاصل (2ث) => ") or 2)))),
        "7":  ("ضبط السطوع",               lambda: print(AndroidAdvanced.set_brightness(int(input("0-255 => "))))),
        "8":  ("ضبط الصوت",               lambda: print(AndroidAdvanced.set_volume(input("music/ring/alarm => "), int(input("0-15 => "))))),
        "9":  ("دوران الشاشة",             lambda: print(AndroidAdvanced.screen_rotation(input("landscape/portrait/auto => ")))),
        "10": ("معلومات WiFi",             lambda: print(json.dumps(AndroidAdvanced.wifi_info(), indent=2, ensure_ascii=False))),
        "11": ("ضبط Proxy",               lambda: print(AndroidAdvanced.proxy_set(input("Host => "), int(input("Port => "))))),
        "12": ("حذف Proxy",               lambda: print(AndroidAdvanced.proxy_clear())),
        "13": ("Logcat",                   lambda: print(AndroidAdvanced.get_logcat(int(input("عدد (50) => ") or 50), input("Tag (فارغ=الكل) => ")))),
        "14": ("خصائص النظام",            lambda: [print(f"  {k}: {v}") for k,v in list(AndroidAdvanced.get_properties().items())[:30]]),
        "15": ("معلومات البطارية",         lambda: print(json.dumps(AndroidAdvanced.battery_detail(), indent=2, ensure_ascii=False))),
        "16": ("تغيير حاكم المعالج",       lambda: print(AndroidAdvanced.cpu_governor(input("performance/powersave/ondemand => ") or "performance"))),
    }
    while True:
        print("\n═"*45)
        print("  📱  Android Advanced — 16 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
