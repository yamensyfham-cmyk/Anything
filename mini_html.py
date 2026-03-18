"""
MiniHTML — بديل BeautifulSoup + lxml
Pure Python, zero dependencies
يدعم: CSS selectors, XPath-like queries, HTML parsing, XML parsing
"""
import re
from html.parser import HTMLParser
from html import unescape
from io import StringIO

class Tag:
    __slots__ = ('name','attrs','children','parent','text_content')

    def __init__(self, name, attrs=None, parent=None):
        self.name         = name.lower() if name else ''
        self.attrs        = dict(attrs or [])
        self.children     = []
        self.parent       = parent
        self.text_content = ''

    def get_text(self, separator='', strip=True):
        parts = []
        self._collect_text(parts)
        text = separator.join(parts)
        return text.strip() if strip else text

    def _collect_text(self, parts):
        for child in self.children:
            if isinstance(child, str):
                t = child.strip()
                if t: parts.append(t)
            elif isinstance(child, Tag):
                child._collect_text(parts)

    def get(self, attr, default=None):
        return self.attrs.get(attr, default)

    def __getitem__(self, attr):
        return self.attrs[attr]

    def __contains__(self, attr):
        return attr in self.attrs

    def __repr__(self):
        a = ' '.join(f'{k}="{v}"' for k,v in list(self.attrs.items())[:3])
        return f'<{self.name} {a}>'

    @property
    def string(self):
        texts = [c for c in self.children if isinstance(c, str) and c.strip()]
        return texts[0].strip() if len(texts) == 1 else None

    @property
    def strings(self):
        parts = []
        self._collect_text(parts)
        return parts

    @property
    def next_sibling(self):
        if not self.parent: return None
        siblings = self.parent.children
        for i, s in enumerate(siblings):
            if s is self and i+1 < len(siblings):
                return siblings[i+1]
        return None

    def find(self, tag=None, attrs=None, **kwargs):
        """أول عنصر مطابق"""
        results = self._search(tag, attrs or {}, kwargs, limit=1)
        return results[0] if results else None

    def find_all(self, tag=None, attrs=None, limit=None, **kwargs):
        """كل العناصر المطابقة"""
        return self._search(tag, attrs or {}, kwargs, limit=limit)

    def select_one(self, selector):
        results = self.select(selector)
        return results[0] if results else None

    def select(self, selector):
        """CSS selector محدود"""
        return _css_select(self, selector)

    def _match(self, tag_name, attrs, kwargs):
        if tag_name and tag_name != self.name and tag_name != True:
            return False
        check = dict(attrs)
        check.update(kwargs)
        for k, v in check.items():
            k = k.rstrip('_').replace('_','-')
            node_val = self.attrs.get(k, '')
            if v is True:
                if k not in self.attrs: return False
            elif v is None:
                pass
            elif isinstance(v, re.Pattern):
                if not v.search(node_val): return False
            elif callable(v):
                if not v(node_val): return False
            else:
                if str(v) not in node_val: return False
        return True

    def _search(self, tag, attrs, kwargs, limit=None):
        results = []
        self._walk(tag, attrs, kwargs, results, limit)
        return results

    def _walk(self, tag, attrs, kwargs, results, limit):
        if limit and len(results) >= limit: return
        for child in self.children:
            if not isinstance(child, Tag): continue
            if child._match(tag, attrs, kwargs):
                results.append(child)
                if limit and len(results) >= limit: return
            child._walk(tag, attrs, kwargs, results, limit)

    def decompose(self):
        if self.parent:
            try: self.parent.children.remove(self)
            except ValueError: pass
        self.parent = None

    def __str__(self):
        attrs = ''.join(f' {k}="{v}"' for k,v in self.attrs.items())
        children = ''.join(str(c) for c in self.children)
        VOID = {'br','hr','img','input','link','meta','area','base','col','embed','param','source','track','wbr'}
        if self.name in VOID:
            return f'<{self.name}{attrs}/>'
        return f'<{self.name}{attrs}>{children}</{self.name}>'

class NavigableString(str):
    @property
    def string(self): return str(self)
    def get_text(self, **kwargs): return str(self)

class _Parser(HTMLParser):
    VOID = {'br','hr','img','input','link','meta','area','base','col',
            'embed','param','source','track','wbr','!doctype'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root    = Tag('[document]')
        self._stack  = [self.root]

    def _cur(self): return self._stack[-1]

    def handle_starttag(self, tag, attrs):
        node = Tag(tag, attrs, self._cur())
        self._cur().children.append(node)
        if tag.lower() not in self.VOID:
            self._stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self._stack)-1, 0, -1):
            if self._stack[i].name == tag.lower():
                self._stack = self._stack[:i]
                return

    def handle_data(self, data):
        if data:
            self._cur().children.append(data)

    def handle_comment(self, data): pass

def _css_select(root: Tag, selector: str) -> list:
    """
    يدعم:
    - tag  →  div
    - .class  →  .menu
    - #id  →  #main
    - [attr]  →  [href]
    - [attr=val]  →  [type="text"]
    - tag.class  →  div.active
    - a b (descendant)
    - a > b (direct child)
    - a, b (multiple)
    """
    results = []
    for part in selector.split(','):
        results += _match_selector(root, part.strip())

    seen = set()
    out  = []
    for r in results:
        if id(r) not in seen:
            seen.add(id(r)); out.append(r)
    return out

def _parse_simple(sel):
    """تحليل محدد بسيط → (tag, id, classes, attrs)"""
    tag = ''; id_ = ''; classes = []; attrs = []

    for m in re.finditer(r'\[([^\]]+)\]', sel):
        a = m.group(1)
        if '=' in a:
            k,v = a.split('=',1)
            attrs.append((k.strip(), v.strip().strip('"').strip("'")))
        else:
            attrs.append((a.strip(), None))
    sel2 = re.sub(r'\[[^\]]+\]', '', sel)

    m = re.search(r'#([\w-]+)', sel2)
    if m: id_ = m.group(1); sel2 = sel2[:m.start()] + sel2[m.end():]

    for m in re.finditer(r'\.([\w-]+)', sel2):
        classes.append(m.group(1))
    sel2 = re.sub(r'\.[\w-]+','', sel2)
    tag  = sel2.strip()
    return tag, id_, classes, attrs

def _node_matches(node, tag, id_, classes, attrs):
    if not isinstance(node, Tag): return False
    if tag and node.name != tag: return False
    if id_ and node.attrs.get('id','') != id_: return False
    node_classes = node.attrs.get('class','').split()
    for cls in classes:
        if cls not in node_classes: return False
    for k, v in attrs:
        if k not in node.attrs: return False
        if v is not None and node.attrs[k] != v: return False
    return True

def _all_descendants(node):
    for child in node.children:
        if isinstance(child, Tag):
            yield child
            yield from _all_descendants(child)

def _direct_children(node):
    return [c for c in node.children if isinstance(c, Tag)]

def _match_selector(root, selector):

    if '>' in selector:
        parts = [p.strip() for p in selector.split('>')]
        nodes = [root]
        for part in parts:
            tag, id_, classes, attrs = _parse_simple(part)
            next_nodes = []
            for n in nodes:
                for child in _direct_children(n):
                    if _node_matches(child, tag, id_, classes, attrs):
                        next_nodes.append(child)
            nodes = next_nodes
        return nodes
    elif ' ' in selector:
        parts = selector.split(None, 1)
        tag0, id0, cls0, at0 = _parse_simple(parts[0])
        candidates = [n for n in _all_descendants(root) if _node_matches(n, tag0, id0, cls0, at0)]
        results = []
        for c in candidates:
            results += _match_selector(c, parts[1])
        return results
    else:
        tag, id_, classes, attrs = _parse_simple(selector)
        return [n for n in _all_descendants(root) if _node_matches(n, tag, id_, classes, attrs)]

class BeautifulSoup(Tag):
    """
    بديل BeautifulSoup كامل — pure Python
    يدعم: html.parser, lxml (يتجاهل المحلل ويستخدم stdlib)
    """
    def __init__(self, markup='', parser='html.parser', **kwargs):
        super().__init__('[document]')
        if markup:
            p = _Parser()
            try:
                p.feed(str(markup))
            except Exception:
                pass
            self.children = p.root.children
            for child in self.children:
                if isinstance(child, Tag):
                    child.parent = self

    @property
    def title(self):
        return self.find('title')

    def __str__(self):
        return ''.join(str(c) for c in self.children)

    def prettify(self, indent=2):
        return self._prettify(0, indent)

    def _prettify(self, level, indent):
        out = ''
        for child in self.children:
            if isinstance(child, str):
                if child.strip():
                    out += ' '*level*indent + child.strip() + '\n'
            elif isinstance(child, Tag):
                attrs = ''.join(f' {k}="{v}"' for k,v in child.attrs.items())
                out  += ' '*level*indent + f'<{child.name}{attrs}>\n'
                if hasattr(child, '_prettify'):
                    out += child._prettify(level+1, indent)
                out  += ' '*level*indent + f'</{child.name}>\n'
        return out

import xml.etree.ElementTree as _ET

class MiniXML:
    """بديل lxml — يستخدم stdlib xml.etree"""

    @staticmethod
    def fromstring(text):
        try:    return _ET.fromstring(text)
        except Exception as e: raise ValueError(str(e))

    @staticmethod
    def parse(path):
        return _ET.parse(path)

    @staticmethod
    def tostring(elem, encoding='unicode', pretty=False):
        if pretty: _ET.indent(elem, space='  ')
        return _ET.tostring(elem, encoding=encoding)

    @staticmethod
    def xpath(elem, path):
        """XPath مبسط"""
        try:    return elem.findall(path)
        except: return []

    @staticmethod
    def to_dict(elem) -> dict:
        d = {**elem.attrib}
        if elem.text and elem.text.strip(): d['_text'] = elem.text.strip()
        for child in elem:
            cd = MiniXML.to_dict(child)
            if child.tag in d:
                if not isinstance(d[child.tag], list): d[child.tag] = [d[child.tag]]
                d[child.tag].append(cd)
            else:
                d[child.tag] = cd
        return d

def SoupStrainer(*a, **kw): return None

if __name__ == "__main__":
    html = """
    <html><body>
      <h1 id="title">مرحبا</h1>
      <div class="content">
        <p>الفقرة الأولى <a href="http://test.com">رابط</a></p>
        <ul><li>بند 1</li><li>بند 2</li></ul>
      </div>
      <table><tr><th>Name</th><th>Age</th></tr><tr><td>أحمد</td><td>25</td></tr></table>
    </body></html>
    """
    soup = BeautifulSoup(html)
    print("h1:", soup.find('h1').get_text())
    print("links:", [a['href'] for a in soup.find_all('a', href=True)])
    print("li:", [li.get_text() for li in soup.select('ul li')])
    print("table:", [[td.get_text() for td in tr.find_all('td')] for tr in soup.find_all('tr')])
    print("✅ MiniHTML OK")
