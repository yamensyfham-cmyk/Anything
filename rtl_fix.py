"""
إصلاح عرض العربية في Termux
Pure Python — صفر مكاتب خارجية
يتضمن: Arabic Reshaper + Unicode BiDi
"""
import sys, io, builtins

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

_FORMS = {
    0x0621:('\u0621',None,None,None),
    0x0622:('\u0622','\uFE82',None,None),
    0x0623:('\u0623','\uFE84',None,None),
    0x0624:('\u0624','\uFE86',None,None),
    0x0625:('\u0625','\uFE88',None,None),
    0x0626:('\u0626','\uFE8A','\uFE8B','\uFE8C'),
    0x0627:('\u0627','\uFE8E',None,None),
    0x0628:('\u0628','\uFE90','\uFE91','\uFE92'),
    0x0629:('\u0629','\uFE94',None,None),
    0x062A:('\u062A','\uFE96','\uFE97','\uFE98'),
    0x062B:('\u062B','\uFE9A','\uFE9B','\uFE9C'),
    0x062C:('\u062C','\uFE9E','\uFE9F','\uFEA0'),
    0x062D:('\u062D','\uFEA2','\uFEA3','\uFEA4'),
    0x062E:('\u062E','\uFEA6','\uFEA7','\uFEA8'),
    0x062F:('\u062F','\uFEAA',None,None),
    0x0630:('\u0630','\uFEAC',None,None),
    0x0631:('\u0631','\uFEAE',None,None),
    0x0632:('\u0632','\uFEB0',None,None),
    0x0633:('\u0633','\uFEB2','\uFEB3','\uFEB4'),
    0x0634:('\u0634','\uFEB6','\uFEB7','\uFEB8'),
    0x0635:('\u0635','\uFEBA','\uFEBB','\uFEBC'),
    0x0636:('\u0636','\uFEBE','\uFEBF','\uFEC0'),
    0x0637:('\u0637','\uFEC2','\uFEC3','\uFEC4'),
    0x0638:('\u0638','\uFEC6','\uFEC7','\uFEC8'),
    0x0639:('\u0639','\uFECA','\uFECB','\uFECC'),
    0x063A:('\u063A','\uFECE','\uFECF','\uFED0'),
    0x0641:('\u0641','\uFED2','\uFED3','\uFED4'),
    0x0642:('\u0642','\uFED6','\uFED7','\uFED8'),
    0x0643:('\u0643','\uFEDA','\uFEDB','\uFEDC'),
    0x0644:('\u0644','\uFEDE','\uFEDF','\uFEE0'),
    0x0645:('\u0645','\uFEE2','\uFEE3','\uFEE4'),
    0x0646:('\u0646','\uFEE6','\uFEE7','\uFEE8'),
    0x0647:('\u0647','\uFEEA','\uFEEB','\uFEEC'),
    0x0648:('\u0648','\uFEEE',None,None),
    0x0649:('\u0649','\uFEF0',None,None),
    0x064A:('\u064A','\uFEF2','\uFEF3','\uFEF4'),
    0x067E:('\u067E','\uFB57','\uFB58','\uFB59'),
    0x0686:('\u0686','\uFB7B','\uFB7C','\uFB7D'),
    0x0698:('\u0698','\uFB8B',None,None),
    0x06A9:('\u06A9','\uFB8F','\uFB90','\uFB91'),
    0x06AF:('\u06AF','\uFB93','\uFB94','\uFB95'),
    0x06CC:('\u06CC','\uFBFE','\uFBFF','\uFBFC'),
}
_NO_LEFT = {cp for cp,f in _FORMS.items() if f[2] is None}

_LAM_ALEF = {
    '\u0622':('\uFEF5','\uFEF6'), '\u0623':('\uFEF7','\uFEF8'),
    '\u0625':('\uFEF9','\uFEFA'), '\u0627':('\uFEFB','\uFEFC'),
}

def _letter(c): return ord(c) in _FORMS
def _left(c):   return ord(c) in _FORMS and ord(c) not in _NO_LEFT

def _form(c, prev_conn, next_conn):
    f = _FORMS.get(ord(c))
    if not f: return c
    if prev_conn and next_conn and f[3]: return f[3]
    if prev_conn and f[1]:              return f[1]
    if next_conn and f[2]:              return f[2]
    return f[0]

def _reshape(text):
    cs = list(text)
    out, i = [], 0
    while i < len(cs):
        c = cs[i]
        if not _letter(c):
            out.append(c); i += 1; continue
        nxt = cs[i+1] if i+1 < len(cs) else None
        prv = cs[i-1] if i > 0 else None
        pc = prv is not None and _letter(prv) and _left(prv)
        nc = nxt is not None and _letter(nxt)

        if c == '\u0644' and nxt in _LAM_ALEF:
            pair = _LAM_ALEF[nxt]
            out.append(pair[1] if pc else pair[0])
            i += 2; continue
        out.append(_form(c, pc, nc))
        i += 1
    return ''.join(out)

_RTL_RANGES = [(0x0590,0x08FF),(0xFB1D,0xFDFF),(0xFE70,0xFEFF)]

def _is_rtl(c):
    cp = ord(c)
    return any(a <= cp <= b for a,b in _RTL_RANGES)

def _bidi(text):
    """عكس اتجاه النص ليظهر صحيحاً في terminal LTR"""
    if not text: return text

    segs, cur, cur_rtl = [], [], _is_rtl(text[0])
    for ch in text:
        ch_rtl = _is_rtl(ch) or (ch in ' ،؛؟\u060c\u061b\u061f' and cur_rtl)
        if ch_rtl != cur_rtl and cur:
            segs.append((''.join(cur), cur_rtl)); cur = []
        cur_rtl = ch_rtl; cur.append(ch)
    if cur: segs.append((''.join(cur), cur_rtl))

    has_rtl = any(r for _,r in segs)
    if not has_rtl: return text

    rtl_n = sum(1 for c in text if _is_rtl(c))
    alpha = sum(1 for c in text if c.strip() and not c.isdigit()) or 1

    if rtl_n / alpha > 0.3:

        out = []
        for seg, is_rtl in reversed(segs):
            out.append(seg[::-1] if is_rtl else seg)
        return ''.join(out)
    return text

def fix(text: str) -> str:
    if not text or not isinstance(text, str): return text
    if not any('\u0600' <= c <= '\u06FF' for c in text): return text
    lines = text.split('\n')
    out   = []
    for line in lines:
        if not any('\u0600' <= c <= '\u06FF' for c in line):
            out.append(line); continue
        try:    out.append(_bidi(_reshape(line)))
        except: out.append(line)
    return '\n'.join(out)

_orig = builtins.print
def _p(*args, **kwargs):
    _orig(*[fix(a) if isinstance(a,str) else a for a in args], **kwargs)
builtins.print = _p

if __name__ == "__main__":
    tests = ["مرحبا بالعالم","1- الذكاء الاصطناعي","── أندرويد ──",
             "IP: 1.1.1.1 — فحص المنافذ","Hello مع عربي 123"]
    for t in tests: print(f"  {t}")
    print("✅ rtl_fix — pure Python")
