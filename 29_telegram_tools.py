"""
أدوات بوت تلجرام — 30 ميزة
pip install telethon
"""
import os, sys, json, asyncio, time, re
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

try:
    from telethon import TelegramClient, events
    from telethon.tl.functions.messages import GetHistoryRequest
    from telethon.tl.functions.channels import GetParticipantsRequest
    from telethon.tl.types import ChannelParticipantsSearch, InputPeerEmpty
    from telethon.tl.functions.account import GetAuthorizationsRequest
    _TELETHON = True
except ImportError:
    _TELETHON = False

CONFIG_FILE = os.path.join(BASE_DIR, ".tg_config.json")

def _load_config():
    if os.path.exists(CONFIG_FILE):
        return json.load(open(CONFIG_FILE))
    return {}

def _save_config(cfg):
    json.dump(cfg, open(CONFIG_FILE,'w'), indent=2)
    os.chmod(CONFIG_FILE, 0o600)

def _client():
    cfg = _load_config()
    if not cfg.get("api_id"):
        raise Exception("لم يتم الإعداد. نفّذ الإعداد أولاً.")
    return TelegramClient(
        os.path.join(BASE_DIR, "tg_session"),
        cfg["api_id"], cfg["api_hash"]
    )

def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

class TelegramTools:

    @staticmethod
    def setup(api_id: str, api_hash: str, phone: str):
        _save_config({"api_id": int(api_id), "api_hash": api_hash, "phone": phone})
        return "✅ تم حفظ الإعدادات."

    @staticmethod
    def login():
        async def _do():
            cfg = _load_config()
            async with _client() as cl:
                await cl.start(phone=cfg["phone"])
                me = await cl.get_me()
                return f"✅ مسجل دخول: {me.first_name} (@{me.username})"
        return _run(_do())

    @staticmethod
    def send_message(entity: str, text: str):
        async def _do():
            async with _client() as cl:
                await cl.send_message(entity, text)
                return f"✅ أُرسلت إلى {entity}"
        return _run(_do())

    @staticmethod
    def send_file(entity: str, path: str, caption=""):
        async def _do():
            async with _client() as cl:
                await cl.send_file(entity, path, caption=caption)
                return f"✅ أُرسل الملف: {path}"
        return _run(_do())

    @staticmethod
    def get_messages(entity: str, limit=20):
        async def _do():
            async with _client() as cl:
                msgs = await cl.get_messages(entity, limit=limit)
                return [{"id":m.id,"date":str(m.date)[:16],"from":getattr(m.sender,"username",""),"text":(m.text or "")[:100]} for m in msgs]
        return _run(_do())

    @staticmethod
    def get_dialogs(limit=20):
        async def _do():
            async with _client() as cl:
                dialogs = await cl.get_dialogs(limit=limit)
                return [{"name":d.name,"id":d.id,"type":type(d.entity).__name__,"unread":d.unread_count} for d in dialogs]
        return _run(_do())

    @staticmethod
    def download_media(entity: str, msg_id: int, out_dir="."):
        async def _do():
            async with _client() as cl:
                msg  = await cl.get_messages(entity, ids=msg_id)
                path = await cl.download_media(msg, file=out_dir)
                return f"✅ محفوظ: {path}"
        return _run(_do())

    @staticmethod
    def forward_message(from_entity: str, to_entity: str, msg_id: int):
        async def _do():
            async with _client() as cl:
                await cl.forward_messages(to_entity, msg_id, from_entity)
                return f"✅ تم التوجيه."
        return _run(_do())

    @staticmethod
    def delete_messages(entity: str, msg_ids: list):
        async def _do():
            async with _client() as cl:
                await cl.delete_messages(entity, msg_ids)
                return f"✅ حُذفت {len(msg_ids)} رسالة."
        return _run(_do())

    @staticmethod
    def get_entity_info(entity: str):
        async def _do():
            async with _client() as cl:
                ent = await cl.get_entity(entity)
                return {
                    "id":       ent.id,
                    "type":     type(ent).__name__,
                    "title":    getattr(ent,"title",None) or getattr(ent,"first_name",""),
                    "username": getattr(ent,"username",""),
                }
        return _run(_do())

    @staticmethod
    def get_participants(group: str, limit=100):
        async def _do():
            async with _client() as cl:
                participants = await cl.get_participants(group, limit=limit)
                return [{"id":p.id,"name":f"{p.first_name or ''} {p.last_name or ''}".strip(),"username":p.username or ""} for p in participants]
        return _run(_do())

    @staticmethod
    def search_messages(entity: str, query: str, limit=20):
        async def _do():
            async with _client() as cl:
                msgs = await cl.get_messages(entity, search=query, limit=limit)
                return [{"id":m.id,"date":str(m.date)[:16],"text":(m.text or "")[:150]} for m in msgs]
        return _run(_do())

    @staticmethod
    def get_profile_photo(entity: str, out="profile.jpg"):
        async def _do():
            async with _client() as cl:
                path = await cl.download_profile_photo(entity, file=out)
                return f"✅ {path}"
        return _run(_do())

    @staticmethod
    def edit_message(entity: str, msg_id: int, new_text: str):
        async def _do():
            async with _client() as cl:
                await cl.edit_message(entity, msg_id, new_text)
                return "✅ تم التعديل."
        return _run(_do())

    @staticmethod
    def pin_message(entity: str, msg_id: int):
        async def _do():
            async with _client() as cl:
                await cl.pin_message(entity, msg_id)
                return "✅ تم التثبيت."
        return _run(_do())

    @staticmethod
    def send_bulk(entities: list, text: str, delay=2):
        results = []
        for ent in entities:
            r = TelegramTools.send_message(ent, text)
            results.append({"entity":ent,"result":r})
            time.sleep(delay)
        return results

    @staticmethod
    def auto_reply_bot(entity: str, rules: dict):
        """قاموس rules: {keyword: reply}"""
        async def _do():
            async with _client() as cl:
                @cl.on(events.NewMessage(chats=entity))
                async def handler(event):
                    text = event.message.text or ""
                    for kw, reply in rules.items():
                        if kw.lower() in text.lower():
                            await event.reply(reply)
                            break
                print(f"🤖 بوت الرد التلقائي يعمل على {entity}")
                await cl.run_until_disconnected()
        _run(_do())

    @staticmethod
    def export_chat_history(entity: str, out="chat_history.json", limit=500):
        async def _do():
            async with _client() as cl:
                msgs = await cl.get_messages(entity, limit=limit)
                data = [{"id":m.id,"date":str(m.date),"from":getattr(m.sender,"username",""),"text":m.text or ""} for m in msgs]
                json.dump(data, open(out,'w',encoding='utf-8'), indent=2, ensure_ascii=False)
                return f"✅ {len(data)} رسالة → {out}"
        return _run(_do())

    @staticmethod
    def schedule_message(entity: str, text: str, at: str):
        """at: HH:MM"""
        from datetime import datetime
        now  = datetime.now()
        h,m  = map(int, at.split(":"))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= now:
            import datetime as dt
            target += dt.timedelta(days=1)
        diff = (target - now).total_seconds()
        print(f"⏰ سيُرسل في {at} ({diff:.0f}ث)")
        time.sleep(diff)
        return TelegramTools.send_message(entity, text)

    @staticmethod
    def get_active_sessions():
        async def _do():
            async with _client() as cl:
                auths = await cl(GetAuthorizationsRequest())
                return [{"device":a.device_model,"app":a.app_name,"date_active":str(a.date_active)[:16]} for a in auths.authorizations]
        return _run(_do())

    @staticmethod
    def broadcast_to_groups(text: str):
        async def _do():
            async with _client() as cl:
                dialogs = await cl.get_dialogs()
                groups = [d for d in dialogs if d.is_group or d.is_channel]
                sent = 0
                for g in groups[:20]:
                    try:
                        await cl.send_message(g.id, text)
                        sent += 1
                        await asyncio.sleep(3)
                    except Exception: pass
                return f"✅ أُرسل إلى {sent} مجموعة"
        return _run(_do())

    @staticmethod
    def monitor_new_messages(entity: str, keyword="", save_to="tg_monitor.json"):
        async def _do():
            data = []
            async with _client() as cl:
                @cl.on(events.NewMessage(chats=entity))
                async def handler(event):
                    text = event.message.text or ""
                    if not keyword or keyword.lower() in text.lower():
                        entry = {"date":str(event.message.date)[:16],"text":text[:200]}
                        data.append(entry)
                        print(f"📨 {entry['date']}: {text[:80]}")
                        json.dump(data, open(save_to,'w',encoding='utf-8'), indent=2, ensure_ascii=False)
                print(f"👀 مراقبة {entity} — Ctrl+C للإيقاف")
                await cl.run_until_disconnected()
        _run(_do())

    @staticmethod
    def leave_group(entity: str):
        async def _do():
            async with _client() as cl:
                await cl.delete_dialog(entity)
                return f"✅ تم مغادرة {entity}"
        return _run(_do())

    @staticmethod
    def get_unread():
        async def _do():
            async with _client() as cl:
                dialogs = await cl.get_dialogs()
                return [{"name":d.name,"unread":d.unread_count} for d in dialogs if d.unread_count > 0]
        return _run(_do())

    @staticmethod
    def mark_all_read():
        async def _do():
            async with _client() as cl:
                dialogs = await cl.get_dialogs()
                for d in dialogs:
                    if d.unread_count > 0:
                        await cl.mark_read(d.id)
                return "✅ تم قراءة كل الرسائل."
        return _run(_do())

if __name__ == "__main__":
    if not _TELETHON:
        print("❌ pip install telethon")
        sys.exit(1)

    tg = TelegramTools()
    menu = {
        "1":  ("إعداد API",                lambda: print(tg.setup(input("API ID => "), input("API Hash => "), input("رقم الهاتف (+966...) => ")))),
        "2":  ("تسجيل الدخول",             lambda: print(tg.login())),
        "3":  ("إرسال رسالة",              lambda: print(tg.send_message(input("Entity (username/id) => "), input("النص => ")))),
        "4":  ("إرسال ملف",               lambda: print(tg.send_file(input("Entity => "), input("مسار الملف => "), input("Caption => ")))),
        "5":  ("قراءة رسائل",              lambda: print(json.dumps(tg.get_messages(input("Entity => "), int(input("العدد (20) => ") or 20)), indent=2, ensure_ascii=False))),
        "6":  ("قائمة المحادثات",          lambda: [print(f"  {d['name']:<30} {d['type']:<12} غير مقروء: {d['unread']}") for d in tg.get_dialogs()]),
        "7":  ("معلومات Entity",           lambda: print(json.dumps(tg.get_entity_info(input("Username/ID => ")), indent=2, ensure_ascii=False))),
        "8":  ("قائمة الأعضاء",            lambda: [print(f"  @{m['username']:<20} {m['name']}") for m in tg.get_participants(input("Group => "), int(input("العدد (100) => ") or 100))]),
        "9":  ("بحث في رسائل",             lambda: print(json.dumps(tg.search_messages(input("Entity => "), input("بحث => ")), indent=2, ensure_ascii=False))),
        "10": ("تحميل ميديا",              lambda: print(tg.download_media(input("Entity => "), int(input("Message ID => "))))),
        "11": ("توجيه رسالة",              lambda: print(tg.forward_message(input("من => "), input("إلى => "), int(input("Message ID => "))))),
        "12": ("حذف رسائل",               lambda: print(tg.delete_messages(input("Entity => "), list(map(int, input("IDs (مسافة) => ").split()))))),
        "13": ("تعديل رسالة",              lambda: print(tg.edit_message(input("Entity => "), int(input("Message ID => ")), input("النص الجديد => ")))),
        "14": ("تثبيت رسالة",              lambda: print(tg.pin_message(input("Entity => "), int(input("Message ID => "))))),
        "15": ("تصدير سجل محادثة",         lambda: print(tg.export_chat_history(input("Entity => "), input("ملف الإخراج (chat.json) => ") or "chat.json"))),
        "16": ("رسالة مجدولة",            lambda: print(tg.schedule_message(input("Entity => "), input("النص => "), input("الوقت (HH:MM) => ")))),
        "17": ("الجلسات النشطة",           lambda: print(json.dumps(tg.get_active_sessions(), indent=2, ensure_ascii=False))),
        "18": ("غير مقروء",               lambda: [print(f"  {d['name']}: {d['unread']}") for d in tg.get_unread()]),
        "19": ("قراءة الكل",              lambda: print(tg.mark_all_read())),
        "20": ("مراقبة رسائل جديدة",       lambda: tg.monitor_new_messages(input("Entity => "), input("كلمة مفتاحية (اختياري) => "))),
        "21": ("بوت رد تلقائي",           lambda: tg.auto_reply_bot(input("Entity => "), {input(f"كلمة {i+1} => "):input(f"رد {i+1} => ") for i in range(int(input("عدد القواعد => ") or 1))})),
        "22": ("إرسال دفعي",              lambda: print(json.dumps(tg.send_bulk(input("Entities (مسافة) => ").split(), input("النص => ")), indent=2, ensure_ascii=False))),
        "23": ("بث لكل المجموعات",        lambda: print(tg.broadcast_to_groups(input("النص => ")))),
        "24": ("مغادرة مجموعة",           lambda: print(tg.leave_group(input("Entity => ")))),
        "25": ("صورة البروفايل",           lambda: print(tg.get_profile_photo(input("Username => ")))),
    }
    while True:
        print("\n═"*45)
        print("  📱  Telegram Tools — 25 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
