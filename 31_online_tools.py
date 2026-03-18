"""
أدوات الإنترنت — طقس/أخبار/عملات/خرائط/ترجمة — 30 ميزة
مكاتب: stdlib فقط (urllib)
"""
import os, sys, json, re, time, urllib.request, urllib.parse
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

def _get(url, headers=None, timeout=10):
    try:
        req = urllib.request.Request(url, headers=headers or {"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8","replace"))
    except Exception as e:
        return {"error": str(e)}

def _get_text(url, headers=None, timeout=10):
    try:
        req = urllib.request.Request(url, headers=headers or {"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8","replace")
    except Exception as e:
        return f"❌ {e}"

class WeatherTools:

    @staticmethod
    def current(city: str) -> dict:
        """طقس حالي مجاني عبر wttr.in"""
        url  = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        data = _get(url)
        if "error" in data: return data
        try:
            curr = data["current_condition"][0]
            area = data["nearest_area"][0]
            return {
                "المدينة":     city,
                "الحرارة":    f"{curr['temp_C']}°C / {curr['temp_F']}°F",
                "الحالة":     curr["weatherDesc"][0]["value"],
                "الرطوبة":    f"{curr['humidity']}%",
                "الرياح":     f"{curr['windspeedKmph']} km/h",
                "الضغط":      f"{curr['pressure']} mb",
                "الرؤية":     f"{curr['visibility']} km",
                "UV Index":   curr.get("uvIndex","N/A"),
                "الشعور":     f"{curr['FeelsLikeC']}°C",
            }
        except Exception as e:
            return {"error": str(e), "raw": str(data)[:200]}

    @staticmethod
    def forecast(city: str, days=3) -> list:
        """توقعات الطقس"""
        url  = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
        data = _get(url)
        if "error" in data: return [data]
        try:
            forecasts = []
            for day in data.get("weather",[])[:days]:
                forecasts.append({
                    "التاريخ":  day["date"],
                    "الحد الأقصى": f"{day['maxtempC']}°C",
                    "الحد الأدنى": f"{day['mintempC']}°C",
                    "الحالة":   day["hourly"][4]["weatherDesc"][0]["value"],
                    "الأمطار":  f"{day['hourly'][4]['precipMM']} mm",
                    "الرياح":   f"{day['hourly'][4]['windspeedKmph']} km/h",
                })
            return forecasts
        except Exception as e:
            return [{"error": str(e)}]

    @staticmethod
    def ascii_weather(city: str) -> str:
        """طقس بتمثيل ASCII"""
        return _get_text(f"https://wttr.in/{urllib.parse.quote(city)}")

    @staticmethod
    def compare_cities(cities: list) -> list:
        return [WeatherTools.current(c) for c in cities]

    @staticmethod
    def moon_phase() -> str:
        data = _get_text("https://wttr.in/Moon")
        return data[:500]

class NewsTools:

    @staticmethod
    def top_headlines(country="ae", category="general") -> list:
        """أخبار من NewsAPI (مجاني محدود)"""

        feeds = {
            "general":  "https://feeds.bbcarabic.com/BBCArabic/rss.xml",
            "tech":     "https://feeds.feedburner.com/TechCrunch",
            "science":  "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
            "sports":   "https://www.aljazeera.net/rssfeeds/sports",
        }
        feed_url = feeds.get(category, feeds["general"])
        return NewsTools.parse_rss(feed_url)

    @staticmethod
    def parse_rss(url: str) -> list:
        """قراءة RSS Feed"""
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
            xml = urllib.request.urlopen(req, timeout=15).read().decode("utf-8","replace")
            items = re.findall(r'<item>(.*?)</item>', xml, re.DOTALL)
            news  = []
            for item in items[:10]:
                title = re.search(r'<title[^>]*><!\[CDATA\[(.*?)\]\]>|<title[^>]*>(.*?)</title>', item, re.DOTALL)
                link  = re.search(r'<link[^>]*>(.*?)</link>', item, re.DOTALL)
                desc  = re.search(r'<description[^>]*><!\[CDATA\[(.*?)\]\]>|<description[^>]*>(.*?)</description>', item, re.DOTALL)
                news.append({
                    "العنوان":  (title.group(1) or title.group(2) or "").strip()[:100] if title else "",
                    "الرابط":   (link.group(1) or "").strip() if link else "",
                    "الملخص":   re.sub(r'<[^>]+>','',(desc.group(1) or desc.group(2) or "").strip())[:200] if desc else "",
                })
            return news
        except Exception as e:
            return [{"error": str(e)}]

    @staticmethod
    def search_news(query: str) -> list:
        """بحث في الأخبار عبر RSS بديل"""
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ar&gl=SA&ceid=SA:ar"
        return NewsTools.parse_rss(url)

    @staticmethod
    def tech_news() -> list:
        return NewsTools.parse_rss("https://feeds.feedburner.com/TechCrunch")

    @staticmethod
    def security_news() -> list:
        return NewsTools.parse_rss("https://feeds.feedburner.com/TheHackersNews")

class CurrencyTools:

    @staticmethod
    def rate(from_cur: str, to_cur: str) -> float:
        data = _get(f"https://open.er-api.com/v6/latest/{from_cur.upper()}")
        return data.get("rates",{}).get(to_cur.upper(), 0)

    @staticmethod
    def convert(amount: float, from_cur: str, to_cur: str) -> str:
        rate = CurrencyTools.rate(from_cur, to_cur)
        if not rate: return "❌ عملة غير مدعومة"
        return f"{amount} {from_cur.upper()} = {amount*rate:.4f} {to_cur.upper()}"

    @staticmethod
    def all_rates(base="USD") -> dict:
        data = _get(f"https://open.er-api.com/v6/latest/{base.upper()}")
        return data.get("rates", {"error":"فشل"})

    @staticmethod
    def crypto_prices(coins=None) -> dict:
        coins = coins or ["bitcoin","ethereum","binancecoin","ripple","cardano"]
        url   = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(coins)}&vs_currencies=usd,sar"
        return _get(url)

    @staticmethod
    def crypto_info(coin: str) -> dict:
        url = f"https://api.coingecko.com/api/v3/coins/{coin}?localization=false&tickers=false&community_data=false"
        data = _get(url)
        if "error" in data: return data
        try:
            md = data.get("market_data",{})
            return {
                "الاسم":      data.get("name",""),
                "الرمز":      data.get("symbol","").upper(),
                "السعر_USD":  md.get("current_price",{}).get("usd",""),
                "السعر_SAR":  md.get("current_price",{}).get("sar",""),
                "24h%":      f"{md.get('price_change_percentage_24h',0):.2f}%",
                "7d%":       f"{md.get('price_change_percentage_7d',0):.2f}%",
                "القيمة_السوقية": md.get("market_cap",{}).get("usd",""),
                "الترتيب":    data.get("market_cap_rank",""),
            }
        except Exception as e:
            return {"error":str(e)}

    @staticmethod
    def gold_price() -> dict:
        """سعر الذهب عبر API مجاني"""
        try:
            data = _get("https://www.goldapi.io/api/XAU/USD", headers={"x-access-token":"goldapi-demo"})
            if "error" not in data:
                return {"الأوقية_USD": data.get("price",""), "الذهب_SAR": round(data.get("price",0)*3.75,2)}
        except Exception: pass
        return {"info": "يتطلب API Key من goldapi.io"}

class TranslationTools:

    @staticmethod
    def translate(text: str, to_lang="en", from_lang="auto") -> str:
        """ترجمة مجانية عبر MyMemory API"""
        if from_lang == "auto": from_lang = ""
        lang_pair = f"{from_lang}|{to_lang}" if from_lang else f"ar|{to_lang}"
        url  = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={lang_pair}"
        data = _get(url)
        if "error" in data: return data["error"]
        return data.get("responseData",{}).get("translatedText","❌ فشل الترجمة")

    @staticmethod
    def detect_language(text: str) -> str:
        """تحديد لغة النص"""
        url  = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text[:100])}&langpair=en|ar"
        data = _get(url)
        if "error" in data: return "unknown"
        return data.get("responseData",{}).get("translatedText","unknown")

    @staticmethod
    def translate_file(file_path: str, to_lang="en", out_path=None) -> str:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        translated = []
        for line in lines[:100]:
            if line.strip():
                t = TranslationTools.translate(line.strip(), to_lang)
                translated.append(t)
                time.sleep(0.3)
            else:
                translated.append("")
        out = out_path or file_path + f"_{to_lang}.txt"
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(translated))
        return f"✅ {out}"

    @staticmethod
    def bulk_translate(texts: list, to_lang="en") -> list:
        results = []
        for text in texts:
            results.append(TranslationTools.translate(text, to_lang))
            time.sleep(0.3)
        return results

class MapsTools:

    @staticmethod
    def geocode(address: str) -> dict:
        """تحويل عنوان إلى إحداثيات"""
        url  = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(address)}&format=json&limit=1"
        data = _get(url, {"User-Agent":"UAS-Tool/1.0"})
        if isinstance(data, list) and data:
            return {"lat":float(data[0]["lat"]),"lng":float(data[0]["lon"]),"display":data[0]["display_name"]}
        return {"error":"لم يُعثر على النتيجة"}

    @staticmethod
    def reverse_geocode(lat: float, lng: float) -> dict:
        """إحداثيات إلى عنوان"""
        url  = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        data = _get(url, {"User-Agent":"UAS-Tool/1.0"})
        if "error" in data: return data
        return {"عنوان": data.get("display_name",""),"بلد": data.get("address",{}).get("country","")}

    @staticmethod
    def distance(lat1,lng1,lat2,lng2) -> dict:
        """المسافة بين نقطتين (Haversine)"""
        import math
        R = 6371
        dlat = math.radians(lat2-lat1)
        dlng = math.radians(lng2-lng1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlng/2)**2
        c = 2*math.atan2(math.sqrt(a),math.sqrt(1-a))
        d = R*c
        return {"km":round(d,2),"miles":round(d*0.621,2),"meters":round(d*1000)}

    @staticmethod
    def nearby_places(lat: float, lng: float, category="restaurant", radius=1000) -> list:
        """أماكن قريبة عبر Overpass API"""
        q = f"""[out:json][timeout:10];
node[amenity={category}](around:{radius},{lat},{lng});
out 10;"""
        url  = "https://overpass-api.de/api/interpreter"
        data = urllib.parse.urlencode({"data":q}).encode()
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent":"UAS-Tool/1.0"})
            res = json.loads(urllib.request.urlopen(req,timeout=15).read())
            return [{"name":e.get("tags",{}).get("name","?"),
                     "lat":e.get("lat"),"lng":e.get("lon")} for e in res.get("elements",[])[:10]]
        except Exception as e:
            return [{"error":str(e)}]

    @staticmethod
    def maps_link(lat: float, lng: float) -> str:
        return f"https://maps.google.com/?q={lat},{lng}"

    @staticmethod
    def directions_link(from_addr: str, to_addr: str) -> str:
        origin = urllib.parse.quote(from_addr)
        dest   = urllib.parse.quote(to_addr)
        return f"https://maps.google.com/maps?saddr={origin}&daddr={dest}"

if __name__ == "__main__":
    menu = {
        "1":  ("🌤 طقس حالي",              lambda: print(json.dumps(WeatherTools.current(input("المدينة => ")), indent=2, ensure_ascii=False))),
        "2":  ("📅 توقعات الطقس",           lambda: [print(json.dumps(d, indent=2, ensure_ascii=False)) for d in WeatherTools.forecast(input("المدينة => "), int(input("أيام (3) => ") or 3))]),
        "3":  ("🌤 طقس ASCII",              lambda: print(WeatherTools.ascii_weather(input("المدينة => ")))),
        "4":  ("📰 أخبار عامة",             lambda: [print(f"\n📌 {n['العنوان']}\n   {n['الملخص'][:80]}") for n in NewsTools.top_headlines()]),
        "5":  ("🔒 أخبار الأمان",           lambda: [print(f"\n📌 {n['العنوان']}") for n in NewsTools.security_news()]),
        "6":  ("💻 أخبار تقنية",            lambda: [print(f"\n📌 {n['العنوان']}") for n in NewsTools.tech_news()]),
        "7":  ("🔍 بحث في الأخبار",         lambda: [print(f"\n📌 {n['العنوان']}") for n in NewsTools.search_news(input("البحث => "))]),
        "8":  ("💱 تحويل عملة",             lambda: print(CurrencyTools.convert(float(input("المبلغ => ")), input("من => "), input("إلى => ")))),
        "9":  ("💹 أسعار الكريبتو",         lambda: print(json.dumps(CurrencyTools.crypto_prices(), indent=2))),
        "10": ("🪙 معلومات عملة رقمية",     lambda: print(json.dumps(CurrencyTools.crypto_info(input("اسم العملة (bitcoin) => ")), indent=2, ensure_ascii=False))),
        "11": ("💰 كل أسعار الصرف",         lambda: print(json.dumps(CurrencyTools.all_rates(input("العملة الأساس (USD) => ") or "USD"), indent=2))),
        "12": ("🌐 ترجمة نص",              lambda: print(TranslationTools.translate(input("النص => "), input("اللغة (en/ar/fr) => ") or "en"))),
        "13": ("📄 ترجمة ملف",             lambda: print(TranslationTools.translate_file(input("الملف => "), input("اللغة => ") or "en"))),
        "14": ("📍 عنوان إلى إحداثيات",    lambda: print(json.dumps(MapsTools.geocode(input("العنوان => ")), indent=2, ensure_ascii=False))),
        "15": ("📍 إحداثيات إلى عنوان",    lambda: print(json.dumps(MapsTools.reverse_geocode(float(input("Lat => ")), float(input("Lng => "))), indent=2, ensure_ascii=False))),
        "16": ("📏 مسافة بين نقطتين",       lambda: print(json.dumps(MapsTools.distance(float(input("Lat1 => ")), float(input("Lng1 => ")), float(input("Lat2 => ")), float(input("Lng2 => "))), indent=2))),
        "17": ("🏠 أماكن قريبة",            lambda: print(json.dumps(MapsTools.nearby_places(float(input("Lat => ")), float(input("Lng => ")), input("النوع (restaurant/cafe) => ") or "restaurant"), indent=2, ensure_ascii=False))),
        "18": ("🗺 رابط خرائط",             lambda: print(MapsTools.maps_link(float(input("Lat => ")), float(input("Lng => "))))),
    }
    while True:
        print("\n═"*45)
        print("  🌍  Online Tools — 18 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
