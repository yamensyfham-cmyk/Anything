"""
أدوات الإنتاجية — 25 ميزة
مكاتب: stdlib فقط
"""
import os, sys, json, time, threading, re, math
import sqlite3
from datetime import datetime, timedelta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

DB_PATH = os.path.join(BASE_DIR, "productivity.db")

def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY, title TEXT, content TEXT,
        tags TEXT, created TEXT, updated TEXT, pinned INTEGER DEFAULT 0)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY, task TEXT, done INTEGER DEFAULT 0,
        priority TEXT DEFAULT 'medium', due TEXT, created TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY, text TEXT, remind_at TEXT, done INTEGER DEFAULT 0)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY, amount REAL, category TEXT,
        description TEXT, date TEXT)""")
    conn.commit()
    return conn

class Notes:
    """نظام ملاحظات متكامل"""

    @staticmethod
    def add(title: str, content: str, tags="") -> str:
        now = datetime.now().isoformat()
        with _db() as db:
            db.execute("INSERT INTO notes (title,content,tags,created,updated) VALUES (?,?,?,?,?)",
                       (title, content, tags, now, now))
        return f"✅ ملاحظة '{title}' محفوظة."

    @staticmethod
    def list(tag="") -> list:
        with _db() as db:
            if tag:
                rows = db.execute("SELECT id,title,tags,updated FROM notes WHERE tags LIKE ? ORDER BY pinned DESC,updated DESC", (f"%{tag}%",)).fetchall()
            else:
                rows = db.execute("SELECT id,title,tags,updated FROM notes ORDER BY pinned DESC,updated DESC").fetchall()
        return [{"id":r[0],"title":r[1],"tags":r[2],"updated":r[3][:16]} for r in rows]

    @staticmethod
    def get(note_id: int) -> dict:
        with _db() as db:
            r = db.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
        if not r: return {}
        return {"id":r[0],"title":r[1],"content":r[2],"tags":r[3],"created":r[4],"updated":r[5]}

    @staticmethod
    def edit(note_id: int, title=None, content=None, tags=None) -> str:
        with _db() as db:
            r = db.execute("SELECT title,content,tags FROM notes WHERE id=?", (note_id,)).fetchone()
            if not r: return "❌ غير موجودة."
            db.execute("UPDATE notes SET title=?,content=?,tags=?,updated=? WHERE id=?",
                       (title or r[0], content or r[1], tags if tags is not None else r[2],
                        datetime.now().isoformat(), note_id))
        return "✅ تم التعديل."

    @staticmethod
    def delete(note_id: int) -> str:
        with _db() as db:
            db.execute("DELETE FROM notes WHERE id=?", (note_id,))
        return "✅ تم الحذف."

    @staticmethod
    def search(query: str) -> list:
        with _db() as db:
            rows = db.execute(
                "SELECT id,title,tags,updated FROM notes WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?",
                (f"%{query}%",f"%{query}%",f"%{query}%")).fetchall()
        return [{"id":r[0],"title":r[1],"tags":r[2],"updated":r[3][:16]} for r in rows]

    @staticmethod
    def pin(note_id: int) -> str:
        with _db() as db:
            curr = db.execute("SELECT pinned FROM notes WHERE id=?", (note_id,)).fetchone()
            if curr:
                db.execute("UPDATE notes SET pinned=? WHERE id=?", (1-curr[0], note_id))
                return f"✅ {'مثبتة' if 1-curr[0] else 'غير مثبتة'}"
        return "❌ غير موجودة."

    @staticmethod
    def export(out="notes_export.json") -> str:
        with _db() as db:
            rows = db.execute("SELECT * FROM notes").fetchall()
        data = [{"id":r[0],"title":r[1],"content":r[2],"tags":r[3]} for r in rows]
        json.dump(data, open(out,'w',encoding='utf-8'), indent=2, ensure_ascii=False)
        return f"✅ {len(data)} ملاحظة → {out}"

class TodoList:
    """قائمة المهام"""

    @staticmethod
    def add(task: str, priority="medium", due="") -> str:
        with _db() as db:
            db.execute("INSERT INTO todos (task,priority,due,created) VALUES (?,?,?,?)",
                       (task, priority, due, datetime.now().isoformat()))
        return f"✅ مهمة مضافة."

    @staticmethod
    def list(done=None) -> list:
        with _db() as db:
            if done is None:
                rows = db.execute("SELECT id,task,done,priority,due FROM todos ORDER BY done,priority DESC").fetchall()
            else:
                rows = db.execute("SELECT id,task,done,priority,due FROM todos WHERE done=? ORDER BY priority DESC",(int(done),)).fetchall()
        icons = {"high":"🔴","medium":"🟡","low":"🟢"}
        return [{"id":r[0],"task":r[1],"done":"✅" if r[2] else "⬜","priority":icons.get(r[3],"")+" "+r[3],"due":r[4] or ""} for r in rows]

    @staticmethod
    def done(task_id: int) -> str:
        with _db() as db:
            db.execute("UPDATE todos SET done=1 WHERE id=?", (task_id,))
        return "✅ مكتملة!"

    @staticmethod
    def delete(task_id: int) -> str:
        with _db() as db:
            db.execute("DELETE FROM todos WHERE id=?", (task_id,))
        return "✅ محذوفة."

    @staticmethod
    def clear_done() -> str:
        with _db() as db:
            n = db.execute("DELETE FROM todos WHERE done=1").rowcount
            db.commit()
        return f"✅ حُذفت {n} مهمة منجزة."

    @staticmethod
    def stats() -> dict:
        with _db() as db:
            total = db.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
            done  = db.execute("SELECT COUNT(*) FROM todos WHERE done=1").fetchone()[0]
        return {"الكل":total,"منجزة":done,"متبقية":total-done,
                "نسبة_الإنجاز":f"{done/total*100:.0f}%" if total else "0%"}

class Calculator:
    """حاسبة علمية"""

    @staticmethod
    def calc(expr: str) -> str:
        """تقييم تعبير رياضي بأمان"""
        try:
            safe = {k:getattr(math,k) for k in dir(math) if not k.startswith('_')}
            safe.update({'abs':abs,'round':round,'min':min,'max':max,'sum':sum})
            result = eval(expr.replace('^','**'), {"__builtins__":{}}, safe)
            return f"{expr} = {result}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def unit_convert(value: float, from_unit: str, to_unit: str) -> str:
        """تحويل الوحدات"""
        conversions = {

            ("km","m"):1000, ("m","km"):0.001, ("m","cm"):100, ("cm","m"):0.01,
            ("m","ft"):3.28084, ("ft","m"):0.3048, ("m","inch"):39.3701, ("inch","m"):0.0254,
            ("km","mile"):0.621371, ("mile","km"):1.60934,

            ("kg","g"):1000, ("g","kg"):0.001, ("kg","lb"):2.20462, ("lb","kg"):0.453592,
            ("kg","oz"):35.274, ("oz","kg"):0.0283495,

            ("c","f"):"(v*9/5)+32", ("f","c"):"(v-32)*5/9",
            ("c","k"):"v+273.15",   ("k","c"):"v-273.15",

            ("m2","km2"):0.000001, ("km2","m2"):1000000,
            ("m2","ft2"):10.7639,  ("ft2","m2"):0.0929,
            ("acre","m2"):4046.86, ("m2","acre"):0.000247,

            ("kmh","ms"):0.277778, ("ms","kmh"):3.6,
            ("kmh","mph"):0.621371,("mph","kmh"):1.60934,

            ("gb","mb"):1024, ("mb","gb"):1/1024,
            ("tb","gb"):1024, ("gb","tb"):1/1024,
            ("mb","kb"):1024, ("kb","mb"):1/1024,
        }
        key = (from_unit.lower(), to_unit.lower())
        conv = conversions.get(key)
        if conv is None: return f"❌ لا يوجد تحويل من {from_unit} إلى {to_unit}"
        if isinstance(conv, str):
            result = eval(conv.replace('v', str(value)))
        else:
            result = value * conv
        return f"{value} {from_unit} = {round(result, 6)} {to_unit}"

    @staticmethod
    def bmi(weight_kg: float, height_cm: float) -> dict:
        h = height_cm / 100
        bmi = weight_kg / (h**2)
        if   bmi < 18.5: status = "نقص في الوزن"
        elif bmi < 25:   status = "وزن طبيعي"
        elif bmi < 30:   status = "زيادة وزن"
        else:            status = "سمنة"
        return {"BMI": round(bmi,1), "الحالة": status}

    @staticmethod
    def loan_calculator(principal: float, rate: float, years: int) -> dict:
        """حاسبة القرض"""
        r   = rate / 100 / 12
        n   = years * 12
        pmt = principal * r * (1+r)**n / ((1+r)**n - 1) if r else principal/n
        return {
            "القسط_الشهري":     round(pmt, 2),
            "المجموع_المدفوع":  round(pmt*n, 2),
            "الفوائد_الإجمالية":round(pmt*n - principal, 2),
        }

class Reminder:
    """منبهات بسيطة"""

    @staticmethod
    def add(text: str, remind_at: str) -> str:
        """remind_at: YYYY-MM-DD HH:MM"""
        with _db() as db:
            db.execute("INSERT INTO reminders (text,remind_at) VALUES (?,?)", (text, remind_at))
        return f"✅ منبّه: {text} في {remind_at}"

    @staticmethod
    def list() -> list:
        now = datetime.now().isoformat()
        with _db() as db:
            rows = db.execute("SELECT id,text,remind_at,done FROM reminders WHERE done=0 ORDER BY remind_at").fetchall()
        return [{"id":r[0],"text":r[1],"وقت":r[2],"منتهي":r[2]<now} for r in rows]

    @staticmethod
    def check_due() -> list:
        """المنبهات المستحقة الآن"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with _db() as db:
            rows = db.execute("SELECT id,text FROM reminders WHERE done=0 AND remind_at<=?", (now,)).fetchall()
            for r in rows:
                db.execute("UPDATE reminders SET done=1 WHERE id=?", (r[0],))
        return [r[1] for r in rows]

class ExpenseTracker:
    """متتبع المصروفات"""

    @staticmethod
    def add(amount: float, category: str, desc="") -> str:
        with _db() as db:
            db.execute("INSERT INTO expenses (amount,category,description,date) VALUES (?,?,?,?)",
                       (amount, category, desc, datetime.now().strftime("%Y-%m-%d")))
        return f"✅ {amount} — {category}"

    @staticmethod
    def summary(month=None) -> dict:
        with _db() as db:
            if month:
                rows = db.execute("SELECT category,SUM(amount) FROM expenses WHERE date LIKE ? GROUP BY category", (f"{month}%",)).fetchall()
            else:
                rows = db.execute("SELECT category,SUM(amount) FROM expenses GROUP BY category").fetchall()
        totals = {r[0]:round(r[1],2) for r in rows}
        totals["الإجمالي"] = round(sum(totals.values()),2)
        return totals

    @staticmethod
    def history(limit=20) -> list:
        with _db() as db:
            rows = db.execute("SELECT amount,category,description,date FROM expenses ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
        return [{"المبلغ":r[0],"الفئة":r[1],"الوصف":r[2],"التاريخ":r[3]} for r in rows]

if __name__ == "__main__":
    notes = Notes()
    todos = TodoList()
    calc  = Calculator()
    exp   = ExpenseTracker()

    menu = {
        "1":  ("ملاحظة جديدة",         lambda: print(notes.add(input("العنوان => "), input("المحتوى => "), input("التاقات => ")))),
        "2":  ("عرض الملاحظات",        lambda: [print(f"  [{n['id']}] {n['title']} {n['tags']} — {n['updated']}") for n in notes.list()]),
        "3":  ("بحث في الملاحظات",      lambda: [print(f"  [{n['id']}] {n['title']}") for n in notes.search(input("بحث => "))]),
        "4":  ("قراءة ملاحظة",         lambda: print(json.dumps(notes.get(int(input("ID => "))), indent=2, ensure_ascii=False))),
        "5":  ("حذف ملاحظة",           lambda: print(notes.delete(int(input("ID => "))))),
        "6":  ("مهمة جديدة",           lambda: print(todos.add(input("المهمة => "), input("الأولوية (high/medium/low) => ") or "medium", input("التاريخ (YYYY-MM-DD) => ")))),
        "7":  ("عرض المهام",           lambda: [print(f"  [{t['id']}] {t['done']} {t['priority']:<15} {t['task']} {t['due']}") for t in todos.list()]),
        "8":  ("إنجاز مهمة",           lambda: print(todos.done(int(input("ID => "))))),
        "9":  ("إحصاء المهام",         lambda: print(json.dumps(todos.stats(), indent=2, ensure_ascii=False))),
        "10": ("حاسبة",                lambda: print(calc.calc(input("التعبير => ")))),
        "11": ("تحويل وحدات",          lambda: print(calc.unit_convert(float(input("القيمة => ")), input("من => "), input("إلى => ")))),
        "12": ("حاسبة BMI",            lambda: print(json.dumps(calc.bmi(float(input("الوزن (kg) => ")), float(input("الطول (cm) => "))), indent=2, ensure_ascii=False))),
        "13": ("حاسبة قرض",            lambda: print(json.dumps(calc.loan_calculator(float(input("المبلغ => ")), float(input("الفائدة% => ")), int(input("السنوات => "))), indent=2, ensure_ascii=False))),
        "14": ("منبّه جديد",            lambda: print(Reminder.add(input("النص => "), input("الوقت (YYYY-MM-DD HH:MM) => ")))),
        "15": ("عرض المنبهات",         lambda: [print(f"  [{r['id']}] {r['text']} — {r['وقت']}") for r in Reminder.list()]),
        "16": ("مصروف جديد",           lambda: print(exp.add(float(input("المبلغ => ")), input("الفئة => "), input("الوصف => ")))),
        "17": ("ملخص المصروفات",        lambda: print(json.dumps(exp.summary(input("الشهر (YYYY-MM فارغ=الكل) => ") or None), indent=2, ensure_ascii=False))),
        "18": ("سجل المصروفات",         lambda: [print(f"  {r['التاريخ']} | {r['الفئة']:<15} {r['المبلغ']}") for r in exp.history()]),
        "19": ("تصدير الملاحظات",       lambda: print(notes.export())),
    }
    while True:
        print("\n═"*45)
        print("  📝  Productivity — 19 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
