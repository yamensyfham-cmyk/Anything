"""
إدارة جهات الاتصال — stdlib فقط
"""
import os, csv, json

class ContactManager:
    def __init__(self, filename="contacts.csv"):
        self.filename = filename
        self.contacts = self._load()

    def _load(self):
        if not os.path.exists(self.filename): return []
        with open(self.filename, 'r', encoding='utf-8', newline='') as f:
            return list(csv.DictReader(f))

    def _save(self):
        if not self.contacts: return
        with open(self.filename, 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=["name","phone","email","note"])
            w.writeheader(); w.writerows(self.contacts)

    def add(self, name, phone="", email="", note=""):
        self.contacts.append({"name":name,"phone":phone,"email":email,"note":note})
        self._save(); return "✅ تمت الإضافة."

    def list(self): return self.contacts

    def search(self, q):
        q = q.lower()
        return [c for c in self.contacts if any(q in str(v).lower() for v in c.values())]

    def delete(self, name):
        before = len(self.contacts)
        self.contacts = [c for c in self.contacts if c["name"] != name]
        self._save()
        return "✅ تم الحذف." if len(self.contacts) < before else "❌ غير موجود."

    def export_vcf(self, out="contacts.vcf"):
        with open(out, 'w', encoding='utf-8') as f:
            for c in self.contacts:
                f.write("BEGIN:VCARD\nVERSION:3.0\n")
                f.write(f"FN:{c['name']}\n")
                if c.get("phone"): f.write(f"TEL:{c['phone']}\n")
                if c.get("email"): f.write(f"EMAIL:{c['email']}\n")
                if c.get("note"):  f.write(f"NOTE:{c['note']}\n")
                f.write("END:VCARD\n")
        return f"✅ تصدير VCF: {out}"

    def import_vcf(self, vcf_path):
        if not os.path.exists(vcf_path): return "❌ الملف غير موجود."
        added = 0
        with open(vcf_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        import re
        for card in re.split(r'BEGIN:VCARD', content)[1:]:
            name  = re.search(r'FN:(.*)', card)
            phone = re.search(r'TEL[^:]*:(.*)', card)
            email = re.search(r'EMAIL[^:]*:(.*)', card)
            if name:
                self.add(
                    name.group(1).strip(),
                    phone.group(1).strip() if phone else "",
                    email.group(1).strip() if email else "",
                )
                added += 1
        return f"✅ تم استيراد {added} جهة اتصال."

if __name__ == "__main__":
    cm = ContactManager()
    while True:
        print("\n1-إضافة  2-عرض  3-بحث  4-حذف  5-تصدير VCF  6-استيراد VCF  0-خروج")
        ch = input("=> ").strip()
        if ch == "0": break
        elif ch == "1": print(cm.add(input("الاسم => "), input("الهاتف => "), input("البريد => "), input("ملاحظة => ")))
        elif ch == "2":
            for c in cm.list(): print(f"  📞 {c['name']} | {c['phone']} | {c['email']}")
        elif ch == "3":
            for c in cm.search(input("بحث => ")): print(f"  {c}")
        elif ch == "4": print(cm.delete(input("الاسم => ")))
        elif ch == "5": print(cm.export_vcf())
        elif ch == "6": print(cm.import_vcf(input("مسار VCF => ")))
