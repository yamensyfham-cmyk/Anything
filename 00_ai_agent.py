"""
UAS AI Agent — تحكم بكل الأدوات بالعربي
مكاتب: aielostora فقط
باقي الكود: stdlib خالص
"""
import json
import re
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

TOOLS_REGISTRY = {

    "port_scan": {
        "desc": "فحص المنافذ المفتوحة على IP أو domain",
        "args": {"host": "العنوان المراد فحصه"},
        "func": lambda a: __import__('12_osint_tools', fromlist=['OSINTTools']).OSINTTools.port_scan(a["host"])
    },
    "ip_info": {
        "desc": "معلومات عن IP (الدولة، المدينة، ISP...)",
        "args": {"ip": "عنوان IP أو domain"},
        "func": lambda a: __import__('12_osint_tools', fromlist=['OSINTTools']).OSINTTools.ip_info(a["ip"])
    },
    "dns_lookup": {
        "desc": "استعلام DNS لمعرفة IP من domain",
        "args": {"domain": "اسم النطاق"},
        "func": lambda a: __import__('12_osint_tools', fromlist=['OSINTTools']).OSINTTools.dns_lookup(a["domain"])
    },
    "subdomain_scan": {
        "desc": "فحص subdomains لموقع ما",
        "args": {"domain": "النطاق الأساسي مثل example.com"},
        "func": lambda a: __import__('12_osint_tools', fromlist=['OSINTTools']).OSINTTools.subdomains_check(a["domain"])
    },
    "my_ip": {
        "desc": "معرفة IP العام والموقع الجغرافي",
        "args": {},
        "func": lambda a: __import__('12_osint_tools', fromlist=['OSINTTools']).OSINTTools.my_ip_info()
    },
    "web_headers": {
        "desc": "عرض HTTP headers لموقع",
        "args": {"url": "رابط الموقع"},
        "func": lambda a: __import__('12_osint_tools', fromlist=['OSINTTools']).OSINTTools.headers(a["url"])
    },

    "scan_xss": {
        "desc": "فحص ثغرة XSS في موقع",
        "args": {"url": "رابط الموقع"},
        "func": lambda a: __import__('13_web_tools', fromlist=['WebScanner']).WebScanner.scan_xss(a["url"])
    },
    "scan_sqli": {
        "desc": "فحص ثغرة SQL Injection في موقع",
        "args": {"url": "رابط الموقع"},
        "func": lambda a: __import__('13_web_tools', fromlist=['WebScanner']).WebScanner.scan_sqli(a["url"])
    },
    "full_scan": {
        "desc": "فحص شامل للموقع (XSS + SQLi + Headers)",
        "args": {"url": "رابط الموقع"},
        "func": lambda a: __import__('13_web_tools', fromlist=['WebScanner']).WebScanner.full_scan(a["url"])
    },
    "scrape_url": {
        "desc": "استخراج الروابط والإيميلات وأرقام الهاتف من موقع",
        "args": {"url": "رابط الموقع"},
        "func": lambda a: __import__('13_web_tools', fromlist=['WebScraper']).WebScraper.extract(a["url"])
    },

    "system_stats": {
        "desc": "إحصاءات النظام: CPU، RAM، Disk، Uptime",
        "args": {},
        "func": lambda a: __import__('08_resource_monitor', fromlist=['ResourceMonitor']).ResourceMonitor.get_system_stats()
    },
    "list_processes": {
        "desc": "عرض العمليات الجارية مرتبة حسب الذاكرة",
        "args": {},
        "func": lambda a: __import__('07_task_manager', fromlist=['TaskManager']).TaskManager.list_processes()[:20]
    },
    "kill_process": {
        "desc": "إنهاء عملية بالـ PID",
        "args": {"pid": "رقم العملية PID"},
        "func": lambda a: __import__('07_task_manager', fromlist=['TaskManager']).TaskManager.kill_process(int(a["pid"]))
    },
    "find_process": {
        "desc": "البحث عن عملية بالاسم",
        "args": {"name": "اسم العملية أو جزء منه"},
        "func": lambda a: __import__('07_task_manager', fromlist=['TaskManager']).TaskManager.find_process(a["name"])
    },
    "disk_usage": {
        "desc": "معرفة حجم مجلد أو ملف",
        "args": {"path": "المسار"},
        "func": lambda a: __import__('05_file_manager', fromlist=['FileManager']).FileManager.folder_stats(a["path"])
    },
    "find_files": {
        "desc": "البحث عن ملفات بالاسم أو الامتداد",
        "args": {"root": "مجلد البحث", "name_pattern": "نمط الاسم (اختياري)", "extension": "الامتداد بدون نقطة (اختياري)"},
        "func": lambda a: __import__('05_file_manager', fromlist=['FileManager']).FileManager.search(
            a.get("root", "."), a.get("name_pattern", ""), a.get("extension", "")
        )
    },
    "find_duplicates": {
        "desc": "إيجاد الملفات المكررة في مجلد",
        "args": {"path": "المسار"},
        "func": lambda a: {k: v for k, v in __import__('05_file_manager', fromlist=['FileManager']).FileManager.find_duplicates(a["path"]).items()}
    },
    "organize_files": {
        "desc": "تنظيم ملفات مجلد تلقائياً حسب النوع",
        "args": {"path": "المسار"},
        "func": lambda a: __import__('05_file_manager', fromlist=['FileManager']).FileManager.organize_by_type(a["path"])
    },

    "analyze_apk": {
        "desc": "تحليل ملف APK واستخراج معلوماته",
        "args": {"path": "مسار ملف APK"},
        "func": lambda a: __import__('02_apk_analyzer', fromlist=['APKAnalyzer']).APKAnalyzer.analyze(a["path"])
    },

    "sqlite_tables": {
        "desc": "عرض جداول قاعدة بيانات SQLite",
        "args": {"db_path": "مسار قاعدة البيانات"},
        "func": lambda a: __import__('11_sqlite_analyzer', fromlist=['SQLiteAnalyzer']).SQLiteAnalyzer.list_tables(a["db_path"])
    },
    "sqlite_query": {
        "desc": "تنفيذ استعلام SQL على قاعدة بيانات",
        "args": {"db_path": "مسار قاعدة البيانات", "sql": "الاستعلام"},
        "func": lambda a: __import__('11_sqlite_analyzer', fromlist=['SQLiteAnalyzer']).SQLiteAnalyzer.query(a["db_path"], a["sql"])
    },
    "sqlite_search": {
        "desc": "البحث عن قيمة في كل جداول قاعدة البيانات",
        "args": {"db_path": "مسار قاعدة البيانات", "term": "الكلمة المراد البحث عنها"},
        "func": lambda a: __import__('11_sqlite_analyzer', fromlist=['SQLiteAnalyzer']).SQLiteAnalyzer.search_value(a["db_path"], a["term"])
    },

    "hash_text": {
        "desc": "حساب هاش نص (MD5/SHA256/SHA512...)",
        "args": {"text": "النص"},
        "func": lambda a: __import__('18_hash_text_tools', fromlist=['HashTools']).HashTools.hash_text(a["text"])
    },
    "hash_file": {
        "desc": "حساب هاش ملف",
        "args": {"path": "مسار الملف"},
        "func": lambda a: __import__('18_hash_text_tools', fromlist=['HashTools']).HashTools.hash_file_all(a["path"])
    },
    "generate_password": {
        "desc": "توليد كلمة مرور قوية",
        "args": {"length": "الطول (افتراضي 16)", "symbols": "true/false"},
        "func": lambda a: __import__('10_password_generator', fromlist=['PasswordGenerator']).PasswordGenerator.generate(
            int(a.get("length", 16)), a.get("symbols", True) not in (False, "false", "False")
        )
    },
    "check_password": {
        "desc": "فحص قوة كلمة مرور",
        "args": {"password": "كلمة المرور"},
        "func": lambda a: __import__('10_password_generator', fromlist=['PasswordGenerator']).PasswordGenerator.strength(a["password"])
    },
    "encode_base64": {
        "desc": "تشفير نص بـ Base64",
        "args": {"text": "النص"},
        "func": lambda a: __import__('18_hash_text_tools', fromlist=['TextTools']).TextTools.encode_base64(a["text"])
    },
    "decode_base64": {
        "desc": "فك تشفير Base64",
        "args": {"text": "النص المشفر"},
        "func": lambda a: __import__('18_hash_text_tools', fromlist=['TextTools']).TextTools.decode_base64(a["text"])
    },

    "send_sms": {
        "desc": "إرسال رسالة SMS",
        "args": {"number": "رقم الهاتف", "message": "نص الرسالة"},
        "func": lambda a: __import__('03_termux_api', fromlist=['SMSTools']).SMSTools.send_sms(a["number"], a["message"])
    },
    "read_sms": {
        "desc": "قراءة آخر رسائل SMS الواردة",
        "args": {"limit": "عدد الرسائل (افتراضي 10)"},
        "func": lambda a: __import__('03_termux_api', fromlist=['SMSTools']).SMSTools.list_sms(int(a.get("limit", 10)))
    },
    "send_notification": {
        "desc": "إرسال إشعار للجهاز",
        "args": {"title": "عنوان الإشعار", "message": "محتوى الإشعار"},
        "func": lambda a: __import__('03_termux_api', fromlist=['NotificationTools']).NotificationTools.send(a["title"], a["message"])
    },
    "get_location": {
        "desc": "الحصول على الموقع الجغرافي الحالي",
        "args": {},
        "func": lambda a: __import__('03_termux_api', fromlist=['LocationTools']).LocationTools.format_location()
    },
    "battery_status": {
        "desc": "معرفة حالة البطارية",
        "args": {},
        "func": lambda a: __import__('03_termux_api', fromlist=['DeviceInfo']).DeviceInfo.battery()
    },
    "wifi_scan": {
        "desc": "مسح شبكات WiFi المتاحة",
        "args": {},
        "func": lambda a: __import__('03_termux_api', fromlist=['WifiTools']).WifiTools.find_networks_by_security()
    },
    "take_photo": {
        "desc": "التقاط صورة بالكاميرا",
        "args": {"filename": "اسم الملف (اختياري)"},
        "func": lambda a: __import__('03_termux_api', fromlist=['CameraTools']).CameraTools.take_photo(a.get("filename", "photo.jpg"))
    },
    "clipboard_get": {
        "desc": "قراءة محتوى الحافظة",
        "args": {},
        "func": lambda a: __import__('03_termux_api', fromlist=['ClipboardTools']).ClipboardTools.get()
    },
    "clipboard_set": {
        "desc": "كتابة نص في الحافظة",
        "args": {"text": "النص"},
        "func": lambda a: __import__('03_termux_api', fromlist=['ClipboardTools']).ClipboardTools.set(a["text"])
    },

    "adb_screenshot": {
        "desc": "التقاط لقطة شاشة عبر ADB",
        "args": {"filename": "اسم الملف (اختياري)"},
        "func": lambda a: __import__('04_adb_controller', fromlist=['ADBInput']).ADBInput.screenshot(a.get("filename", "screen.png"))
    },
    "adb_tap": {
        "desc": "نقر على إحداثيات الشاشة عبر ADB",
        "args": {"x": "الإحداثية X", "y": "الإحداثية Y"},
        "func": lambda a: __import__('04_adb_controller', fromlist=['ADBInput']).ADBInput.tap(int(a["x"]), int(a["y"]))
    },
    "adb_type": {
        "desc": "كتابة نص عبر ADB",
        "args": {"text": "النص المراد كتابته"},
        "func": lambda a: __import__('04_adb_controller', fromlist=['ADBInput']).ADBInput.type_text(a["text"])
    },
    "adb_key": {
        "desc": "ضغط مفتاح عبر ADB (HOME/BACK/ENTER...)",
        "args": {"key": "اسم المفتاح"},
        "func": lambda a: __import__('04_adb_controller', fromlist=['ADBInput']).ADBInput.key(a["key"])
    },
    "adb_open_app": {
        "desc": "فتح تطبيق عبر ADB بالـ package name",
        "args": {"package": "اسم الحزمة مثل com.whatsapp"},
        "func": lambda a: __import__('04_adb_controller', fromlist=['ADBApps']).ADBApps.start_app(a["package"])
    },
    "adb_list_apps": {
        "desc": "قائمة التطبيقات المثبتة عبر ADB",
        "args": {},
        "func": lambda a: __import__('04_adb_controller', fromlist=['ADBApps']).ADBApps.list_apps()
    },
    "adb_device_info": {
        "desc": "معلومات الجهاز عبر ADB",
        "args": {},
        "func": lambda a: __import__('04_adb_controller', fromlist=['ADBConnection']).ADBConnection.device_info()
    },

    "speed_test": {
        "desc": "قياس سرعة الإنترنت",
        "args": {},
        "func": lambda a: __import__('16_speed_test', fromlist=['SpeedTest']).SpeedTest.full_test()
    },
    "ping": {
        "desc": "قياس زمن الاستجابة لعنوان ما",
        "args": {"host": "العنوان"},
        "func": lambda a: __import__('16_speed_test', fromlist=['SpeedTest']).SpeedTest.ping(a["host"])
    },

    "extract_from_text": {
        "desc": "استخراج IPs وروابط وإيميلات وأرقام هاتف من نص",
        "args": {"text": "النص"},
        "func": lambda a: {
            "ips":    __import__('18_hash_text_tools', fromlist=['TextTools']).TextTools.extract_ips(a["text"]),
            "urls":   __import__('18_hash_text_tools', fromlist=['TextTools']).TextTools.extract_urls(a["text"]),
            "emails": __import__('18_hash_text_tools', fromlist=['TextTools']).TextTools.extract_emails(a["text"]),
            "phones": __import__('18_hash_text_tools', fromlist=['TextTools']).TextTools.extract_phones(a["text"]),
        }
    },
    "qr_generate": {
        "desc": "إنشاء QR Code لرابط أو نص",
        "args": {"data": "النص أو الرابط"},
        "func": lambda a: __import__('18_hash_text_tools', fromlist=['QRGenerator']).QRGenerator.to_text_art(a["data"])
    },
}

def _build_tools_list() -> str:
    lines = []
    for name, info in TOOLS_REGISTRY.items():
        args_str = ", ".join(f"{k}: {v}" for k, v in info["args"].items()) if info["args"] else "لا يحتاج arguments"
        lines.append(f'- {name}: {info["desc"]} | args: {{{args_str}}}')
    return "\n".join(lines)

SYSTEM_PROMPT = """أنت مساعد ذكي يتحكم بأدوات نظام على أندرويد.

عندما يطلب المستخدم شيئاً يمكنك تنفيذه، رد بـ JSON فقط بهذا الشكل:
{"action": "tool_name", "args": {"arg1": "val1"}, "message": "رسالة قصيرة للمستخدم"}

عندما يكون السؤال عاماً أو لا يحتاج تنفيذ أداة، رد بـ JSON هكذا:
{"action": "chat", "args": {}, "message": "ردك هنا"}

عندما تريد تنفيذ أدوات متعددة بالتسلسل:
{"action": "multi", "steps": [{"action": "tool1", "args": {}}, {"action": "tool2", "args": {}}], "message": "سأنفذ خطوتين"}

الأدوات المتاحة:
{tools}

قواعد مهمة:
- رد بـ JSON صالح فقط، لا تضف أي نص خارج الـ JSON
- لا تخترع أدوات غير موجودة في القائمة
- إذا طُلب شيء خارج قدرتك قل ذلك في حقل message مع action: chat
- الـ args يجب أن تكون strings"""

def build_prompt(user_input: str, history: list) -> str:
    tools_list = _build_tools_list()
    system = SYSTEM_PROMPT.replace("{tools}", tools_list)

    context = ""
    if history:
        recent = history[-4:]
        context = "\nالمحادثة السابقة:\n"
        for turn in recent:
            context += f"مستخدم: {turn['user']}\n"
            if turn.get("result_summary"):
                context += f"نتيجة: {turn['result_summary']}\n"

    return f"{system}{context}\n\nطلب المستخدم الآن: {user_input}\n\nردك (JSON فقط):"

def _extract_json(text: str) -> dict:
    """استخراج JSON من رد الـ AI حتى لو فيه نص إضافي"""
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}', text, re.DOTALL)
    for m in matches:
        try:
            return json.loads(m)
        except Exception:
            pass

    start = text.find('{')
    end   = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1])
        except Exception:
            pass

    return {"action": "chat", "args": {}, "message": text}

def execute_tool(action: str, args: dict) -> tuple:
    """تنفيذ أداة وإرجاع (success, result)"""
    if action not in TOOLS_REGISTRY:
        return False, f"الأداة '{action}' غير موجودة."

    try:
        result = TOOLS_REGISTRY[action]["func"](args)
        return True, result
    except KeyError as e:
        return False, f"argument ناقص: {e}"
    except Exception as e:
        return False, f"خطأ في التنفيذ: {e}"

def _format_result(result) -> str:
    """تحويل النتيجة لنص مقروء"""
    if isinstance(result, (dict, list)):
        return json.dumps(result, ensure_ascii=False, indent=2, default=str)
    return str(result)

def _summarize_result(result) -> str:
    """ملخص قصير للنتيجة لإضافته للـ context"""
    text = _format_result(result)
    return text[:300] + "..." if len(text) > 300 else text

class UASAgent:
    def __init__(self):
        self.history = []
        self._ai_available = False
        self._init_ai()

    def _init_ai(self):
        try:
            import aielostora
            self._ai = aielostora
            self._ai_available = True
        except ImportError:
            self._ai_available = False

    def _call_ai(self, prompt: str) -> str:
        if not self._ai_available:
            return json.dumps({"action": "chat", "args": {},
                               "message": "⚠ aielostora غير مثبتة. نفّذ: pip install aielostora"})
        try:
            response = self._ai.gemini(prompt)
            return response if response else "{}"
        except Exception as e:
            return json.dumps({"action": "chat", "args": {}, "message": f"خطأ AI: {e}"})

    def _explain_result(self, action: str, result, success: bool) -> str:
        """يطلب من الـ AI شرح النتيجة بالعربي"""
        if not success:
            return result

        result_text = _format_result(result)
        prompt = f"""لخّص هذه النتيجة بالعربي في جملة أو جملتين بشكل واضح ومفيد:
الأداة المُنفَّذة: {action}
النتيجة:
{result_text[:1000]}

ملخص:"""
        try:
            return self._ai.gemini(prompt)
        except Exception:
            return result_text

    def process(self, user_input: str) -> str:
        """المعالج الرئيسي — يأخذ الأمر وينفذه"""

        prompt   = build_prompt(user_input, self.history)
        ai_reply = self._call_ai(prompt)
        parsed   = _extract_json(ai_reply)

        action  = parsed.get("action", "chat")
        args    = parsed.get("args", {})
        message = parsed.get("message", "")

        output_parts = []

        if action == "chat":
            result = message
            self.history.append({"user": user_input, "result_summary": message[:100]})
            return message

        elif action in TOOLS_REGISTRY:
            print(f"\n  🔧 تنفيذ: {action} {args}")
            success, result = execute_tool(action, args)

            result_text = _format_result(result)
            explanation = self._explain_result(action, result, success) if success else result

            self.history.append({
                "user": user_input,
                "action": action,
                "result_summary": _summarize_result(result)
            })

            output_parts.append(f"{'✅' if success else '❌'} {explanation}")
            if success and len(result_text) < 2000:
                output_parts.append(f"\n📊 النتيجة الكاملة:\n{result_text}")

            return "\n".join(output_parts)

        elif action == "multi":
            steps   = parsed.get("steps", [])
            results = []

            print(f"\n  🔗 تنفيذ {len(steps)} خطوات...")
            for i, step in enumerate(steps, 1):
                step_action = step.get("action", "")
                step_args   = step.get("args", {})
                if step_action not in TOOLS_REGISTRY:
                    results.append(f"  {i}. ❌ '{step_action}' غير موجود")
                    continue
                print(f"     {i}. {step_action}...")
                success, result = execute_tool(step_action, step_args)
                results.append(f"  {i}. {'✅' if success else '❌'} {step_action}: {_summarize_result(result)}")

            combined = "\n".join(results)
            self.history.append({"user": user_input, "result_summary": combined[:200]})
            return f"{message}\n\n{combined}" if message else combined

        else:
            return message or "لم أفهم الطلب."

class C:
    R="\033[0m";B="\033[1m";DIM="\033[2m"
    RED="\033[91m";GRN="\033[92m";YEL="\033[93m"
    CYN="\033[96m";WHT="\033[97m";MAG="\033[95m"

def c(col,t): return f"{col}{t}{C.R}"

EXAMPLES = [
    "افحص المنافذ المفتوحة على 8.8.8.8",
    "كم بطاريتي الآن؟",
    "ابحث عن ملفات Python في مجلد /sdcard",
    "ولّد لي كلمة مرور قوية 20 حرف",
    "افحص موقع example.com عن ثغرات XSS",
    "ما هو IP الخاص بي؟",
    "استخرج الإيميلات من هذا النص: تواصل معنا على test@email.com",
    "خذ لقطة شاشة الآن",
    "احسب SHA256 لنص hello world",
    "فحص شامل لموقع testphp.vulnweb.com",
]

def print_help():
    print(f"\n{c(C.YEL+C.B, '── أمثلة على ما يمكنك قوله ──')}")
    for i, ex in enumerate(EXAMPLES, 1):
        print(f"  {c(C.DIM, str(i)+'.')} {ex}")
    print(f"\n  {c(C.DIM, 'أوامر خاصة: help | tools | history | clear | exit')}")

def print_tools():
    print(f"\n{c(C.CYN+C.B, '── الأدوات المتاحة ──')}")
    for name, info in TOOLS_REGISTRY.items():
        print(f"  {c(C.YEL, name):<30} {info['desc']}")

def run():
    agent = UASAgent()

    os.system("clear" if os.name!="nt" else "cls")
    print(f"""
{c(C.MAG+C.B,'╔══════════════════════════════════════════════════════════╗')}
{c(C.MAG,'║')} {c(C.CYN+C.B,'    UAS Agent — تحكم بالأدوات بالعربي               ')}{c(C.MAG,'║')}
{c(C.MAG,'║')} {c(C.YEL,f'    {len(TOOLS_REGISTRY)} أداة متاحة | مدعوم بـ Gemini/GPT              ')}{c(C.MAG,'║')}
{c(C.MAG,'╚══════════════════════════════════════════════════════════╝')}
""")

    if not agent._ai_available:
        print(c(C.RED, "  ⚠ aielostora غير مثبتة!\n  نفّذ: pip install aielostora\n"))

    print_help()

    while True:
        print()
        try:
            user_input = input(f"{c(C.YEL+C.B,'أنت')} => ").strip()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{c(C.GRN,'وداعاً!')}"); break

        if not user_input:
            continue

        if user_input.lower() in ("exit","quit","خروج"):
            print(c(C.GRN,"وداعاً! 👋")); break
        elif user_input.lower() in ("help","مساعدة"):
            print_help(); continue
        elif user_input.lower() in ("tools","الأدوات"):
            print_tools(); continue
        elif user_input.lower() in ("history","التاريخ"):
            print(json.dumps(agent.history, indent=2, ensure_ascii=False)); continue
        elif user_input.lower() in ("clear","مسح"):
            agent.history = []
            print(c(C.GRN,"✅ تم مسح التاريخ.")); continue

        print(f"{c(C.DIM,'  ⏳ جاري المعالجة...')}")
        response = agent.process(user_input)
        print(f"\n{c(C.CYN+C.B,'Agent')} => {response}")

if __name__ == "__main__":
    run()
