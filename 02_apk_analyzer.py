"""
تحليل ملفات APK
مكاتب: stdlib فقط (zipfile, os, re)
"""
import os
import re
import json
import zipfile
import hashlib

class APKAnalyzer:

    @staticmethod
    def analyze(apk_path: str) -> dict:
        if not os.path.exists(apk_path):
            return {"error": "الملف غير موجود."}
        try:
            with zipfile.ZipFile(apk_path, 'r') as apk:
                files = apk.namelist()
                dex_files  = [f for f in files if f.endswith('.dex')]
                native_libs= [f for f in files if f.startswith('lib/')]
                assets     = [f for f in files if f.startswith('assets/')]
                info = {
                    "الملف":                apk_path,
                    "الحجم":               f"{os.path.getsize(apk_path)/(1024*1024):.2f} MB",
                    "MD5":                  APKAnalyzer._file_hash(apk_path),
                    "عدد الملفات":          len(files),
                    "ملفات DEX":            dex_files,
                    "مكتبات Native":        list(set(re.findall(r'lib/([^/]+)/', '\n'.join(native_libs)))),
                    "الأصول (Assets)":      len(assets),
                    "موارد":               "resources.arsc" in files,
                    "توقيع V1/V2":         "META-INF/CERT.RSA" in files or "META-INF/CERT.DSA" in files,
                    "الأذونات":            APKAnalyzer._extract_permissions(apk),
                    "معلومات التطبيق":     APKAnalyzer._extract_app_info(apk),
                }
            return info
        except zipfile.BadZipFile:
            return {"error": "الملف ليس APK صالحاً."}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def _file_hash(path):
        try:
            h = hashlib.md5()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return "N/A"

    @staticmethod
    def _extract_permissions(apk_zip):
        try:
            raw  = apk_zip.read('AndroidManifest.xml')
            text = raw.decode('utf-8', errors='ignore')
            perms = re.findall(r'android\.permission\.[A-Z_]+', text)
            return sorted(set(perms)) if perms else ["Manifest مشفر - تعذر القراءة"]
        except Exception:
            return ["AndroidManifest.xml غير موجود"]

    @staticmethod
    def _extract_app_info(apk_zip):
        try:
            raw    = apk_zip.read('AndroidManifest.xml').decode('utf-8', errors='ignore')
            pkg    = re.search(r'package[=\s]+"?([a-zA-Z0-9._]+)"?', raw)
            sdk    = re.search(r'minSdkVersion[=\s]+"?(\d+)"?', raw)
            target = re.search(r'targetSdkVersion[=\s]+"?(\d+)"?', raw)
            return {
                "package":          pkg.group(1) if pkg else "N/A",
                "minSdkVersion":    sdk.group(1) if sdk else "N/A",
                "targetSdkVersion": target.group(1) if target else "N/A",
            }
        except Exception:
            return {}

if __name__ == "__main__":
    path   = input("مسار APK => ").strip()
    result = APKAnalyzer.analyze(path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
