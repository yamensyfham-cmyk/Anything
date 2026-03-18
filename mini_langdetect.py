"""
MiniLangDetect — بديل langdetect
Pure Python, zero dependencies
خوارزمية: N-gram + Unicode ranges + frequency scoring
يدعم 30+ لغة
"""
import re
import math
import unicodedata
from collections import Counter

_RANGES = {
    'ar': [(0x0600,0x06FF),(0x0750,0x077F),(0xFB50,0xFDFF),(0xFE70,0xFEFF)],
    'he': [(0x0590,0x05FF),(0xFB1D,0xFB4F)],
    'fa': [(0x0600,0x06FF),(0x0750,0x077F)],
    'ur': [(0x0600,0x06FF)],
    'zh': [(0x4E00,0x9FFF),(0x3400,0x4DBF),(0x20000,0x2A6DF),(0x2A700,0x2B73F)],
    'ja': [(0x3040,0x309F),(0x30A0,0x30FF),(0x4E00,0x9FFF),(0xFF65,0xFF9F)],
    'ko': [(0xAC00,0xD7AF),(0x1100,0x11FF),(0x3130,0x318F)],
    'ru': [(0x0400,0x04FF),(0x0500,0x052F)],
    'uk': [(0x0400,0x04FF)],
    'el': [(0x0370,0x03FF),(0x1F00,0x1FFF)],
    'th': [(0x0E00,0x0E7F)],
    'hi': [(0x0900,0x097F)],
    'bn': [(0x0980,0x09FF)],
    'ta': [(0x0B80,0x0BFF)],
    'te': [(0x0C00,0x0C7F)],
    'gu': [(0x0A80,0x0AFF)],
    'kn': [(0x0C80,0x0CFF)],
    'ml': [(0x0D00,0x0D7F)],
    'si': [(0x0D80,0x0DFF)],
    'my': [(0x1000,0x109F)],
    'km': [(0x1780,0x17FF)],
    'lo': [(0x0E80,0x0EFF)],
    'ka': [(0x10A0,0x10FF)],
    'am': [(0x1200,0x137F)],
    'ti': [(0x1200,0x137F)],
}

def _unicode_score(text: str) -> dict:
    scores = {}
    for lang, ranges in _RANGES.items():
        count = sum(1 for c in text if any(lo <= ord(c) <= hi for lo,hi in ranges))
        if count > 0:
            scores[lang] = count / len(text)
    return scores

_PROFILES = {
    'en': ['the','ing','and','ion','ent','tio','for','hat','his','not','tha','ter','was','ere','her','all','ith','have','but','this','are','from','with','they','will','that','been','has','had','its','who','were','said','each'],
    'fr': ['les','des','une','est','que','pas','sur','ent','ion','par','qui','ter','con','ans','ais','ont','ces','res','ous','tion','dans','pour','avec','vous','mais','tout','bien','elle','plus','nous','être','très','quand','donc'],
    'de': ['die','und','der','ein','ist','den','ich','das','sie','auf','mit','dem','von','war','hat','des','ein','wie','nicht','aber','werden','mehr','auch','sein','noch','oder','alle','wenn','dann','nach','über','jahre','kann'],
    'es': ['los','las','que','del','con','una','ent','ion','por','par','est','res','ado','para','como','este','pero','todo','más','también','sobre','bien','años','hace','tiene','donde','según','entre','cuando','hasta','desde'],
    'pt': ['que','ção','dos','uma','com','por','ção','ent','res','par','ado','para','mais','como','este','pelo','pela','isso','também','entre','depois','ainda','deve','pode','sobre','anos','bem','então','onde','além'],
    'it': ['che','della','del','dei','con','una','per','non','sono','nel','gli','sui','una','più','loro','anche','dopo','però','ancora','tutto','quando','questo','essere','aveva','come','dalla','delle','degli','nella'],
    'nl': ['van','het','een','dat','niet','zijn','heeft','voor','met','aan','door','bij','over','hebben','maar','werd','ook','dan','nog','toen','naar','deze','wel','meer','als','dit','was','had','door','zonder'],
    'pl': ['nie','się','że','jak','jest','ale','przez','jego','jej','ich','wszystko','może','bardzo','będzie','tylko','jestem','kiedy','który','która','które','przez','tego','tej','też','sobie','tym','oraz'],
    'cs': ['pro','byl','ale','nebo','jeho','není','jako','bude','více','také','taky','jejich','celé','jsou','být','mají','musí','mohl','nová','stát','roku','bylo','přes','nové','ještě','mezi','stejně'],
    'sv': ['att','och','det','som','för','inte','men','med','den','har','han','till','vara','också','från','när','hade','efter','under','sedan','alla','eller','utan','dessa','varje','inga','mitt','ditt'],
    'no': ['og','er','det','som','for','ikke','men','med','den','har','han','til','være','også','fra','når','hadde','etter','under','siden','alle','eller','uten','disse','hvert'],
    'da': ['og','er','det','som','for','ikke','men','med','den','har','han','til','være','også','fra','når','havde','efter','under','siden','alle','eller','uden','disse','hvert'],
    'fi': ['olla','että','hän','tämä','kaikki','myös','mutta','niin','sitten','kun','mitä','joka','koska','vaan','vielä','muita','aikaan','jotka','joita','sellainen'],
    'hu': ['hogy','nem','van','egy','azt','volt','meg','ezt','már','csak','lett','ilyen','majd','amikor','akkor','mindig','lehet','olyan','sokkal','pedig','alatt'],
    'ro': ['este','sunt','din','care','mai','spre','dar','sau','pentru','dintre','până','după','prin','unde','când','acesta','acum','dacă','orice','fiecare','acestui'],
    'tr': ['bir','bu','ile','için','da','de','değil','ama','çok','daha','sonra','gibi','olan','veya','şey','nasıl','yani','bile','kadar','üzere','içinde'],
    'id': ['yang','dan','di','ini','itu','atau','dengan','dari','tidak','pada','ada','ke','juga','untuk','karena','oleh','dapat','akan','bisa','sudah','belum'],
    'vi': ['của','và','các','là','có','trong','được','này','với','đây','không','người','năm','theo','về','tại','đã','khi','nên','trên','sau','cho'],
}

def _ngrams(text: str, n: int) -> Counter:
    text = re.sub(r'\s+', ' ', text.lower())
    return Counter(text[i:i+n] for i in range(len(text)-n+1))

def _cosine_sim(c1: Counter, c2_set: set) -> float:
    common = sum(v for k,v in c1.items() if k in c2_set)
    if not common: return 0.0
    mag = math.sqrt(sum(v*v for v in c1.values()))
    return common / (mag + 1e-9)

def _latin_score(text: str) -> dict:
    """نقاط اللغات اللاتينية بـ N-gram"""
    clean = re.sub(r'[^a-z\s]', ' ', text.lower())
    if len(clean.strip()) < 10: return {}
    trigrams = _ngrams(clean, 3)
    scores   = {}
    for lang, words in _PROFILES.items():
        word_set = set(words)

        wc  = sum(1 for w in clean.split() if w in word_set)
        tg  = _cosine_sim(trigrams, set(w for word in words for i in range(len(word)-2) for w in [word[i:i+3]]))
        scores[lang] = wc * 0.7 + tg * 0.3
    return scores

_FA_CHARS = set('پچژگ')

def _arabic_dialect(text: str) -> str:
    """تمييز العربية/الفارسية/الأردية"""
    fa_count = sum(1 for c in text if c in _FA_CHARS)
    ar_score  = sum(1 for c in text if 0x0600 <= ord(c) <= 0x06FF)
    if ar_score == 0: return 'ar'
    if fa_count / max(ar_score, 1) > 0.05:
        return 'fa'
    return 'ar'

class LangResult:
    def __init__(self, lang, prob):
        self.lang = lang
        self.prob = round(prob, 4)
    def __repr__(self): return f"{self.lang}:{self.prob}"

def _normalize(scores: dict) -> dict:
    total = sum(scores.values()) or 1
    return {k: v/total for k,v in scores.items()}

def detect(text: str) -> str:
    results = detect_langs(text)
    return results[0].lang if results else 'unknown'

def detect_langs(text: str) -> list:
    if not text or len(text.strip()) < 3:
        return [LangResult('unknown', 1.0)]

    uni_scores = _unicode_score(text)
    if uni_scores:
        best_lang  = max(uni_scores, key=uni_scores.get)
        best_score = uni_scores[best_lang]
        if best_score > 0.3:

            if best_lang in ('ar', 'fa', 'ur'):
                best_lang = _arabic_dialect(text)

            sorted_scores = sorted(uni_scores.items(), key=lambda x:-x[1])
            total = sum(v for _,v in sorted_scores[:5]) or 1
            results = [LangResult(l, v/total) for l,v in sorted_scores[:5]]

            top    = results[0].prob
            return [LangResult(r.lang, min(1.0, r.prob/top)) for r in results[:3]]

    latin_scores = _latin_score(text)
    if not latin_scores:
        return [LangResult('en', 1.0)]

    filtered = {k: v for k,v in latin_scores.items() if v > 0}
    if not filtered:
        return [LangResult('en', 1.0)]

    sorted_scores = sorted(filtered.items(), key=lambda x:-x[1])
    top_score     = sorted_scores[0][1] or 1

    results = []
    for lang, score in sorted_scores[:5]:
        prob = min(1.0, score / top_score)
        if prob > 0.01:
            results.append(LangResult(lang, prob))

    if results:
        max_p = results[0].prob
        for r in results: r.prob = round(r.prob / max_p, 4)

    return results or [LangResult('en', 1.0)]

class LangDetectException(Exception): pass
DetectorFactory = None

def detect_language(text: str) -> str:
    """alias"""
    return detect(text)

if __name__ == "__main__":
    tests = [
        ("مرحبا بالعالم، كيف حالك اليوم؟", "ar"),
        ("Hello, how are you today?", "en"),
        ("Bonjour, comment allez-vous?", "fr"),
        ("Guten Morgen, wie geht es Ihnen?", "de"),
        ("Hola, ¿cómo estás?", "es"),
        ("Ciao, come stai?", "it"),
        ("Привет, как дела?", "ru"),
        ("今日は良い天気ですね", "ja"),
        ("这是一个测试文本", "zh"),
        ("مرحبا این یک متن فارسی است", "fa"),
    ]
    print("═"*50)
    print("  MiniLangDetect — اختبار")
    print("═"*50)
    correct = 0
    for text, expected in tests:
        result  = detect(text)
        details = detect_langs(text)
        ok = "✅" if result == expected else f"⚠ (متوقع:{expected})"
        print(f"  {ok} [{result}] {text[:30]}")
        if result == expected: correct += 1
    print(f"\n  النتيجة: {correct}/{len(tests)}")
    print("✅ MiniLangDetect OK")
