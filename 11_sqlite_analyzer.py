"""
محلل قواعد البيانات SQLite — مثالي لقواعد بيانات أندرويد
مكاتب: stdlib فقط (sqlite3)
"""
import sqlite3
import os
import json
import csv
import re

class SQLiteAnalyzer:

    @staticmethod
    def list_tables(db_path: str) -> list:
        try:
            with sqlite3.connect(db_path) as c:
                cur = c.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
                return [r[0] for r in cur.fetchall()]
        except Exception as e: return [f"خطأ: {e}"]

    @staticmethod
    def schema(db_path: str) -> dict:
        try:
            with sqlite3.connect(db_path) as c:
                cur = c.cursor()
                cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
                return {r[0]: r[1] for r in cur.fetchall()}
        except Exception as e: return {"error": str(e)}

    @staticmethod
    def query(db_path: str, sql: str, params=()) -> dict:
        try:
            with sqlite3.connect(db_path) as c:
                c.row_factory = sqlite3.Row
                cur = c.cursor()
                cur.execute(sql, params)
                if cur.description:
                    cols = [d[0] for d in cur.description]
                    rows = [list(r) for r in cur.fetchall()]
                    return {"columns": cols, "rows": rows, "count": len(rows)}
                c.commit()
                return {"affected": cur.rowcount}
        except Exception as e: return {"error": str(e)}

    @staticmethod
    def view_table(db_path: str, table: str, limit=20, offset=0) -> dict:
        return SQLiteAnalyzer.query(db_path, f"SELECT * FROM [{table}] LIMIT ? OFFSET ?", (limit, offset))

    @staticmethod
    def table_info(db_path: str, table: str) -> dict:
        try:
            with sqlite3.connect(db_path) as c:
                cur = c.cursor()
                cur.execute(f"PRAGMA table_info([{table}]);")
                cols   = [{"id":r[0],"name":r[1],"type":r[2],"notnull":r[3],"default":r[4],"pk":r[5]} for r in cur.fetchall()]
                cur.execute(f"SELECT COUNT(*) FROM [{table}];")
                count  = cur.fetchone()[0]
                return {"columns": cols, "row_count": count}
        except Exception as e: return {"error": str(e)}

    @staticmethod
    def export_csv(db_path: str, table: str, out_path: str) -> str:
        try:
            data = SQLiteAnalyzer.view_table(db_path, table, limit=999999)
            if "error" in data: return f"❌ {data['error']}"
            with open(out_path, 'w', encoding='utf-8', newline='') as f:
                w = csv.writer(f)
                w.writerow(data['columns'])
                w.writerows(data['rows'])
            return f"✅ تم التصدير: {out_path} ({len(data['rows'])} صف)"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def search_value(db_path: str, search_term: str) -> dict:
        """بحث في كل الجداول والأعمدة"""
        results = {}
        tables  = SQLiteAnalyzer.list_tables(db_path)
        for table in tables:
            info = SQLiteAnalyzer.table_info(db_path, table)
            if "columns" not in info: continue
            for col in info["columns"]:
                if col["type"].upper() in ("TEXT", "BLOB", "VARCHAR", ""):
                    r = SQLiteAnalyzer.query(db_path,
                        f"SELECT * FROM [{table}] WHERE [{col['name']}] LIKE ? LIMIT 5",
                        (f"%{search_term}%",))
                    if r.get("rows"):
                        results[f"{table}.{col['name']}"] = r
        return results

    @staticmethod
    def read_whatsapp_messages(db_path: str, limit=50) -> dict:
        """قراءة رسائل WhatsApp (msgstore.db)"""
        queries = [
            "SELECT key_remote_jid, data, timestamp FROM messages ORDER BY timestamp DESC LIMIT ?",
            "SELECT remote_jid, message_text, timestamp FROM messages ORDER BY timestamp DESC LIMIT ?",
        ]
        for q in queries:
            r = SQLiteAnalyzer.query(db_path, q, (limit,))
            if "rows" in r: return r
        return {"error": "تعذر قراءة قاعدة بيانات WhatsApp"}

    @staticmethod
    def read_sms_db(db_path: str, limit=50) -> dict:
        """قراءة قاعدة بيانات SMS"""
        return SQLiteAnalyzer.query(db_path,
            "SELECT address, body, date, type FROM sms ORDER BY date DESC LIMIT ?", (limit,))

if __name__ == "__main__":
    db = input("مسار قاعدة البيانات => ").strip()
    if not os.path.exists(db):
        print("❌ الملف غير موجود."); exit()

    tables = SQLiteAnalyzer.list_tables(db)
    print(f"\n📊 الجداول ({len(tables)}): {', '.join(tables)}")

    while True:
        print("\n1-عرض جدول  2-بحث  3-استعلام SQL  4-تصدير CSV  5-معلومات جدول  0-خروج")
        ch = input("=> ").strip()
        if ch == "0": break
        elif ch == "1":
            t = input("اسم الجدول => ").strip()
            r = SQLiteAnalyzer.view_table(db, t)
            if "columns" in r:
                print(" | ".join(r["columns"]))
                print("─" * 60)
                for row in r["rows"][:20]:
                    print(" | ".join(str(v)[:20] for v in row))
                print(f"\n({r['count']} صف)")
            else: print(r)
        elif ch == "2":
            term = input("كلمة البحث => ").strip()
            results = SQLiteAnalyzer.search_value(db, term)
            print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
        elif ch == "3":
            sql = input("SQL => ").strip()
            print(json.dumps(SQLiteAnalyzer.query(db, sql), indent=2, ensure_ascii=False, default=str))
        elif ch == "4":
            t   = input("الجدول => ").strip()
            out = input("ملف الإخراج (.csv) => ").strip() or f"{t}.csv"
            print(SQLiteAnalyzer.export_csv(db, t, out))
        elif ch == "5":
            t = input("الجدول => ").strip()
            print(json.dumps(SQLiteAnalyzer.table_info(db, t), indent=2, ensure_ascii=False))
