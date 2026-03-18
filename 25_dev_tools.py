"""
أدوات المطورين — 25 ميزة
مكاتب: stdlib فقط + requests اختياري
"""
import os, sys, json, re, subprocess, time, hashlib, ast
import urllib.request, urllib.parse
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

class DevTools:

    @staticmethod
    def _git(args: list, cwd=".") -> str:
        try:
            r = subprocess.run(["git"]+args, capture_output=True, text=True, cwd=cwd, timeout=30)
            return r.stdout.strip() or r.stderr.strip()
        except FileNotFoundError: return "❌ git غير مثبت. نفّذ: pkg install git"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def git_status(path=".") -> str:
        return DevTools._git(["status", "--short"], path)

    @staticmethod
    def git_log(path=".", count=10) -> str:
        return DevTools._git(["log", f"--oneline", f"-{count}"], path)

    @staticmethod
    def git_diff(path=".") -> str:
        return DevTools._git(["diff"], path)

    @staticmethod
    def git_clone(url: str, dest=".") -> str:
        return DevTools._git(["clone", url, dest])

    @staticmethod
    def git_commit(path=".", message="update") -> str:
        DevTools._git(["add", "-A"], path)
        return DevTools._git(["commit", "-m", message], path)

    @staticmethod
    def git_push(path=".", remote="origin", branch="main") -> str:
        return DevTools._git(["push", remote, branch], path)

    @staticmethod
    def git_pull(path=".") -> str:
        return DevTools._git(["pull"], path)

    @staticmethod
    def git_branches(path=".") -> str:
        return DevTools._git(["branch", "-a"], path)

    @staticmethod
    def git_init(path=".") -> str:
        return DevTools._git(["init"], path)

    @staticmethod
    def analyze_python(path: str) -> dict:
        """تحليل ملف Python"""
        try:
            code = open(path, encoding='utf-8', errors='ignore').read()
            tree = ast.parse(code)
            classes   = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            imports   = []
            for n in ast.walk(tree):
                if isinstance(n, ast.Import):
                    imports += [a.name for a in n.names]
                elif isinstance(n, ast.ImportFrom):
                    if n.module: imports.append(n.module)
            lines = code.split('\n')
            return {
                "ملف":       path,
                "أسطر":      len(lines),
                "أسطر_كود":  len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
                "أسطر_تعليق":len([l for l in lines if l.strip().startswith('#')]),
                "classes":   classes,
                "functions": functions,
                "imports":   list(set(imports)),
                "syntax":    "✅ صحيح" if True else "❌",
            }
        except SyntaxError as e:
            return {"خطأ": f"Syntax Error: {e}"}
        except Exception as e:
            return {"خطأ": str(e)}

    @staticmethod
    def find_todos(folder: str) -> list:
        """ابحث عن TODO/FIXME/HACK في الكود"""
        results = []
        pattern = re.compile(r'#\s*(TODO|FIXME|HACK|NOTE|XXX|BUG)\s*:?\s*(.*)', re.I)
        for root, _, files in os.walk(folder):
            for fname in files:
                if fname.endswith(('.py','.js','.ts','.java','.kt','.c','.cpp')):
                    path = os.path.join(root, fname)
                    try:
                        for i, line in enumerate(open(path, errors='ignore'), 1):
                            m = pattern.search(line)
                            if m:
                                results.append({"file":path,"line":i,"type":m.group(1),"text":m.group(2).strip()})
                    except Exception: pass
        return results

    @staticmethod
    def count_lines(folder: str) -> dict:
        """عد أسطر الكود حسب اللغة"""
        ext_lang = {'.py':'Python','.js':'JavaScript','.ts':'TypeScript',
                    '.java':'Java','.kt':'Kotlin','.c':'C','.cpp':'C++',
                    '.html':'HTML','.css':'CSS','.sh':'Shell','.go':'Go'}
        stats = {}
        for root, _, files in os.walk(folder):
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in ext_lang:
                    lang = ext_lang[ext]
                    try:
                        count = sum(1 for _ in open(os.path.join(root,fname), errors='ignore'))
                        stats[lang] = stats.get(lang, 0) + count
                    except Exception: pass
        return dict(sorted(stats.items(), key=lambda x:-x[1]))

    @staticmethod
    def api_test(method: str, url: str, headers: dict=None,
                 params: dict=None, body: dict=None) -> dict:
        """اختبار API endpoint"""
        if params:
            url += '?' + urllib.parse.urlencode(params)
        req_headers = {"Content-Type":"application/json","User-Agent":"UAS-Dev/1.0"}
        if headers: req_headers.update(headers)
        data = json.dumps(body).encode() if body else None
        req  = urllib.request.Request(url, data=data, headers=req_headers, method=method.upper())
        t0   = time.time()
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body_resp = r.read().decode('utf-8','replace')
                try:    body_json = json.loads(body_resp)
                except Exception: body_json = body_resp[:500]
                return {
                    "status":   r.status,
                    "time_ms":  round((time.time()-t0)*1000),
                    "headers":  dict(r.headers),
                    "body":     body_json,
                }
        except urllib.request.HTTPError as e:
            return {"status": e.code, "time_ms": round((time.time()-t0)*1000),
                    "body": e.read().decode('utf-8','replace')[:500]}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def load_test(url: str, requests_count=10, concurrency=5) -> dict:
        """اختبار الحمل على API"""
        import threading
        results = []
        errors  = []
        lock    = threading.Lock()

        def make_request():
            t0 = time.time()
            try:
                urllib.request.urlopen(url, timeout=15)
                ms = round((time.time()-t0)*1000)
                with lock: results.append(ms)
            except Exception as e:
                with lock: errors.append(str(e)[:30])

        total_start = time.time()
        threads = []
        for _ in range(requests_count):
            while len([t for t in threads if t.is_alive()]) >= concurrency:
                time.sleep(0.01)
            t = threading.Thread(target=make_request)
            threads.append(t); t.start()
        for t in threads: t.join()
        total_time = time.time() - total_start

        if results:
            return {
                "طلبات":    requests_count,
                "ناجحة":    len(results),
                "فاشلة":    len(errors),
                "avg_ms":   round(sum(results)/len(results)),
                "min_ms":   min(results),
                "max_ms":   max(results),
                "RPS":      round(requests_count/total_time,1),
            }
        return {"error": "كل الطلبات فشلت", "errors": errors[:5]}

    @staticmethod
    def json_to_csv(json_path: str, csv_path: str) -> str:
        import csv
        try:
            data = json.load(open(json_path, encoding='utf-8'))
            if isinstance(data, dict): data = [data]
            with open(csv_path,'w',encoding='utf-8',newline='') as f:
                if data:
                    w = csv.DictWriter(f, fieldnames=data[0].keys())
                    w.writeheader(); w.writerows(data)
            return f"✅ {csv_path}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def csv_to_json(csv_path: str, json_path: str) -> str:
        import csv
        try:
            with open(csv_path, encoding='utf-8-sig') as f:
                data = list(csv.DictReader(f))
            json.dump(data, open(json_path,'w',encoding='utf-8'), indent=2, ensure_ascii=False)
            return f"✅ {json_path} ({len(data)} سجل)"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def xml_to_json(xml_path: str, json_path: str) -> str:
        import xml.etree.ElementTree as ET
        def elem_to_dict(elem):
            d = {}
            if elem.text and elem.text.strip(): d["_text"] = elem.text.strip()
            if elem.attrib: d.update(elem.attrib)
            for child in elem:
                child_data = elem_to_dict(child)
                if child.tag in d:
                    if not isinstance(d[child.tag], list): d[child.tag] = [d[child.tag]]
                    d[child.tag].append(child_data)
                else:
                    d[child.tag] = child_data
            return d
        try:
            tree = ET.parse(xml_path)
            data = {tree.getroot().tag: elem_to_dict(tree.getroot())}
            json.dump(data, open(json_path,'w',encoding='utf-8'), indent=2, ensure_ascii=False)
            return f"✅ {json_path}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def format_json(path: str, indent=2) -> str:
        try:
            data = json.load(open(path, encoding='utf-8'))
            json.dump(data, open(path,'w',encoding='utf-8'), indent=indent, ensure_ascii=False)
            return f"✅ تم تنسيق {path}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def validate_json(path: str) -> str:
        try:
            json.load(open(path, encoding='utf-8'))
            return "✅ JSON صالح"
        except json.JSONDecodeError as e:
            return f"❌ خطأ في السطر {e.lineno}: {e.msg}"

    @staticmethod
    def minify_json(path: str, out: str) -> str:
        try:
            data = json.load(open(path, encoding='utf-8'))
            open(out,'w',encoding='utf-8').write(json.dumps(data, ensure_ascii=False, separators=(',',':')))
            size_before = os.path.getsize(path)
            size_after  = os.path.getsize(out)
            return f"✅ {size_before}B → {size_after}B (وفّر {size_before-size_after}B)"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def generate_uuid(count=1) -> list:
        import uuid
        return [str(uuid.uuid4()) for _ in range(count)]

    @staticmethod
    def timestamp_convert(ts=None) -> dict:
        import datetime
        now = ts or time.time()
        dt  = datetime.datetime.fromtimestamp(float(now))
        return {
            "unix":  int(now),
            "iso":   dt.isoformat(),
            "human": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "utc":   datetime.datetime.utcfromtimestamp(float(now)).isoformat() + "Z",
        }

    @staticmethod
    def diff_files(path1: str, path2: str) -> str:
        """مقارنة ملفين نصيين"""
        import difflib
        try:
            lines1 = open(path1, encoding='utf-8', errors='ignore').readlines()
            lines2 = open(path2, encoding='utf-8', errors='ignore').readlines()
            diff   = list(difflib.unified_diff(lines1, lines2, fromfile=path1, tofile=path2))
            return ''.join(diff[:100]) if diff else "✅ الملفان متطابقان"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def generate_readme(folder: str) -> str:
        """توليد README.md أوتوماتيكي"""
        name   = os.path.basename(os.path.abspath(folder))
        py_files = [f for f in os.listdir(folder) if f.endswith('.py')]
        content = f"# {name}\n\n## الملفات\n"
        for f in sorted(py_files):
            path = os.path.join(folder, f)
            try:
                first_comment = ""
                for line in open(path, errors='ignore'):
                    line = line.strip()
                    if line.startswith('"""') or line.startswith("'''"):
                        first_comment = line.strip('"').strip("'").strip()
                        break
                content += f"- `{f}` — {first_comment}\n"
            except Exception: content += f"- `{f}`\n"
        out = os.path.join(folder, "README.md")
        open(out,'w',encoding='utf-8').write(content)
        return f"✅ {out}"

if __name__ == "__main__":
    dt = DevTools()
    menu = {
        "1":  ("Git Status",            lambda: print(dt.git_status(input("المجلد (.) => ") or "."))),
        "2":  ("Git Log",               lambda: print(dt.git_log(input("المجلد (.) => ") or "."))),
        "3":  ("Git Clone",             lambda: print(dt.git_clone(input("URL => "), input("الوجهة => ")))),
        "4":  ("Git Commit + Push",     lambda: (print(dt.git_commit(input("المجلد => "), input("الرسالة => "))), print(dt.git_push(input("المجلد => "))))),
        "5":  ("تحليل Python",          lambda: print(json.dumps(dt.analyze_python(input("مسار الملف => ")), indent=2, ensure_ascii=False))),
        "6":  ("ابحث عن TODO",          lambda: [print(f"  [{r['type']}] {r['file']}:{r['line']} — {r['text']}") for r in dt.find_todos(input("المجلد => "))]),
        "7":  ("عد أسطر الكود",         lambda: print(json.dumps(dt.count_lines(input("المجلد => ")), indent=2, ensure_ascii=False))),
        "8":  ("اختبار API",            lambda: print(json.dumps(dt.api_test(input("Method (GET) => ") or "GET", input("URL => ")), indent=2, ensure_ascii=False))),
        "9":  ("اختبار الحمل",          lambda: print(json.dumps(dt.load_test(input("URL => "), int(input("طلبات (10) => ") or 10)), indent=2, ensure_ascii=False))),
        "10": ("JSON → CSV",            lambda: print(dt.json_to_csv(input("JSON => "), input("CSV => ")))),
        "11": ("CSV → JSON",            lambda: print(dt.csv_to_json(input("CSV => "), input("JSON => ")))),
        "12": ("XML → JSON",            lambda: print(dt.xml_to_json(input("XML => "), input("JSON => ")))),
        "13": ("تنسيق JSON",            lambda: print(dt.format_json(input("JSON => ")))),
        "14": ("ضغط JSON",              lambda: print(dt.minify_json(input("JSON => "), input("الإخراج => ")))),
        "15": ("توليد UUID",            lambda: [print(u) for u in dt.generate_uuid(int(input("العدد (1) => ") or 1))]),
        "16": ("تحويل Timestamp",       lambda: print(json.dumps(dt.timestamp_convert(input("Unix timestamp (فارغ=الآن) => ") or None), indent=2))),
        "17": ("مقارنة ملفين",          lambda: print(dt.diff_files(input("الملف 1 => "), input("الملف 2 => ")))),
        "18": ("توليد README",          lambda: print(dt.generate_readme(input("المجلد => ")))),
    }
    while True:
        print("\n═"*45)
        print("  💻  Dev Tools — 18 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
