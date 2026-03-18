"""
UAS — Unified Automation Suite v4.0
أداة الأتمتة الموحدة — Termux / Android
"""
import os, sys, subprocess
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

class C:
    R="\033[0m";B="\033[1m";DIM="\033[2m"
    RED="\033[91m";GRN="\033[92m";YEL="\033[93m"
    BLU="\033[94m";MAG="\033[95m";CYN="\033[96m";WHT="\033[97m"

def c(col,t): return f"{col}{t}{C.R}"
def cl(): os.system("clear" if os.name!="nt" else "cls")

TOOLS = {
    "🧠  AI": [
        ("99", "🧠 AI Agent",              "تحكم بكل الأدوات بالعربي",              "00_ai_agent"),
        ("20", "💬 AI Chat",               "محادثة Gemini/GPT مع ذاكرة",            "01_ai_chat"),
    ],
    "🤖  ANDROID": [
        ("1",  "📱 Termux API",            "SMS/إشعارات/كاميرا/GPS/WiFi",           "03_termux_api"),
        ("2",  "🤖 ADB WiFi",              "تحكم كامل بدون روت",                    "04_adb_controller"),
        ("3",  "⚡ Android Automation",    "ردود تلقائية/GPS Logger/Battery",       "17_android_automation"),
        ("4",  "📱 Android Deep",          "معلومات عميقة/TTS/تسجيل/مستشعرات",     "34_android_deep"),
        ("5",  "📦 APK Analyzer",          "تحليل ملفات APK",                       "02_apk_analyzer"),
    ],
    "🖥  SYSTEM": [
        ("6",  "📁 File Manager",          "شجرة/بحث/مكررات/تنظيم",               "05_file_manager"),
        ("7",  "📊 Resource Monitor",      "CPU/RAM/Disk/Uptime",                   "08_resource_monitor"),
        ("8",  "⚙  Task Manager",          "العمليات وإدارتها",                     "07_task_manager"),
        ("9",  "🖥  System Advanced",       "معلومات/حرارة/مراقبة/نسخ",             "28_system_advanced"),
        ("10", "🗄  SQLite Analyzer",       "قواعد بيانات أندرويد",                  "11_sqlite_analyzer"),
        ("11", "📡 Monitoring",             "مراقبة URLs/النظام/التنبيهات",          "35_monitoring"),
    ],
    "🌐  NETWORK": [
        ("12", "🌐 Network Monitor",       "اتصالات/منافذ/سرعة",                   "09_network_monitor"),
        ("13", "🌐 Network Advanced",      "LAN/SSL/Traceroute/DNS",               "23_network_advanced"),
        ("14", "⚡ Speed Test",             "قياس سرعة الإنترنت",                    "16_speed_test"),
        ("15", "🔍 OSINT Tools",            "IP/DNS/Ports/Subdomains",               "12_osint_tools"),
        ("16", "🔒 Web Scanner",            "XSS/SQLi/Headers",                      "13_web_tools"),
        ("17", "🌐 Web Automation",         "Crawl/Scrape/Monitor/Forms",            "32_web_automation"),
        ("18", "📱 Telegram",               "Bot/رسائل/مجموعات/مراقبة",             "29_telegram_tools"),
        ("19", "📧 Email",                  "إرسال/استقبال/رد تلقائي",              "30_email_tools"),
    ],
    "🔐  SECURITY": [
        ("21", "🔐 File Encryptor",         "تشفير/فك تشفير",                        "06_file_encryptor"),
        ("22", "🔑 Password",               "توليد + فحص + Pwned",                  "10_password_generator"),
        ("23", "🔧 Hash & Text",            "MD5/SHA/Base64/HEX",                    "18_hash_text_tools"),
        ("24", "🛡  Security Toolkit",       "JWT/Steganography/Brute/Scan",         "24_security_toolkit"),
        ("25", "🔌 SSH Tools",              "SSH/SFTP/Shell/Tunnel",                "20_ssh_tools"),
    ],
    "📊  DATA & MEDIA": [
        ("26", "📊 Data Analysis",          "CSV/Excel/Charts/pandas",              "21_data_analysis"),
        ("27", "📄 PDF & OCR",              "قراءة/دمج/OCR/إنشاء",                  "31_pdf_ocr_tools"),
        ("28", "📱 QR Tools",               "توليد/قراءة QR",                        "22_qr_tools"),
        ("29", "🖼  Image Tools",            "تحويل/فلاتر/ضغط/دمج",                 "19_image_tools"),
        ("30", "🎬 Media Downloader",        "yt-dlp/ffmpeg/تحويل",                  "27_media_downloader"),
        ("31", "📝 Text NLP",               "تحليل/ترجمة/تلخيص/مشاعر",             "33_text_nlp_tools"),
        ("32", "💰 Crypto & Finance",        "عملات/أسهم/محفظة/تنبيهات",            "36_crypto_finance"),
    ],
    "🛠  TOOLS": [
        ("33", "💻 Dev Tools",              "Git/API Test/JSON/كود",                "25_dev_tools"),
        ("34", "📝 Productivity",           "ملاحظات/مهام/حاسبة/مصروفات",          "26_productivity"),
        ("35", "💾 Backup",                 "نسخ احتياطي",                           "__backup__"),
        ("36", "🗜  Compressor",             "ضغط/فك ضغط",                           "__compress__"),
        ("37", "📞 Contacts",               "جهات اتصال + VCF",                     "14_contacts"),
        ("38", "⏰ Scheduler",              "جدولة المهام",                          "15_scheduler_logger"),
    ],
}

CAT_C = {"AI":C.MAG,"ANDROID":C.GRN,"SYSTEM":C.BLU,"NETWORK":C.YEL,
         "SECURITY":C.RED,"DATA":C.CYN,"TOOLS":C.WHT}

def _backup():
    import shutil
    from datetime import datetime
    src=input("مجلد المصدر => ").strip(); dst=input("مجلد الوجهة => ").strip()
    try:
        out=os.path.join(dst,f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        shutil.make_archive(out,'zip',src); print(c(C.GRN,f"✅ {out}.zip"))
    except Exception as e: print(c(C.RED,f"❌ {e}"))

def _compress():
    import shutil
    print("1- ضغط  |  2- فك ضغط"); ch=input("=> ").strip()
    try:
        if ch=="1":
            path=input("المسار => ").strip(); fmt=input("التنسيق (zip/tar/gztar) => ").strip() or "zip"
            base=os.path.splitext(os.path.basename(path))[0]
            shutil.make_archive(os.path.join(os.path.dirname(path) or ".",base),fmt,os.path.dirname(path) or ".",os.path.basename(path))
            print(c(C.GRN,"✅ تم الضغط."))
        elif ch=="2":
            path=input("الملف المضغوط => ").strip(); dest=input("مجلد الوجهة => ").strip()
            os.makedirs(dest,exist_ok=True); shutil.unpack_archive(path,dest)
            print(c(C.GRN,"✅ تم فك الضغط."))
    except Exception as e: print(c(C.RED,f"❌ {e}"))

INLINE={"__backup__":_backup,"__compress__":_compress}

def banner():
    cl()
    total = sum(len(v) for v in TOOLS.values())
    print(f"""
{c(C.MAG+C.B,'╔══════════════════════════════════════════════════════════╗')}
{c(C.MAG,'║')} {c(C.CYN+C.B,'    UAS — Unified Automation Suite v4.0               ')}{c(C.MAG,'║')}
{c(C.MAG,'║')} {c(C.YEL,f'    {total} أداة | 490+ ميزة | Termux • No Root          ')}{c(C.MAG,'║')}
{c(C.MAG,'╚══════════════════════════════════════════════════════════╝')}""")

def print_menu():
    banner()
    for cat,tools in TOOLS.items():
        col=next((v for k,v in CAT_C.items() if k in cat),C.WHT)
        print(f"\n  {c(col+C.B,'── '+cat+' ──────────────────────────────────')}")
        for num,name,desc,_ in tools:
            print(f"  {c(C.YEL,f'{num:>2}')}. {c(C.B+C.WHT,name):<34}{c(C.DIM,desc)}")
    print(f"\n  {c(C.RED,' 0')}. خروج\n")

def find(num):
    for tools in TOOLS.values():
        for t in tools:
            if t[0]==num: return t
    return None

def launch(num):
    info=find(num)
    if not info: print(c(C.RED,"❌ اختيار غير صالح.")); return
    _,name,desc,module=info
    if module in INLINE:
        print(f"\n{c(C.CYN+C.B,name)}\n"+"─"*45); INLINE[module](); return
    path=os.path.join(BASE_DIR,f"{module}.py")
    if not os.path.exists(path):
        print(c(C.RED,f"❌ الملف غير موجود: {module}.py")); return
    cl()
    print(f"\n{c(C.CYN+C.B,f'[ {name} ]')}")
    print(c(C.DIM,desc)+"\n"+"═"*50+"\n")
    try: subprocess.run([sys.executable,path])
    except KeyboardInterrupt: pass

def main():
    while True:
        print_menu()
        try: ch=input(f"  {c(C.YEL+C.B,'اختر')} => ").strip()
        except (KeyboardInterrupt,EOFError): print(f"\n{c(C.GRN,'وداعاً! 👋')}\n"); break
        if ch=="0": print(f"\n{c(C.GRN,'✅ وداعاً!')}\n"); break
        if ch:
            try: launch(ch)
            except KeyboardInterrupt: pass
            except Exception as e: print(c(C.RED,f"❌ {e}"))
        input(f"\n{c(C.DIM,'↩ اضغط Enter للعودة...')}")

if __name__=="__main__":
    main()
