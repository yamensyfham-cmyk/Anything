"""
أتمتة الويب المتقدمة — 15 ميزة
يستخدم: mini_html (مبني بـ pure Python) بدل BeautifulSoup + lxml
"""
import os, sys, json, re, time, threading
import urllib.request, urllib.parse, urllib.robotparser
from datetime import datetime
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix
from mini_html import BeautifulSoup

try:
    import requests
    _REQ = True
except ImportError:
    _REQ = False

def _fetch(url, timeout=15, headers=None, session=None):
    h = {"User-Agent":"Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36"}
    if headers: h.update(headers)
    if session and _REQ:
        r = session.get(url, headers=h, timeout=timeout)
        return r.text, r.status_code, dict(r.headers)
    if _REQ:
        r = requests.get(url, headers=h, timeout=timeout)
        return r.text, r.status_code, dict(r.headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode('utf-8','replace'), r.status, dict(r.headers)

class WebAutomation:

    @staticmethod
    def monitor_changes(url: str, interval=60, out="changes.json"):
        import hashlib
        print(f"👀 مراقبة {url} — Ctrl+C للإيقاف")
        prev_hash = ""; changes = []
        try:
            while True:
                try:
                    html,_,_ = _fetch(url)
                    curr_hash = hashlib.md5(html.encode()).hexdigest()
                    if prev_hash and curr_hash != prev_hash:
                        entry = {"time":datetime.now().isoformat(),"url":url}
                        changes.append(entry)
                        print(f"⚡ تغيير! {entry['time']}")
                        json.dump(changes, open(out,'w'), indent=2)
                    prev_hash = curr_hash
                except Exception as e: print(f"  ⚠ {e}")
                time.sleep(interval)
        except KeyboardInterrupt: return changes

    @staticmethod
    def check_keyword(url: str, keyword: str) -> dict:
        try:
            html,status,_ = _fetch(url)
            count = html.lower().count(keyword.lower())
            return {"url":url,"keyword":keyword,"found":count>0,"count":count,"status":status}
        except Exception as e: return {"error":str(e)}

    @staticmethod
    def crawl(start_url: str, max_pages=20, same_domain=True) -> list:
        domain  = urllib.parse.urlparse(start_url).netloc
        visited, queue, pages = set(), [start_url], []
        while queue and len(pages) < max_pages:
            url = queue.pop(0)
            if url in visited: continue
            visited.add(url)
            try:
                html,status,_ = _fetch(url, timeout=8)
                soup  = BeautifulSoup(html)
                links = [a.get('href','') for a in soup.find_all('a', href=True)]
                page  = {"url":url,"status":status,"links":len(links)}
                title = soup.find('title')
                page["title"] = title.get_text() if title else ""
                pages.append(page)
                for link in links[:10]:
                    href = str(link)
                    if href.startswith('http') and href not in visited:
                        if not same_domain or urllib.parse.urlparse(href).netloc == domain:
                            queue.append(href)
            except Exception: pass
        return pages

    @staticmethod
    def scrape_table(url: str, table_index=0) -> list:
        try:
            html,_,_ = _fetch(url)
            soup   = BeautifulSoup(html)
            tables = soup.find_all('table')
            if not tables or table_index >= len(tables):
                return [{"error":f"لا يوجد جدول بالفهرس {table_index}"}]
            table   = tables[table_index]
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            rows    = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all('td')]
                if cells:
                    if headers: rows.append(dict(zip(headers,cells)))
                    else: rows.append(cells)
            return rows
        except Exception as e: return [{"error":str(e)}]

    @staticmethod
    def scrape_articles(url: str) -> list:
        try:
            html,_,_ = _fetch(url)
            soup     = BeautifulSoup(html)
            articles = []
            for tag in ['article','div']:
                for el in soup.find_all(tag)[:15]:
                    cls = el.attrs.get('class','')
                    if not any(k in str(cls).lower() for k in ['article','post','news','story','card']): continue
                    h = el.find(['h1','h2','h3'])
                    p = el.find('p')
                    a = el.find('a', href=True)
                    if h:
                        articles.append({
                            "title": h.get_text(strip=True)[:100],
                            "text":  p.get_text(strip=True)[:200] if p else "",
                            "link":  str(a.get('href','')) if a else "",
                        })
            return articles or [{"note":"لم يُعثر على مقالات"}]
        except Exception as e: return [{"error":str(e)}]

    @staticmethod
    def scrape_social_meta(url: str) -> dict:
        try:
            html,_,_ = _fetch(url)
            soup     = BeautifulSoup(html)
            meta     = {}
            for tag in soup.find_all('meta'):
                prop = tag.get('property') or tag.get('name','')
                if any(p in str(prop) for p in ['og:','twitter:']):
                    meta[prop] = tag.get('content','')
            title = soup.find('title')
            meta['title'] = title.get_text() if title else ""
            desc = soup.find('meta', attrs={'name':'description'})
            meta['description'] = desc.get('content','') if desc else ""
            return meta
        except Exception as e: return {"error":str(e)}

    @staticmethod
    def extract_all(url: str) -> dict:
        try:
            html,status,headers = _fetch(url)
            soup   = BeautifulSoup(html)

            links  = list(set(str(a.get('href','')) for a in soup.find_all('a', href=True) if str(a.get('href','')).startswith('http')))

            emails = list(set(re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', html)))

            phones = list(set(re.findall(r'[\+]?[\d\s\-\(\)]{9,15}', html)))

            headings = [h.get_text(strip=True) for h in soup.find_all(['h1','h2','h3'])]

            images = list(set(str(img.get('src','')) for img in soup.find_all('img', src=True)))
            title  = soup.find('title')
            return {
                "url":      url,
                "status":   status,
                "title":    title.get_text() if title else "",
                "links":    links[:30],
                "emails":   emails[:20],
                "phones":   [p.strip() for p in phones if len(re.sub(r'\D','',p))>=9][:10],
                "headings": headings[:15],
                "images":   images[:20],
            }
        except Exception as e: return {"error":str(e)}

    @staticmethod
    def bulk_check_urls(urls: list) -> list:
        results = []
        def check(url):
            t0 = time.time()
            try:
                _,status,headers = _fetch(url, timeout=8)
                results.append({"url":url,"status":status,"ms":round((time.time()-t0)*1000),
                                 "server":headers.get('Server','')})
            except Exception as e:
                results.append({"url":url,"status":0,"error":str(e)[:40]})
        threads = [threading.Thread(target=check,args=(u,)) for u in urls]
        for t in threads: t.start()
        for t in threads: t.join()
        return results

    @staticmethod
    def check_robots_txt(url: str, path: str) -> dict:
        try:
            base = urllib.parse.urlparse(url)
            robots_url = f"{base.scheme}://{base.netloc}/robots.txt"
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url); rp.read()
            return {"robots_url":robots_url,"path":path,"allowed":rp.can_fetch("*", path)}
        except Exception as e: return {"error":str(e)}

    @staticmethod
    def wayback_check(url: str) -> dict:
        try:
            api = f"http://archive.org/wayback/available?url={urllib.parse.quote(url)}"
            data = json.loads(urllib.request.urlopen(api, timeout=10).read())
            snap = data.get("archived_snapshots",{}).get("closest",{})
            return {"available":snap.get("available",False),"url":snap.get("url",""),
                    "timestamp":snap.get("timestamp","")}
        except Exception as e: return {"error":str(e)}

    @staticmethod
    def extract_structured_data(url: str) -> list:
        try:
            html,_,_ = _fetch(url)
            soup = BeautifulSoup(html)
            data = []
            for script in soup.find_all('script'):
                if script.get('type') == 'application/ld+json':
                    try:
                        t = script.get_text()
                        if t: data.append(json.loads(t))
                    except Exception: pass
            return data
        except Exception as e: return [{"error":str(e)}]

    @staticmethod
    def broken_links(url: str) -> list:
        try:
            html,_,_ = _fetch(url)
            links = re.findall(r'href=["\']?(https?://[^\s"\'<>]+)', html)
            broken = []
            for link in list(set(links))[:30]:
                try:
                    req = urllib.request.Request(link, method='HEAD', headers={"User-Agent":"Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=5) as r:
                        if r.status >= 400: broken.append({"url":link,"status":r.status})
                except Exception as e:
                    broken.append({"url":link,"error":str(e)[:30]})
            return broken
        except Exception as e: return [{"error":str(e)}]

    @staticmethod
    def generate_sitemap(start_url: str, max_pages=50) -> str:
        pages = WebAutomation.crawl(start_url, max_pages)
        urls  = [p["url"] for p in pages]
        xml   = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        for u in urls: xml += f"  <url><loc>{u}</loc></url>\n"
        xml  += "</urlset>"
        out   = "sitemap.xml"
        import builtins as _bi
        _bi.open(out,'w').write(xml)
        return f"✅ {out} ({len(urls)} URL)"

    @staticmethod
    def screenshot_url(url: str, out="screenshot.png") -> str:
        try:
            api = f"https://image.thum.io/get/{url}"
            urllib.request.urlretrieve(api, out)
            return f"✅ {out}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def submit_form(url: str, form_data: dict) -> dict:
        if not _REQ: return {"error":"pip install requests"}
        try:
            r = requests.post(url, data=form_data, headers={"User-Agent":"Mozilla/5.0"}, timeout=15)
            return {"status":r.status_code,"url":r.url,"body":r.text[:500]}
        except Exception as e: return {"error":str(e)}

if __name__ == "__main__":
    wa = WebAutomation()
    menu = {
        "1":  ("استخراج شامل",             lambda: print(json.dumps(wa.extract_all(input("URL => ")), indent=2, ensure_ascii=False))),
        "2":  ("مراقبة تغييرات",           lambda: wa.monitor_changes(input("URL => "), int(input("كل (60ث) => ") or 60))),
        "3":  ("فحص كلمة",                lambda: print(json.dumps(wa.check_keyword(input("URL => "), input("الكلمة => ")), indent=2, ensure_ascii=False))),
        "4":  ("Crawl موقع",              lambda: [print(f"  {p['status']} {p['url'][:60]}") for p in wa.crawl(input("URL => "), int(input("أقصى صفحات (20) => ") or 20))]),
        "5":  ("استخراج جدول HTML",       lambda: print(json.dumps(wa.scrape_table(input("URL => "), int(input("فهرس الجدول (0) => ") or 0)), indent=2, ensure_ascii=False))),
        "6":  ("استخراج مقالات",          lambda: print(json.dumps(wa.scrape_articles(input("URL => ")), indent=2, ensure_ascii=False))),
        "7":  ("Open Graph Meta",         lambda: print(json.dumps(wa.scrape_social_meta(input("URL => ")), indent=2, ensure_ascii=False))),
        "8":  ("فحص URLs دفعي",           lambda: [print(f"  {'✅' if r.get('status',0)<400 else '❌'} {r['url'][:50]}") for r in wa.bulk_check_urls(input("URLs (مسافة) => ").split())]),
        "9":  ("فحص robots.txt",          lambda: print(json.dumps(wa.check_robots_txt(input("URL => "), input("المسار => ")), indent=2))),
        "10": ("Wayback Machine",         lambda: print(json.dumps(wa.wayback_check(input("URL => ")), indent=2))),
        "11": ("JSON-LD Structured Data", lambda: print(json.dumps(wa.extract_structured_data(input("URL => ")), indent=2, ensure_ascii=False))),
        "12": ("الروابط المكسورة",        lambda: [print(f"  ❌ {r.get('url','')} {r.get('status',r.get('error',''))}") for r in wa.broken_links(input("URL => "))]),
        "13": ("توليد Sitemap",           lambda: print(wa.generate_sitemap(input("URL => "), int(input("أقصى صفحات (50) => ") or 50)))),
        "14": ("لقطة شاشة موقع",          lambda: print(wa.screenshot_url(input("URL => "), input("ملف الإخراج (screenshot.png) => ") or "screenshot.png"))),
        "15": ("إرسال نموذج",             lambda: print(json.dumps(wa.submit_form(input("URL => "), {input(f"حقل {i+1} => "):input(f"قيمة {i+1} => ") for i in range(int(input("عدد الحقول => ") or 2))}), indent=2))),
    }
    while True:
        print("\n═"*45)
        print("  🌐  Web Automation — 15 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
