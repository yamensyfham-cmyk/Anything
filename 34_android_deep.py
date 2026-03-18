"""
أدوات أندرويد عميقة — 30 ميزة
يتطلب: ADB + Termux:API بدون روت
"""
import os, sys, json, subprocess, time, re, threading
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

def _adb(args, timeout=30):
    try:
        r = subprocess.run(["adb","shell"]+args, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e: return f"❌ {e}"

def _termux(args, timeout=15):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        out = r.stdout.strip()
        try: return json.loads(out) if out else {}
        except Exception: return out
    except Exception as e: return f"❌ {e}"

class AndroidDeepTools:

    @staticmethod
    def full_device_info() -> dict:
        props = {
            "Brand":         "ro.product.brand",
            "Model":         "ro.product.model",
            "Android":       "ro.build.version.release",
            "SDK":           "ro.build.version.sdk",
            "Build":         "ro.build.display.id",
            "Security Patch":"ro.build.version.security_patch",
            "Bootloader":    "ro.bootloader",
            "Hardware":      "ro.hardware",
            "CPU ABI":       "ro.product.cpu.abi",
            "Resolution":    None,
            "Density":       None,
        }
        result = {}
        for key, prop in props.items():
            if prop: result[key] = _adb(["getprop", prop])
        result["Resolution"] = _adb(["wm","size"])
        result["Density"]    = _adb(["wm","density"])
        result["IMEI"]       = _adb(["service","call","iphonesubinfo","1"])[:50]
        return result

    @staticmethod
    def installed_apps(include_system=False) -> list:
        flag = "" if include_system else "-3"
        out  = _adb(["pm","list","packages"] + ([flag] if flag else []))
        return [line.replace("package:","") for line in out.split('\n') if line.strip()]

    @staticmethod
    def app_info(package: str) -> dict:
        out = _adb(["dumpsys","package",package])
        info = {}
        patterns = {
            "versionName":  r'versionName=([^\s]+)',
            "versionCode":  r'versionCode=(\d+)',
            "targetSDK":    r'targetSdk=(\d+)',
            "firstInstall": r'firstInstallTime=([^\n]+)',
            "lastUpdate":   r'lastUpdateTime=([^\n]+)',
            "dataDir":      r'dataDir=([^\s]+)',
        }
        for k,p in patterns.items():
            m = re.search(p, out)
            if m: info[k] = m.group(1).strip()
        info["package"] = package
        return info

    @staticmethod
    def force_stop(package: str) -> str:
        return _adb(["am","force-stop",package])

    @staticmethod
    def clear_app_data(package: str) -> str:
        return _adb(["pm","clear",package])

    @staticmethod
    def enable_app(package: str) -> str:
        return _adb(["pm","enable",package])

    @staticmethod
    def disable_app(package: str) -> str:
        return _adb(["pm","disable-user","--user","0",package])

    @staticmethod
    def open_app(package: str) -> str:
        return _adb(["monkey","-p",package,"-c","android.intent.category.LAUNCHER","1"])

    @staticmethod
    def open_activity(package: str, activity: str) -> str:
        return _adb(["am","start","-n",f"{package}/{activity}"])

    @staticmethod
    def send_intent(action: str, data="") -> str:
        cmd = ["am","start","-a",action]
        if data: cmd += ["-d",data]
        return _adb(cmd)

    @staticmethod
    def storage_info() -> dict:
        out = _adb(["df","-h"])
        lines = [l for l in out.split('\n') if '/sdcard' in l or '/data' in l]
        result = {}
        for line in lines:
            parts = line.split()
            if len(parts) >= 5:
                result[parts[5] if len(parts)>5 else parts[0]] = {
                    "size":parts[1],"used":parts[2],"avail":parts[3],"use%":parts[4]
                }
        return result

    @staticmethod
    def memory_usage_per_app(top=15) -> list:
        out = _adb(["dumpsys","meminfo"])
        apps = []
        pattern = re.compile(r'(\d+)K:\s+(.+?)\s*\(pid\s+(\d+)')
        for m in pattern.finditer(out):
            apps.append({"kb":int(m.group(1)),"app":m.group(2),"pid":m.group(3)})
        return sorted(apps,key=lambda x:-x["kb"])[:top]

    @staticmethod
    def battery_detail() -> dict:
        out = _adb(["dumpsys","battery"])
        info = {}
        for line in out.split('\n'):
            if ':' in line:
                k,v = line.split(':',1)
                info[k.strip()] = v.strip()
        return info

    @staticmethod
    def cpu_usage() -> str:
        return _adb(["top","-n","1","-b","-q"])[:1000]

    @staticmethod
    def wifi_info() -> dict:
        out = _adb(["dumpsys","wifi"])
        info = {}
        patterns = {
            "SSID":    r'mWifiInfo.+?SSID:\s*"([^"]+)"',
            "IP":      r'mWifiInfo.+?IP address:\s*([\d.]+)',
            "Signal":  r'mWifiInfo.+?Rssi:\s*(-\d+)',
            "Speed":   r'mWifiInfo.+?Link speed:\s*(\d+)',
        }
        for k,p in patterns.items():
            m = re.search(p, out, re.DOTALL)
            if m: info[k] = m.group(1)
        return info

    @staticmethod
    def active_connections() -> str:
        return _adb(["netstat","-tuln"]) or _adb(["cat","/proc/net/tcp"])

    @staticmethod
    def data_usage_per_app() -> list:
        out = _adb(["cat","/proc/net/xt_qtaguid/stats"])
        lines = out.split('\n')[1:]
        apps  = []
        for line in lines[:30]:
            parts = line.split()
            if len(parts) >= 8:
                apps.append({"iface":parts[1],"uid":parts[3],
                             "rx_bytes":parts[5],"tx_bytes":parts[7]})
        return apps

    @staticmethod
    def list_media_files(media_type="images") -> list:
        type_map = {
            "images": "/sdcard/DCIM",
            "downloads": "/sdcard/Download",
            "music": "/sdcard/Music",
            "videos": "/sdcard/Movies",
        }
        folder = type_map.get(media_type, f"/sdcard/{media_type}")
        out    = _adb(["ls","-la",folder])
        return [l for l in out.split('\n') if l.strip() and not l.startswith('total')]

    @staticmethod
    def backup_sdcard(local_out="sdcard_backup.tar.gz") -> str:
        print("⏳ جاري النسخ الاحتياطي...")
        tmp = "/sdcard/uas_backup.tar.gz"
        _adb(["tar","czf",tmp,"/sdcard/DCIM","/sdcard/Download"])
        r = subprocess.run(["adb","pull",tmp,local_out], capture_output=True, text=True)
        _adb(["rm","-f",tmp])
        return r.stdout.strip() or r.stderr.strip()

    @staticmethod
    def push_file(local: str, remote: str) -> str:
        r = subprocess.run(["adb","push",local,remote], capture_output=True, text=True)
        return r.stdout.strip() or r.stderr.strip()

    @staticmethod
    def pull_file(remote: str, local=".") -> str:
        r = subprocess.run(["adb","pull",remote,local], capture_output=True, text=True)
        return r.stdout.strip() or r.stderr.strip()

    @staticmethod
    def get_sensors() -> dict:
        result = _termux(["termux-sensor","-l"])
        return result if isinstance(result,dict) else {"output":str(result)[:200]}

    @staticmethod
    def read_sensor(name: str, readings=5) -> dict:
        return _termux(["termux-sensor","-s",name,"-n",str(readings)])

    @staticmethod
    def get_telephony() -> dict:
        return _termux(["termux-telephony-deviceinfo"])

    @staticmethod
    def get_call_log(limit=10) -> list:
        r = _termux(["termux-call-log","-l",str(limit)])
        return r if isinstance(r,list) else []

    @staticmethod
    def make_call(number: str) -> str:
        r = _termux(["termux-telephony-call",number])
        return str(r)

    @staticmethod
    def get_contacts() -> list:
        r = _termux(["termux-contact-list"])
        return r if isinstance(r,list) else []

    @staticmethod
    def fingerprint_auth() -> dict:
        return _termux(["termux-fingerprint"])

    @staticmethod
    def tts_speak(text: str, lang="ar", rate=1.0) -> str:
        r = _termux(["termux-tts-speak","-l",lang,"-r",str(rate),text])
        return "✅ جارٍ الكلام." if r is not None else "❌ فشل"

    @staticmethod
    def tts_list_engines() -> list:
        r = _termux(["termux-tts-engines"])
        return r if isinstance(r,list) else [str(r)]

    @staticmethod
    def record_audio(out="recording.aac", duration=10) -> str:
        r = _termux(["termux-microphone-record","-e","AAC","-d",str(duration),"-f",out])
        return f"✅ {out}" if os.path.exists(out) else str(r)

    @staticmethod
    def stop_recording() -> str:
        return str(_termux(["termux-microphone-record","-q"]))

    @staticmethod
    def media_player_play(path: str) -> str:
        return str(_termux(["termux-media-player","play",path]))

    @staticmethod
    def media_player_stop() -> str:
        return str(_termux(["termux-media-player","stop"]))

    @staticmethod
    def get_media_info() -> dict:
        return _termux(["termux-media-player","info"])

    @staticmethod
    def share_file(path: str, mimetype="*/*") -> str:
        r = _termux(["termux-share","-a","send","-c",mimetype,path])
        return str(r)

    @staticmethod
    def open_url_in_browser(url: str) -> str:
        return str(_termux(["termux-open-url",url]))

if __name__ == "__main__":
    adt = AndroidDeepTools()
    menu = {
        "1":  ("معلومات الجهاز الكاملة",   lambda: print(json.dumps(adt.full_device_info(), indent=2, ensure_ascii=False))),
        "2":  ("قائمة التطبيقات",          lambda: [print(f"  {a}") for a in adt.installed_apps()[:30]]),
        "3":  ("معلومات تطبيق",            lambda: print(json.dumps(adt.app_info(input("Package => ")), indent=2, ensure_ascii=False))),
        "4":  ("إغلاق تطبيق",              lambda: print(adt.force_stop(input("Package => ")))),
        "5":  ("مسح بيانات تطبيق",         lambda: print(adt.clear_app_data(input("Package => ")))),
        "6":  ("تعطيل تطبيق",              lambda: print(adt.disable_app(input("Package => ")))),
        "7":  ("تفعيل تطبيق",              lambda: print(adt.enable_app(input("Package => ")))),
        "8":  ("معلومات البطارية",          lambda: print(json.dumps(adt.battery_detail(), indent=2, ensure_ascii=False))),
        "9":  ("معلومات التخزين",           lambda: print(json.dumps(adt.storage_info(), indent=2, ensure_ascii=False))),
        "10": ("استهلاك الذاكرة",           lambda: [print(f"  {a['app']:<40} {a['kb']/1024:.1f} MB") for a in adt.memory_usage_per_app()]),
        "11": ("معلومات WiFi",              lambda: print(json.dumps(adt.wifi_info(), indent=2))),
        "12": ("رفع ملف",                  lambda: print(adt.push_file(input("المحلي => "), input("البعيد => ")))),
        "13": ("سحب ملف",                  lambda: print(adt.pull_file(input("البعيد => "), input("المحلي (.) => ") or "."))),
        "14": ("نسخ sdcard",               lambda: print(adt.backup_sdcard(input("الإخراج (sdcard_backup.tar.gz) => ") or "sdcard_backup.tar.gz"))),
        "15": ("قائمة الصور",              lambda: [print(f"  {f}") for f in adt.list_media_files("images")[:20]]),
        "16": ("المستشعرات",               lambda: print(json.dumps(adt.get_sensors(), indent=2, ensure_ascii=False))),
        "17": ("معلومات الشبكة الخلوية",   lambda: print(json.dumps(adt.get_telephony(), indent=2, ensure_ascii=False))),
        "18": ("سجل المكالمات",            lambda: print(json.dumps(adt.get_call_log(), indent=2, ensure_ascii=False))),
        "19": ("جهات الاتصال",             lambda: [print(f"  {c.get('name','')} — {c.get('number','')}") for c in adt.get_contacts()[:20]]),
        "20": ("نص لصوت TTS",              lambda: print(adt.tts_speak(input("النص => "), input("اللغة (ar/en) => ") or "ar"))),
        "21": ("تسجيل صوت",               lambda: print(adt.record_audio(input("اسم الملف (recording.aac) => ") or "recording.aac", int(input("المدة (10ث) => ") or 10)))),
        "22": ("تشغيل صوت",               lambda: print(adt.media_player_play(input("مسار الملف => ")))),
        "23": ("إيقاف الصوت",             lambda: print(adt.media_player_stop())),
        "24": ("مشاركة ملف",              lambda: print(adt.share_file(input("مسار الملف => ")))),
        "25": ("فتح رابط",                lambda: print(adt.open_url_in_browser(input("URL => ")))),
    }
    while True:
        print("\n═"*45)
        print("  📱  Android Deep Tools — 25 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
