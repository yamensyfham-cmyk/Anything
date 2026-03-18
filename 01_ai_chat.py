"""
محرك الذكاء الاصطناعي مع ذاكرة سياقية
مكاتب: aielostora + stdlib
"""
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

class AIMaster:
    def __init__(self):
        self.model    = "1"
        self.mem_file = "ai_memory.json"
        self.history  = self._load()
        self._hist    = []

    def _load(self):
        if os.path.exists(self.mem_file):
            try:
                with open(self.mem_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        with open(self.mem_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def ask(self, question: str) -> str:
        try:
            import aielostora
            if self.model == "1":
                resp = aielostora.gemini(question)
            else:
                resp = aielostora.gpt3(question)
        except ImportError:
            return "❌ aielostora غير مثبتة. نفّذ: pip install aielostora"
        except Exception as e:
            return f"❌ خطأ: {e}"

        self._hist.append({"role": "user",  "text": question})
        self._hist.append({"role": "model", "text": resp})
        if len(self._hist) > 20:
            self._hist = self._hist[-20:]
        self.history.append({"user": question, "bot": resp})
        if len(self.history) > 100:
            self.history = self.history[-100:]
        self._save()
        return resp

    def clear_history(self):
        self.history = []
        self._hist   = []
        self._save()
        return "✅ تم مسح التاريخ."

    def export_chat(self, filename="chat_export.txt"):
        if not self.history:
            return "لا يوجد تاريخ للتصدير."
        with open(filename, 'w', encoding='utf-8') as f:
            for turn in self.history:
                f.write(f"أنت: {turn['user']}\n")
                f.write(f"AI: {turn['bot']}\n\n")
        return f"✅ تم التصدير: {filename}"

if __name__ == "__main__":
    ai = AIMaster()
    print("1- Gemini  |  2- ChatGPT")
    ai.model = input("النموذج => ").strip() or "1"
    print("اكتب 'خروج' للإنهاء | 'مسح' | 'تصدير'\n")
    while True:
        try:
            q = input("أنت => ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not q: continue
        if q == "خروج": break
        if q == "مسح":   print(ai.clear_history()); continue
        if q == "تصدير": print(ai.export_chat());   continue
        print(f"\n🤖 AI => {ai.ask(q)}\n")
