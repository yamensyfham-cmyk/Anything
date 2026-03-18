"""
مدير الملفات المتقدم
بدون أي مكاتب خارجية — stdlib فقط
"""
import os
import shutil
import hashlib
import re
import time
from datetime import datetime

def _size_str(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"

def _human_time(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")

class FileManager:

    @staticmethod
    def tree(path=".", depth=3, current=0, prefix=""):
        if current > depth: return
        try:
            entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            print(f"{prefix}[محظور]")
            return
        for i, entry in enumerate(entries):
            connector = "└── " if i == len(entries)-1 else "├── "
            icon = "📁 " if entry.is_dir() else "📄 "
            size = "" if entry.is_dir() else f"  ({_size_str(entry.stat().st_size)})"
            print(f"{prefix}{connector}{icon}{entry.name}{size}")
            if entry.is_dir() and current < depth:
                ext = "    " if i == len(entries)-1 else "│   "
                FileManager.tree(entry.path, depth, current+1, prefix+ext)

    @staticmethod
    def search(root=".", name_pattern="", extension="", min_size=0, max_size=0,
               contains_text="", modified_days=0) -> list:
        results = []
        pat = re.compile(name_pattern, re.IGNORECASE) if name_pattern else None
        now = time.time()
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for fname in files:
                full = os.path.join(dirpath, fname)
                try:
                    stat = os.stat(full)
                    size = stat.st_size

                    if pat and not pat.search(fname): continue
                    if extension and not fname.lower().endswith(f".{extension.lstrip('.')}"): continue
                    if min_size and size < min_size * 1024: continue
                    if max_size and size > max_size * 1024 * 1024: continue
                    if modified_days and (now - stat.st_mtime) > modified_days * 86400: continue
                    if contains_text:
                        try:
                            with open(full, 'r', encoding='utf-8', errors='ignore') as f:
                                if contains_text.lower() not in f.read(1024*512).lower():
                                    continue
                        except Exception:
                            continue
                    results.append({
                        "path":     full,
                        "size":     _size_str(size),
                        "modified": _human_time(stat.st_mtime),
                    })
                except (PermissionError, OSError):
                    pass
        return results

    @staticmethod
    def find_duplicates(root=".") -> dict:
        """يجد الملفات المكررة بمقارنة MD5"""
        hashes = {}
        print("جاري المسح...")
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for fname in files:
                full = os.path.join(dirpath, fname)
                try:
                    md5 = hashlib.md5(open(full, 'rb').read(1024*1024)).hexdigest()
                    hashes.setdefault(md5, []).append(full)
                except (PermissionError, OSError):
                    pass
        dups = {h: paths for h, paths in hashes.items() if len(paths) > 1}
        total_waste = 0
        for paths in dups.values():
            sz = os.path.getsize(paths[0])
            total_waste += sz * (len(paths) - 1)
        print(f"✅ مجموعات مكررة: {len(dups)} — مساحة مهدرة: {_size_str(total_waste)}")
        return dups

    @staticmethod
    def batch_rename(folder: str, find: str, replace: str, regex=False) -> list:
        results = []
        for fname in sorted(os.listdir(folder)):
            old_path = os.path.join(folder, fname)
            if not os.path.isfile(old_path): continue
            if regex:
                new_name = re.sub(find, replace, fname)
            else:
                new_name = fname.replace(find, replace)
            if new_name != fname:
                new_path = os.path.join(folder, new_name)
                try:
                    os.rename(old_path, new_path)
                    results.append(f"✅ {fname} → {new_name}")
                except Exception as e:
                    results.append(f"❌ {fname}: {e}")
        return results if results else ["لا توجد ملفات مطابقة."]

    @staticmethod
    def organize_by_type(folder: str) -> dict:
        """ينظم الملفات في مجلدات حسب النوع"""
        type_map = {
            "صور":    [".jpg",".jpeg",".png",".gif",".webp",".bmp",".heic"],
            "فيديو":  [".mp4",".mkv",".avi",".mov",".3gp",".webm"],
            "صوت":    [".mp3",".aac",".flac",".wav",".ogg",".m4a"],
            "مستندات":[".pdf",".doc",".docx",".xls",".xlsx",".ppt",".pptx",".txt",".odt"],
            "مضغوطة": [".zip",".rar",".7z",".tar",".gz",".bz2"],
            "كود":    [".py",".js",".html",".css",".java",".kt",".sh",".json",".xml"],
            "APK":    [".apk",".xapk"],
        }
        moved = {k: [] for k in type_map}
        moved["أخرى"] = []
        ext_lookup = {}
        for category, exts in type_map.items():
            for ext in exts:
                ext_lookup[ext] = category
        for fname in os.listdir(folder):
            src = os.path.join(folder, fname)
            if not os.path.isfile(src): continue
            ext = os.path.splitext(fname)[1].lower()
            category = ext_lookup.get(ext, "أخرى")
            dest_dir = os.path.join(folder, category)
            os.makedirs(dest_dir, exist_ok=True)
            try:
                shutil.move(src, os.path.join(dest_dir, fname))
                moved[category].append(fname)
            except Exception as e:
                moved["أخرى"].append(f"❌ {fname}: {e}")
        summary = {k: len(v) for k, v in moved.items() if v}
        return summary

    @staticmethod
    def folder_stats(path=".") -> dict:
        stats = {"total_files": 0, "total_dirs": 0, "total_size": 0,
                 "largest_file": ("", 0), "by_extension": {}}
        for dirpath, dirs, files in os.walk(path):
            stats["total_dirs"] += len(dirs)
            for fname in files:
                stats["total_files"] += 1
                full = os.path.join(dirpath, fname)
                try:
                    sz = os.path.getsize(full)
                    stats["total_size"] += sz
                    if sz > stats["largest_file"][1]:
                        stats["largest_file"] = (full, sz)
                    ext = os.path.splitext(fname)[1].lower() or "بلا امتداد"
                    stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1
                except OSError:
                    pass
        stats["total_size_str"]    = _size_str(stats["total_size"])
        stats["largest_file_str"]  = f"{stats['largest_file'][0]}  ({_size_str(stats['largest_file'][1])})"
        del stats["total_size"], stats["largest_file"]
        stats["by_extension"] = dict(sorted(stats["by_extension"].items(),
                                            key=lambda x: -x[1])[:15])
        return stats

    @staticmethod
    def safe_copy(src: str, dest: str, verify=True) -> str:
        try:
            shutil.copy2(src, dest)
            if verify:
                src_md5  = hashlib.md5(open(src, 'rb').read()).hexdigest()
                dest_md5 = hashlib.md5(open(dest if os.path.isfile(dest)
                                            else os.path.join(dest, os.path.basename(src)), 'rb').read()).hexdigest()
                if src_md5 != dest_md5:
                    return "❌ فشل التحقق من التكامل!"
            return f"✅ نُسخ بنجاح: {dest}"
        except Exception as e:
            return f"❌ {e}"

if __name__ == "__main__":
    import json

    fm = FileManager()
    menu = {
        "1": ("عرض الشجرة",         lambda: fm.tree(input("المسار (.) => ").strip() or ".", int(input("عمق (3) => ").strip() or 3))),
        "2": ("بحث عن ملفات",       lambda: [print(r['path'], r['size'], r['modified'])
                                              for r in fm.search(
                                                  input("المجلد (.) => ").strip() or ".",
                                                  input("نمط الاسم => ").strip(),
                                                  input("الامتداد => ").strip(),
                                              )]),
        "3": ("ملفات مكررة",        lambda: [print(f"\n{paths}") for _, paths in fm.find_duplicates(input("المجلد (.) => ").strip() or ".").items()]),
        "4": ("إعادة تسمية دفعية",  lambda: [print(r) for r in fm.batch_rename(
                                                  input("المجلد => ").strip(),
                                                  input("البحث عن => ").strip(),
                                                  input("الاستبدال بـ => ").strip(),
                                              )]),
        "5": ("تنظيم بالنوع",       lambda: print(json.dumps(fm.organize_by_type(input("المجلد => ").strip()), indent=2, ensure_ascii=False))),
        "6": ("إحصائيات المجلد",    lambda: print(json.dumps(fm.folder_stats(input("المجلد (.) => ").strip() or "."), indent=2, ensure_ascii=False))),
        "7": ("نسخ مع تحقق",        lambda: print(fm.safe_copy(input("المصدر => ").strip(), input("الوجهة => ").strip()))),
    }
    while True:
        print("\n" + "═"*45)
        print("  📁  File Manager")
        print("═"*45)
        for k, (label, _) in menu.items():
            print(f"  {k}. {label}")
        print("  0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except KeyboardInterrupt: pass
            except Exception as e: print(f"خطأ: {e}")
