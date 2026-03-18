"""
أدوات الميديا والتحميل — 20 ميزة
pip install yt-dlp requests
"""
import os, sys, subprocess, json, re, time
import urllib.request, urllib.parse
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

def _run(cmd, timeout=300):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except FileNotFoundError as e: return "", str(e), 1
    except Exception as e: return "", str(e), 1

class MediaDownloader:

    @staticmethod
    def _yt(args: list) -> str:
        out, err, code = _run(["yt-dlp"] + args)
        return out or err

    @staticmethod
    def download_video(url: str, out_dir=".", quality="best") -> str:
        """تحميل فيديو بأفضل جودة"""
        os.makedirs(out_dir, exist_ok=True)
        return MediaDownloader._yt([
            "-f", f"{quality}[ext=mp4]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", os.path.join(out_dir, "%(title)s.%(ext)s"),
            url
        ])

    @staticmethod
    def download_audio(url: str, out_dir=".", fmt="mp3") -> str:
        """تحميل صوت فقط"""
        os.makedirs(out_dir, exist_ok=True)
        return MediaDownloader._yt([
            "-x", "--audio-format", fmt,
            "-o", os.path.join(out_dir, "%(title)s.%(ext)s"),
            url
        ])

    @staticmethod
    def download_playlist(url: str, out_dir=".", audio_only=False) -> str:
        """تحميل قائمة تشغيل"""
        os.makedirs(out_dir, exist_ok=True)
        args = ["-o", os.path.join(out_dir, "%(playlist_index)s - %(title)s.%(ext)s")]
        if audio_only: args += ["-x", "--audio-format", "mp3"]
        else: args += ["-f", "best[ext=mp4]/best"]
        return MediaDownloader._yt(args + [url])

    @staticmethod
    def get_info(url: str) -> dict:
        """معلومات الفيديو"""
        out, err, _ = _run(["yt-dlp", "--dump-json", "--no-download", url], timeout=30)
        try:
            data = json.loads(out)
            return {
                "title":    data.get("title",""),
                "duration": f"{data.get('duration',0)//60}:{data.get('duration',0)%60:02d}",
                "views":    data.get("view_count",0),
                "channel":  data.get("uploader",""),
                "formats":  len(data.get("formats",[])),
                "thumb":    data.get("thumbnail",""),
            }
        except Exception: return {"error": err[:200]}

    @staticmethod
    def list_formats(url: str) -> str:
        return MediaDownloader._yt(["-F", url])

    @staticmethod
    def download_format(url: str, format_id: str, out_dir=".") -> str:
        return MediaDownloader._yt([
            "-f", format_id,
            "-o", os.path.join(out_dir, "%(title)s.%(ext)s"),
            url
        ])

    @staticmethod
    def download_subtitles(url: str, lang="ar", out_dir=".") -> str:
        return MediaDownloader._yt([
            "--write-sub", "--sub-lang", lang,
            "--skip-download",
            "-o", os.path.join(out_dir, "%(title)s.%(ext)s"),
            url
        ])

    @staticmethod
    def download_thumbnail(url: str, out_dir=".") -> str:
        return MediaDownloader._yt([
            "--write-thumbnail", "--skip-download",
            "-o", os.path.join(out_dir, "%(title)s.%(ext)s"),
            url
        ])

    @staticmethod
    def batch_download(urls: list, out_dir=".", audio_only=False) -> str:
        count = 0
        for url in urls:
            if audio_only: MediaDownloader.download_audio(url, out_dir)
            else:          MediaDownloader.download_video(url, out_dir)
            count += 1
        return f"✅ تم تحميل {count} ملف"

    @staticmethod
    def download_file(url: str, out_path: str, show_progress=True) -> str:
        """تحميل أي ملف مباشرة"""
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                total = int(r.headers.get("Content-Length", 0))
                downloaded = 0
                with open(out_path, 'wb') as f:
                    while True:
                        chunk = r.read(65536)
                        if not chunk: break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if show_progress and total:
                            pct = downloaded/total*100
                            print(f"\r  ⬇ {pct:.1f}% — {downloaded/1024/1024:.1f} MB", end="")
            if show_progress: print()
            return f"✅ {out_path} ({downloaded/1024/1024:.2f} MB)"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def download_images_from_page(url: str, out_dir=".") -> str:
        """تحميل كل صور صفحة"""
        os.makedirs(out_dir, exist_ok=True)
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8','replace')
            import re
            imgs = re.findall(r'src=["\']?(https?://[^"\'<>\s]+\.(?:jpg|jpeg|png|gif|webp))', html, re.I)
            count = 0
            for img_url in imgs[:20]:
                fname = os.path.join(out_dir, f"img_{count:03d}.{img_url.split('.')[-1][:4]}")
                try:
                    urllib.request.urlretrieve(img_url, fname)
                    count += 1
                except Exception: pass
            return f"✅ تم تحميل {count} صورة → {out_dir}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def resume_download(url: str, out_path: str) -> str:
        """استكمال تحميل متوقف"""
        existing = os.path.getsize(out_path) if os.path.exists(out_path) else 0
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Range": f"bytes={existing}-"
            })
            with urllib.request.urlopen(req, timeout=60) as r:
                mode = 'ab' if existing else 'wb'
                with open(out_path, mode) as f:
                    while True:
                        chunk = r.read(65536)
                        if not chunk: break
                        f.write(chunk)
            return f"✅ اكتمل: {out_path}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def convert_video(src: str, out: str, extra_args=None) -> str:
        """تحويل فيديو باستخدام ffmpeg"""
        cmd = ["ffmpeg", "-i", src]
        if extra_args: cmd += extra_args
        cmd.append(out)
        out_str, err, code = _run(cmd, timeout=300)
        return f"✅ {out}" if code == 0 else f"❌ {err[-200:]}"

    @staticmethod
    def extract_audio_from_video(src: str, out: str = None) -> str:
        out = out or os.path.splitext(src)[0] + ".mp3"
        return MediaDownloader.convert_video(src, out, ["-vn", "-acodec", "libmp3lame"])

    @staticmethod
    def compress_video(src: str, out: str = None, crf=28) -> str:
        out = out or os.path.splitext(src)[0] + "_compressed.mp4"
        return MediaDownloader.convert_video(src, out, ["-c:v", "libx264", f"-crf", str(crf)])

    @staticmethod
    def video_info(path: str) -> dict:
        out, err, _ = _run(["ffprobe","-v","quiet","-print_format","json","-show_streams","-show_format", path], timeout=30)
        try:
            data = json.loads(out)
            fmt  = data.get("format",{})
            streams = data.get("streams",[])
            video = next((s for s in streams if s.get("codec_type")=="video"),{})
            audio = next((s for s in streams if s.get("codec_type")=="audio"),{})
            return {
                "الحجم":      f"{int(fmt.get('size',0))/1024/1024:.2f} MB",
                "المدة":      f"{float(fmt.get('duration',0)):.1f}s",
                "البيتريت":   f"{int(fmt.get('bit_rate',0))//1000} kbps",
                "الفيديو":    f"{video.get('codec_name','')} {video.get('width','')}x{video.get('height','')}",
                "الصوت":      f"{audio.get('codec_name','')} {audio.get('sample_rate','')}Hz",
            }
        except Exception: return {"error": "تأكد من تثبيت ffprobe"}

if __name__ == "__main__":
    md = MediaDownloader()
    menu = {
        "1":  ("تحميل فيديو",               lambda: print(md.download_video(input("URL => "), input("المجلد (.) => ") or "."))),
        "2":  ("تحميل صوت MP3",             lambda: print(md.download_audio(input("URL => "), input("المجلد (.) => ") or "."))),
        "3":  ("تحميل قائمة تشغيل",         lambda: print(md.download_playlist(input("URL => "), input("المجلد => ") or "."))),
        "4":  ("معلومات الفيديو",            lambda: print(json.dumps(md.get_info(input("URL => ")), indent=2, ensure_ascii=False))),
        "5":  ("قائمة الصيغ المتاحة",       lambda: print(md.list_formats(input("URL => ")))),
        "6":  ("تحميل بصيغة محددة",         lambda: print(md.download_format(input("URL => "), input("Format ID => ")))),
        "7":  ("تحميل الترجمة",             lambda: print(md.download_subtitles(input("URL => "), input("اللغة (ar) => ") or "ar"))),
        "8":  ("تحميل الصورة المصغرة",      lambda: print(md.download_thumbnail(input("URL => ")))),
        "9":  ("تحميل ملف مباشر",           lambda: print(md.download_file(input("URL => "), input("حفظ في => ")))),
        "10": ("تحميل صور من صفحة",         lambda: print(md.download_images_from_page(input("URL الصفحة => "), input("المجلد => ") or "."))),
        "11": ("استكمال تحميل",             lambda: print(md.resume_download(input("URL => "), input("مسار الملف => ")))),
        "12": ("تحويل فيديو (ffmpeg)",       lambda: print(md.convert_video(input("المصدر => "), input("الإخراج => ")))),
        "13": ("استخراج صوت من فيديو",      lambda: print(md.extract_audio_from_video(input("مسار الفيديو => ")))),
        "14": ("ضغط فيديو",                 lambda: print(md.compress_video(input("مسار الفيديو => ")))),
        "15": ("معلومات ملف ميديا",         lambda: print(json.dumps(md.video_info(input("المسار => ")), indent=2, ensure_ascii=False))),
    }
    while True:
        print("\n═"*45)
        print("  🎬  Media Tools — 15 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
