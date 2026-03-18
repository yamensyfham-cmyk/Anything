"""
مولد كلمات المرور + فحص القوة
مكاتب: stdlib فقط (secrets, string)
"""
import secrets
import string
import hashlib
import json

class PasswordGenerator:

    CHARS_LETTERS  = string.ascii_letters
    CHARS_DIGITS   = string.digits
    CHARS_SYMBOLS  = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    @staticmethod
    def generate(length=16, symbols=True, numbers=True, uppercase=True) -> str:
        pool = PasswordGenerator.CHARS_LETTERS
        if numbers: pool += PasswordGenerator.CHARS_DIGITS
        if symbols: pool += PasswordGenerator.CHARS_SYMBOLS
        if not uppercase: pool = pool.replace(string.ascii_uppercase, "")

        pw = []
        if numbers: pw.append(secrets.choice(PasswordGenerator.CHARS_DIGITS))
        if symbols: pw.append(secrets.choice(PasswordGenerator.CHARS_SYMBOLS))
        if uppercase: pw.append(secrets.choice(string.ascii_uppercase))
        pw.append(secrets.choice(string.ascii_lowercase))

        pw += [secrets.choice(pool) for _ in range(length - len(pw))]

        secrets.SystemRandom().shuffle(pw)
        return ''.join(pw)

    @staticmethod
    def passphrase(count=4) -> str:
        words = [
            "apple","brave","cloud","dance","eagle","flame","grace","happy",
            "ivory","jolly","karma","lemon","magic","noble","ocean","peace",
            "quest","river","storm","tiger","ultra","vivid","water","xenon",
            "alpha","delta","foxtrot","hotel","india","kilo","lima","mike",
            "november","oscar","papa","romeo","sierra","tango","uniform"
        ]
        return '-'.join(secrets.choice(words) for _ in range(count))

    @staticmethod
    def strength(pw: str) -> dict:
        score = 0
        feedback = []
        if len(pw) >= 8:  score += 1
        else: feedback.append("أقصر من 8 أحرف")
        if len(pw) >= 12: score += 1
        if len(pw) >= 16: score += 1
        if any(c.isupper() for c in pw): score += 1
        else: feedback.append("لا يوجد حرف كبير")
        if any(c.islower() for c in pw): score += 1
        if any(c.isdigit() for c in pw): score += 1
        else: feedback.append("لا يوجد رقم")
        if any(c in PasswordGenerator.CHARS_SYMBOLS for c in pw): score += 1
        else: feedback.append("لا يوجد رمز")
        levels = {0:"ضعيف جداً",1:"ضعيف",2:"متوسط",3:"جيد",4:"قوي",5:"قوي جداً",6:"ممتاز",7:"لا يُكسر"}
        return {"score": score, "level": levels.get(score, "ممتاز"), "tips": feedback}

    @staticmethod
    def hash_password(pw: str) -> dict:
        """تشفير كلمة مرور بـ SHA-256 و SHA-512"""
        return {
            "sha256": hashlib.sha256(pw.encode()).hexdigest(),
            "sha512": hashlib.sha512(pw.encode()).hexdigest(),
        }

if __name__ == "__main__":
    while True:
        print("\n1-توليد  2-Passphrase  3-فحص قوة  4-هاش  0-خروج")
        ch = input("=> ").strip()
        if ch == "0": break
        elif ch == "1":
            l = int(input("الطول (16) => ") or 16)
            s = input("رموز؟ (نعم) => ").strip().lower() != "لا"
            n = input("أرقام؟ (نعم) => ").strip().lower() != "لا"
            pw = PasswordGenerator.generate(l, s, n)
            print(f"\n🔑 {pw}")
            print(json.dumps(PasswordGenerator.strength(pw), indent=2, ensure_ascii=False))
        elif ch == "2":
            c = int(input("عدد الكلمات (4) => ") or 4)
            print(f"\n🔑 {PasswordGenerator.passphrase(c)}")
        elif ch == "3":
            pw = input("كلمة المرور => ").strip()
            print(json.dumps(PasswordGenerator.strength(pw), indent=2, ensure_ascii=False))
        elif ch == "4":
            pw = input("كلمة المرور => ").strip()
            print(json.dumps(PasswordGenerator.hash_password(pw), indent=2, ensure_ascii=False))
