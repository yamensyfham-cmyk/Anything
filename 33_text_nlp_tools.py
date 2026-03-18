"""
أدوات معالجة النصوص — 18 ميزة
يستخدم: mini_langdetect (مبني بـ pure Python) بدل langdetect
"""
import os, sys, re, json, collections, math, string
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix
from mini_langdetect import detect, detect_langs

try:
    from googletrans import Translator
    _GTRANS = True
except ImportError:
    _GTRANS = False

class TextProcessor:

    @staticmethod
    def analyze(text: str) -> dict:
        words = text.split()
        sents = re.split(r'[.!?؟]\s*', text)
        sents = [s for s in sents if s.strip()]
        chars = len(text)
        letters = sum(c.isalpha() for c in text)
        return {
            "الكلمات":             len(words),
            "الجمل":              len(sents),
            "الأحرف":             chars,
            "الحروف_فقط":         letters,
            "الأرقام":            sum(c.isdigit() for c in text),
            "الرموز":             sum(c in string.punctuation for c in text),
            "متوسط_كلمات_الجملة": round(len(words)/len(sents),1) if sents else 0,
            "متوسط_حروف_الكلمة":  round(letters/len(words),1) if words else 0,
            "الكثافة_المعلوماتية": round(len(set(words))/len(words),3) if words else 0,
        }

    @staticmethod
    def word_frequency(text: str, top=20, exclude_common=True) -> dict:
        common = {'في','من','إلى','على','هو','هي','هذا','هذه','التي','الذي','كان','قد','أن',
                  'مع','كل','ما','لا','عن','بعد','قبل','the','is','are','was','and','or','to','of','a','an'}
        words = re.findall(r'\b\w{2,}\b', text.lower())
        if exclude_common: words = [w for w in words if w not in common]
        return dict(collections.Counter(words).most_common(top))

    @staticmethod
    def readability_score(text: str) -> dict:
        words = text.split()
        sents = max(len(re.split(r'[.!?؟]+', text)), 1)
        syllables = sum(max(1, len(re.findall(r'[aeiouAEIOU]', w))) for w in words)
        asl = len(words) / sents
        asw = syllables / len(words) if words else 0
        fre = 206.835 - 1.015*asl - 84.6*asw
        level = "صعب جداً" if fre<30 else "صعب" if fre<50 else "متوسط" if fre<70 else "سهل" if fre<90 else "سهل جداً"
        return {"Flesch_Reading_Ease":round(fre,1),"المستوى":level,
                "avg_sentence_len":round(asl,1),"avg_word_syllables":round(asw,2)}

    @staticmethod
    def extract_keywords(text: str, top=10) -> list:
        stop = {'في','من','إلى','على','هو','هي','the','is','are','was','and','or','to','a'}
        words = [w.lower() for w in re.findall(r'\b\w{3,}\b', text) if w.lower() not in stop]
        tf    = collections.Counter(words)
        scores = {w: tf[w] * math.log(2) for w in tf}
        return sorted(scores.items(), key=lambda x:-x[1])[:top]

    @staticmethod
    def summarize(text: str, sentences=3) -> str:
        sents = re.split(r'(?<=[.!?؟])\s+', text)
        if len(sents) <= sentences: return text
        words  = collections.Counter(re.findall(r'\b\w{3,}\b', text.lower()))
        def score(s): return sum(words.get(w.lower(),0) for w in s.split())
        ranked = sorted(enumerate(sents), key=lambda x:-score(x[1]))[:sentences]
        return ' '.join(s for _,s in sorted(ranked, key=lambda x:x[0]))

    @staticmethod
    def sentiment_simple(text: str) -> dict:
        pos_ar = ['جيد','ممتاز','رائع','جميل','سعيد','أحب','نجح','مذهل','بدر','ممتاز']
        neg_ar = ['سيء','فشل','كره','حزين','مشكلة','خطأ','ضعيف','رديء','مزعج']
        pos_en = ['good','great','excellent','happy','love','success','wonderful','amazing','best']
        neg_en = ['bad','fail','hate','sad','problem','error','weak','terrible','awful','worst']
        text_l = text.lower()
        pos = sum(text_l.count(w) for w in pos_ar + pos_en)
        neg = sum(text_l.count(w) for w in neg_ar + neg_en)
        if pos > neg: sentiment = "إيجابي 😊"
        elif neg > pos: sentiment = "سلبي 😞"
        else: sentiment = "محايد 😐"
        return {"sentiment":sentiment,"positive":pos,"negative":neg,
                "score":round((pos-neg)/(pos+neg+0.001),2)}

    @staticmethod
    def detect_language(text: str) -> dict:
        try:
            langs = detect_langs(text)
            return [{"language":l.lang,"confidence":round(l.prob,3)} for l in langs]
        except Exception as e:
            return {"error":str(e)}

    @staticmethod
    def translate(text: str, dest="en", src="auto") -> str:
        if not _GTRANS:
            import urllib.parse, urllib.request
            try:
                url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src}&tl={dest}&dt=t&q={urllib.parse.quote(text)}"
                req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
                data = json.loads(urllib.request.urlopen(req, timeout=10).read())
                return ''.join(part[0] for part in data[0] if part[0])
            except Exception as e:
                return f"❌ {e}"
        try:
            translator = Translator()
            result = translator.translate(text, dest=dest, src=src)
            return result.text
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def diff_texts(text1: str, text2: str) -> dict:
        import difflib
        ratio = difflib.SequenceMatcher(None, text1, text2).ratio()
        diff  = list(difflib.unified_diff(text1.split('\n'), text2.split('\n'), lineterm=''))
        return {"similarity":round(ratio,3),"diff_lines":diff[:20]}

    @staticmethod
    def find_patterns(text: str) -> dict:
        return {
            "emails":   re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text),
            "phones":   re.findall(r'[\+]?[\d\s\-\(\)]{9,15}', text),
            "urls":     re.findall(r'https?://[^\s"\'<>]+', text),
            "ips":      re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text),
            "dates":    re.findall(r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b', text),
            "hashtags": re.findall(r'#\w+', text),
            "mentions": re.findall(r'@\w+', text),
        }

    @staticmethod
    def clean_text(text: str, options=None) -> str:
        opts = options or ["html","extra_spaces","urls","emojis"]
        if "html"         in opts: text = re.sub(r'<[^>]+>','',text)
        if "urls"         in opts: text = re.sub(r'https?://\S+','',text)
        if "emojis"       in opts: text = re.sub(r'[\U00010000-\U0010ffff]','',text,flags=re.UNICODE)
        if "extra_spaces" in opts: text = re.sub(r'\s{2,}',' ',text).strip()
        if "punctuation"  in opts: text = text.translate(str.maketrans('','',string.punctuation))
        return text

    @staticmethod
    def generate_ngrams(text: str, n=2) -> list:
        words  = text.split()
        ngrams = [tuple(words[i:i+n]) for i in range(len(words)-n+1)]
        freq   = collections.Counter(ngrams)
        return [{"ngram":" ".join(g),"count":c} for g,c in freq.most_common(20)]

    @staticmethod
    def text_to_speech_espeak(text: str, lang="ar", speed=150) -> str:
        import subprocess
        try:
            subprocess.run(["espeak","-v",lang,"-s",str(speed),text], timeout=30)
            return "✅ تشغيل الصوت."
        except FileNotFoundError:
            return "❌ pkg install espeak"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def count_by_char_type(text: str) -> dict:
        return {
            "arabic":    sum('\u0600'<=c<='\u06ff' for c in text),
            "english":   sum(c.isalpha() and c.isascii() for c in text),
            "digits":    sum(c.isdigit() for c in text),
            "spaces":    sum(c.isspace() for c in text),
            "punctuation":sum(c in string.punctuation for c in text),
        }

    @staticmethod
    def obfuscate(text: str) -> str:
        return ''.join('*' if c.isalpha() else '#' if c.isdigit() else c for c in text)

    @staticmethod
    def lorem_ipsum(words=100) -> str:
        import random
        base = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat".split()
        return ' '.join(random.choice(base) for _ in range(words))

    @staticmethod
    def format_number_arabic(n: float) -> str:
        ones = ['','واحد','اثنان','ثلاثة','أربعة','خمسة','ستة','سبعة','ثمانية','تسعة','عشرة',
                'أحد عشر','اثنا عشر','ثلاثة عشر','أربعة عشر','خمسة عشر','ستة عشر','سبعة عشر','ثمانية عشر','تسعة عشر']
        tens  = ['','','عشرون','ثلاثون','أربعون','خمسون','ستون','سبعون','ثمانون','تسعون']
        n = int(n)
        if n < 0:    return 'سالب ' + TextProcessor.format_number_arabic(-n)
        if n < 20:   return ones[n]
        if n < 100:  return tens[n//10] + (' و' + ones[n%10] if n%10 else '')
        if n < 1000: return ones[n//100] + ' مئة' + (' و' + TextProcessor.format_number_arabic(n%100) if n%100 else '')
        if n < 1000000: return TextProcessor.format_number_arabic(n//1000) + ' ألف' + (' و' + TextProcessor.format_number_arabic(n%1000) if n%1000 else '')
        return str(n)

    @staticmethod
    def word_cloud_data(text: str, top=30) -> list:
        freq = TextProcessor.word_frequency(text, top)
        max_f = max(freq.values()) if freq else 1
        return [{"word":w,"count":c,"size":round(c/max_f*100)} for w,c in freq.items()]

if __name__ == "__main__":
    tp = TextProcessor()
    menu = {
        "1":  ("تحليل نص",               lambda: print(json.dumps(tp.analyze(input("النص => ")), indent=2, ensure_ascii=False))),
        "2":  ("تكرار الكلمات",           lambda: print(json.dumps(tp.word_frequency(input("النص => ")), indent=2, ensure_ascii=False))),
        "3":  ("صعوبة القراءة",           lambda: print(json.dumps(tp.readability_score(input("النص => ")), indent=2, ensure_ascii=False))),
        "4":  ("الكلمات المفتاحية",        lambda: [print(f"  {w}: {round(s,2)}") for w,s in tp.extract_keywords(input("النص => "))]),
        "5":  ("تلخيص تلقائي",            lambda: print(tp.summarize(input("النص => "), int(input("جمل (3) => ") or 3)))),
        "6":  ("تحليل المشاعر",           lambda: print(json.dumps(tp.sentiment_simple(input("النص => ")), indent=2, ensure_ascii=False))),
        "7":  ("كشف اللغة",               lambda: print(json.dumps(tp.detect_language(input("النص => ")), indent=2))),
        "8":  ("ترجمة",                   lambda: print(tp.translate(input("النص => "), input("اللغة (en/ar/fr...) => ") or "en"))),
        "9":  ("استخراج أنماط",           lambda: print(json.dumps(tp.find_patterns(input("النص => ")), indent=2, ensure_ascii=False))),
        "10": ("تنظيف نص",                lambda: print(tp.clean_text(input("النص => ")))),
        "11": ("N-Grams",                 lambda: [print(f"  {r['ngram']}: {r['count']}") for r in tp.generate_ngrams(input("النص => "), int(input("N (2) => ") or 2))]),
        "12": ("مقارنة نصين",             lambda: print(json.dumps(tp.diff_texts(input("النص 1 => "), input("النص 2 => ")), indent=2, ensure_ascii=False))),
        "13": ("تشويش نص",                lambda: print(tp.obfuscate(input("النص => ")))),
        "14": ("رقم بالعربي",             lambda: print(tp.format_number_arabic(float(input("الرقم => "))))),
        "15": ("إحصاء نوع الأحرف",        lambda: print(json.dumps(tp.count_by_char_type(input("النص => ")), indent=2, ensure_ascii=False))),
        "16": ("نص لصوت (espeak)",        lambda: print(tp.text_to_speech_espeak(input("النص => "), input("اللغة (ar/en) => ") or "ar"))),
        "17": ("Lorem Ipsum",             lambda: print(tp.lorem_ipsum(int(input("عدد الكلمات (100) => ") or 100)))),
        "18": ("كلمات للرسم البياني",      lambda: [print(f"  {r['word']}: {r['size']}%") for r in tp.word_cloud_data(input("النص => "))[:15]]),
    }
    while True:
        print("\n═"*45)
        print("  📝  Text NLP — 18 ميزة | mini_langdetect")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
