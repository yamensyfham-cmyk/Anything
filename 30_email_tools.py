"""
أدوات البريد الإلكتروني — 25 ميزة
مكاتب: stdlib فقط (smtplib, imaplib, email)
"""
import os, sys, json, smtplib, imaplib, email, time, re
import email.mime.text, email.mime.multipart, email.mime.base
import email.encoders, email.header
from datetime import datetime
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

CONFIG_FILE = os.path.join(BASE_DIR, ".email_config.json")

SMTP_SERVERS = {
    "gmail":   ("smtp.gmail.com",   465),
    "outlook": ("smtp.office365.com",587),
    "yahoo":   ("smtp.mail.yahoo.com",465),
    "icloud":  ("smtp.mail.me.com",  587),
    "zoho":    ("smtp.zoho.com",     465),
}
IMAP_SERVERS = {
    "gmail":   ("imap.gmail.com",   993),
    "outlook": ("outlook.office365.com",993),
    "yahoo":   ("imap.mail.yahoo.com",993),
    "icloud":  ("imap.mail.me.com",  993),
    "zoho":    ("imap.zoho.com",     993),
}

def _load(): return json.load(open(CONFIG_FILE)) if os.path.exists(CONFIG_FILE) else {}
def _save(c): json.dump(c,open(CONFIG_FILE,'w'),indent=2); os.chmod(CONFIG_FILE,0o600)
def _decode_header(h):
    parts = email.header.decode_header(h)
    return ''.join(p.decode(enc or 'utf-8','replace') if isinstance(p,bytes) else p for p,enc in parts)

class EmailTools:

    @staticmethod
    def setup(address: str, password: str, provider="gmail"):
        _save({"address":address,"password":password,"provider":provider})
        return "✅ تم حفظ الإعدادات."

    @staticmethod
    def send(to: str, subject: str, body: str, html=False, attachments=None):
        cfg = _load()
        if not cfg: return "❌ نفّذ الإعداد أولاً."
        provider = cfg.get("provider","gmail")
        host,port = SMTP_SERVERS.get(provider,("smtp.gmail.com",465))
        msg = email.mime.multipart.MIMEMultipart()
        msg['From'] = cfg["address"]; msg['To'] = to; msg['Subject'] = subject
        content_type = 'html' if html else 'plain'
        msg.attach(email.mime.text.MIMEText(body, content_type, 'utf-8'))
        if attachments:
            for path in attachments:
                if not os.path.exists(path): continue
                with open(path,'rb') as f:
                    part = email.mime.base.MIMEBase('application','octet-stream')
                    part.set_payload(f.read())
                    email.encoders.encode_base64(part)
                    part.add_header('Content-Disposition','attachment',filename=os.path.basename(path))
                    msg.attach(part)
        try:
            if port == 465:
                import ssl
                with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as s:
                    s.login(cfg["address"], cfg["password"])
                    s.send_message(msg)
            else:
                with smtplib.SMTP(host, port) as s:
                    s.starttls()
                    s.login(cfg["address"], cfg["password"])
                    s.send_message(msg)
            return f"✅ أُرسل إلى {to}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def send_bulk(recipients: list, subject: str, body: str, delay=2):
        results = []
        for to in recipients:
            r = EmailTools.send(to, subject, body)
            results.append({"to":to,"result":r})
            time.sleep(delay)
        return results

    @staticmethod
    def send_html(to: str, subject: str, html_body: str):
        return EmailTools.send(to, subject, html_body, html=True)

    @staticmethod
    def send_with_attachment(to: str, subject: str, body: str, file_paths: list):
        return EmailTools.send(to, subject, body, attachments=file_paths)

    @staticmethod
    def send_template(to: str, template: str, variables: dict):
        """استبدال {{variable}} في قالب"""
        body = template
        for k,v in variables.items():
            body = body.replace(f"{{{{{k}}}}}", str(v))
        subject = variables.get("subject","رسالة من UAS")
        return EmailTools.send(to, subject, body)

    @staticmethod
    def _imap():
        cfg = _load()
        if not cfg: raise Exception("نفّذ الإعداد أولاً.")
        provider = cfg.get("provider","gmail")
        host,port = IMAP_SERVERS.get(provider,("imap.gmail.com",993))
        m = imaplib.IMAP4_SSL(host, port)
        m.login(cfg["address"], cfg["password"])
        return m

    @staticmethod
    def inbox(limit=20, folder="INBOX") -> list:
        try:
            m = EmailTools._imap()
            m.select(folder)
            _,data = m.search(None,'ALL')
            ids = data[0].split()[-limit:]
            messages = []
            for mid in reversed(ids):
                _,raw = m.fetch(mid,'(RFC822)')
                msg = email.message_from_bytes(raw[0][1])
                messages.append({
                    "id":      mid.decode(),
                    "from":    _decode_header(msg.get("From","")),
                    "subject": _decode_header(msg.get("Subject","")),
                    "date":    msg.get("Date","")[:25],
                    "read":    "\\Seen" in (msg.get("Flags","") or ""),
                })
            m.logout()
            return messages
        except Exception as e: return [{"error":str(e)}]

    @staticmethod
    def read_email(msg_id: str, folder="INBOX") -> dict:
        try:
            m = EmailTools._imap()
            m.select(folder)
            _,raw = m.fetch(msg_id,'(RFC822)')
            msg  = email.message_from_bytes(raw[0][1])
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8','replace')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8','replace')
            m.logout()
            return {
                "from":    _decode_header(msg.get("From","")),
                "to":      _decode_header(msg.get("To","")),
                "subject": _decode_header(msg.get("Subject","")),
                "date":    msg.get("Date",""),
                "body":    body[:3000],
            }
        except Exception as e: return {"error":str(e)}

    @staticmethod
    def search_emails(query: str, folder="INBOX", limit=20) -> list:
        try:
            m = EmailTools._imap()
            m.select(folder)
            criteria = f'(SUBJECT "{query}")'
            _,data = m.search(None,criteria)
            ids = data[0].split()[-limit:]
            messages = []
            for mid in ids:
                _,raw = m.fetch(mid,'(RFC822)')
                msg = email.message_from_bytes(raw[0][1])
                messages.append({
                    "id":      mid.decode(),
                    "from":    _decode_header(msg.get("From","")),
                    "subject": _decode_header(msg.get("Subject","")),
                    "date":    msg.get("Date","")[:25],
                })
            m.logout()
            return messages
        except Exception as e: return [{"error":str(e)}]

    @staticmethod
    def unread_count(folder="INBOX") -> int:
        try:
            m = EmailTools._imap()
            m.select(folder)
            _,data = m.search(None,'UNSEEN')
            count = len(data[0].split()) if data[0] else 0
            m.logout()
            return count
        except Exception as e: return -1

    @staticmethod
    def list_folders() -> list:
        try:
            m = EmailTools._imap()
            _,folders = m.list()
            m.logout()
            return [f.decode().split('"."')[-1].strip().strip('"') for f in folders]
        except Exception as e: return [str(e)]

    @staticmethod
    def delete_email(msg_id: str, folder="INBOX") -> str:
        try:
            import imaplib
            m = EmailTools._imap()
            m.select(folder)
            m.store(msg_id,'+FLAGS','\\Deleted')
            m.expunge()
            m.logout()
            return f"✅ حُذفت الرسالة {msg_id}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def move_email(msg_id: str, from_folder: str, to_folder: str) -> str:
        try:
            m = EmailTools._imap()
            m.select(from_folder)
            m.copy(msg_id, to_folder)
            m.store(msg_id,'+FLAGS','\\Deleted')
            m.expunge()
            m.logout()
            return f"✅ نُقلت إلى {to_folder}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def download_attachments(msg_id: str, out_dir=".", folder="INBOX") -> list:
        saved = []
        try:
            m = EmailTools._imap()
            m.select(folder)
            _,raw = m.fetch(msg_id,'(RFC822)')
            msg  = email.message_from_bytes(raw[0][1])
            m.logout()
            os.makedirs(out_dir, exist_ok=True)
            for part in msg.walk():
                if part.get_content_maintype() == 'multipart': continue
                if not part.get('Content-Disposition'): continue
                fname = part.get_filename()
                if fname:
                    fname = _decode_header(fname)
                    path  = os.path.join(out_dir, fname)
                    open(path,'wb').write(part.get_payload(decode=True))
                    saved.append(path)
        except Exception as e: saved.append(f"❌ {e}")
        return saved

    @staticmethod
    def mark_read(msg_id: str, folder="INBOX") -> str:
        try:
            m = EmailTools._imap()
            m.select(folder)
            m.store(msg_id,'+FLAGS','\\Seen')
            m.logout()
            return "✅ علّمت كمقروءة."
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def auto_reply(keyword: str, reply_text: str, folder="INBOX", check_interval=60):
        """رد تلقائي على رسائل تحتوي كلمة معينة"""
        replied = set()
        print(f"🔄 رد تلقائي نشط — Ctrl+C للإيقاف")
        try:
            while True:
                try:
                    msgs = EmailTools.search_emails(keyword, folder, 5)
                    for msg in msgs:
                        mid = msg.get("id","")
                        if mid and mid not in replied:
                            sender = msg.get("from","")
                            addr   = re.search(r'<(.+?)>',sender)
                            addr   = addr.group(1) if addr else sender
                            if addr and '@' in addr:
                                EmailTools.send(addr, f"Re: {msg.get('subject','')}",
                                               reply_text)
                                replied.add(mid)
                                print(f"✅ رد على {addr}")
                except Exception as e:
                    print(f"⚠ {e}")
                time.sleep(check_interval)
        except KeyboardInterrupt:
            return f"⏹ توقف (ردود: {len(replied)})"

    @staticmethod
    def export_inbox(out="inbox_export.json", limit=100) -> str:
        msgs = EmailTools.inbox(limit)
        json.dump(msgs, open(out,'w',encoding='utf-8'), indent=2, ensure_ascii=False)
        return f"✅ {len(msgs)} رسالة → {out}"

    @staticmethod
    def spam_check(sender: str) -> dict:
        """فحص بسيط للمرسل"""
        domain = sender.split('@')[-1].strip('>')
        disposable = ["mailinator","tempmail","guerrillamail","10minutemail","throwaway"]
        return {
            "sender":     sender,
            "domain":     domain,
            "disposable": any(d in domain for d in disposable),
            "has_numbers":bool(re.search(r'\d{4,}',domain)),
        }

if __name__ == "__main__":
    em = EmailTools()
    menu = {
        "1":  ("إعداد البريد",             lambda: print(em.setup(input("البريد => "), input("كلمة المرور (App Password) => "), input("المزود (gmail/outlook/yahoo) => ") or "gmail"))),
        "2":  ("إرسال رسالة",              lambda: print(em.send(input("إلى => "), input("الموضوع => "), input("النص => ")))),
        "3":  ("إرسال HTML",               lambda: print(em.send_html(input("إلى => "), input("الموضوع => "), input("HTML => ")))),
        "4":  ("إرسال مع مرفق",            lambda: print(em.send_with_attachment(input("إلى => "), input("الموضوع => "), input("النص => "), input("مسارات الملفات (مسافة) => ").split()))),
        "5":  ("إرسال دفعي",               lambda: print(json.dumps(em.send_bulk(input("عناوين (مسافة) => ").split(), input("الموضوع => "), input("النص => ")), indent=2, ensure_ascii=False))),
        "6":  ("الصندوق الوارد",           lambda: [print(f"  [{m['id']:>4}] {m['date'][:16]} | {m['from'][:30]:<30} {m['subject'][:40]}") for m in em.inbox(int(input("العدد (20) => ") or 20))]),
        "7":  ("قراءة رسالة",              lambda: print(json.dumps(em.read_email(input("Message ID => ")), indent=2, ensure_ascii=False))),
        "8":  ("بحث في البريد",             lambda: [print(f"  [{m['id']}] {m['from'][:30]} — {m['subject'][:50]}") for m in em.search_emails(input("بحث => "))]),
        "9":  ("عدد غير المقروء",          lambda: print(f"📬 {em.unread_count()} رسالة غير مقروءة")),
        "10": ("قائمة المجلدات",           lambda: [print(f"  {f}") for f in em.list_folders()]),
        "11": ("تحميل المرفقات",           lambda: print(em.download_attachments(input("Message ID => "), input("مجلد الحفظ (.) => ") or "."))),
        "12": ("حذف رسالة",               lambda: print(em.delete_email(input("Message ID => ")))),
        "13": ("نقل رسالة",               lambda: print(em.move_email(input("Message ID => "), input("من مجلد => "), input("إلى مجلد => ")))),
        "14": ("تصدير الصندوق الوارد",     lambda: print(em.export_inbox(input("ملف الإخراج (inbox.json) => ") or "inbox_export.json"))),
        "15": ("رد تلقائي",               lambda: em.auto_reply(input("الكلمة المفتاحية => "), input("نص الرد => "))),
        "16": ("فحص مرسل Spam",           lambda: print(json.dumps(em.spam_check(input("عنوان البريد => ")), indent=2, ensure_ascii=False))),
    }
    while True:
        print("\n═"*45)
        print("  📧  Email Tools — 16 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
