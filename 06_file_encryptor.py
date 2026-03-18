"""
تشفير وفك تشفير الملفات
يستخدم: mini_crypto (AES-256-CBC + Fernet)
"""
import os
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
from mini_crypto import Fernet, aes_encrypt_cbc, aes_decrypt_cbc, pbkdf2
import os
import base64
import hashlib

def _kbytes(key: str) -> bytes:
    return hashlib.sha256(key.encode()).digest()

def _xor(data: bytes, key: str) -> bytes:
    kb = _kbytes(key)
    return bytes(b ^ kb[i % 32] for i, b in enumerate(data))

def _new_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode()

class FileEncryptor:

    def __init__(self, key=None):
        self.key = key or _new_key()

    def encrypt_file(self, filepath: str) -> str:
        try:
            data      = open(filepath, 'rb').read()
            encrypted = _xor(data, self.key)
            checksum  = hashlib.sha256(data).digest()
            out       = filepath + '.enc'
            with open(out, 'wb') as f:
                f.write(checksum + encrypted)
            return f"✅ مشفر: {out}\n🔑 المفتاح: {self.key}"
        except Exception as e:
            return f"❌ {e}"

    def decrypt_file(self, filepath: str, key: str) -> str:
        try:
            raw       = open(filepath, 'rb').read()
            checksum  = raw[:32]
            encrypted = raw[32:]
            decrypted = _xor(encrypted, key)
            if hashlib.sha256(decrypted).digest() != checksum:
                return "❌ مفتاح خاطئ أو الملف تالف."
            out = filepath[:-4] if filepath.endswith('.enc') else filepath + '.dec'
            open(out, 'wb').write(decrypted)
            return f"✅ فُك التشفير: {out}"
        except Exception as e:
            return f"❌ {e}"

    def encrypt_text(self, text: str) -> str:
        encrypted = _xor(text.encode(), self.key)
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt_text(self, encoded: str, key: str) -> str:
        try:
            encrypted = base64.urlsafe_b64decode(encoded.encode())
            return _xor(encrypted, key).decode()
        except Exception as e:
            return f"❌ {e}"

if __name__ == "__main__":
    enc = FileEncryptor()
    print("🔐 File Encryptor — XOR+SHA256 (stdlib فقط)")
    print("1- تشفير ملف  |  2- فك تشفير  |  3- تشفير نص  |  4- فك تشفير نص")
    ch = input("=> ").strip()
    if ch == "1":
        print(enc.encrypt_file(input("مسار الملف => ").strip()))
    elif ch == "2":
        print(enc.decrypt_file(input("مسار الملف المشفر => ").strip(), input("المفتاح => ").strip()))
    elif ch == "3":
        t = input("النص => ").strip()
        r = enc.encrypt_text(t)
        print(f"مشفر: {r}\nمفتاح: {enc.key}")
    elif ch == "4":
        t = input("المشفر => ").strip()
        k = input("المفتاح => ").strip()
        print(enc.decrypt_text(t, k))
