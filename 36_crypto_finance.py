"""
أدوات المالية والعملات — 20 ميزة
مكاتب: stdlib فقط (urllib)
"""
import os, sys, json, time, re, sqlite3
import urllib.request, urllib.parse
from datetime import datetime, timedelta
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

def _get_json(url, timeout=10):
    try:
        req = urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        return json.loads(urllib.request.urlopen(req,timeout=timeout).read())
    except Exception as e: return {"error":str(e)}

FINANCE_DB = os.path.join(BASE_DIR,"finance.db")

def _db():
    conn = sqlite3.connect(FINANCE_DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY, symbol TEXT, amount REAL, buy_price REAL, date TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS price_alerts (
        id INTEGER PRIMARY KEY, symbol TEXT, target REAL, direction TEXT,
        active INTEGER DEFAULT 1, created TEXT)""")
    conn.commit()
    return conn

class CryptoFinanceTools:

    @staticmethod
    def crypto_price(symbol: str) -> dict:
        """سعر عملة رقمية من CoinGecko (مجاني)"""
        sym = symbol.lower()
        data = _get_json(f"https://api.coingecko.com/api/v3/simple/price?ids={sym}&vs_currencies=usd,sar,aed&include_24hr_change=true")
        if data.get("error") or sym not in data:

            search = _get_json(f"https://api.coingecko.com/api/v3/search?query={sym}")
            if search.get("coins"):
                coin_id = search["coins"][0]["id"]
                data = _get_json(f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd,sar,aed&include_24hr_change=true")
                sym = coin_id
        if sym in data:
            d = data[sym]
            return {"symbol":sym,"usd":d.get("usd",0),"sar":d.get("sar",0),
                    "aed":d.get("aed",0),"change_24h":round(d.get("usd_24h_change",0),2)}
        return {"error":"العملة غير موجودة"}

    @staticmethod
    def crypto_top(limit=10) -> list:
        """أعلى العملات الرقمية"""
        data = _get_json(f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page={limit}&page=1")
        if isinstance(data,list):
            return [{"rank":i+1,"name":c["name"],"symbol":c["symbol"].upper(),
                     "price":c["current_price"],"change_24h":round(c.get("price_change_percentage_24h",0),2),
                     "market_cap":c.get("market_cap",0)} for i,c in enumerate(data)]
        return [{"error":str(data)}]

    @staticmethod
    def crypto_history(coin_id: str, days=7) -> list:
        data = _get_json(f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&interval=daily")
        prices = data.get("prices",[])
        return [{"date":datetime.fromtimestamp(p[0]/1000).strftime("%Y-%m-%d"),
                 "price":round(p[1],4)} for p in prices]

    @staticmethod
    def crypto_search(query: str) -> list:
        data = _get_json(f"https://api.coingecko.com/api/v3/search?query={urllib.parse.quote(query)}")
        return [{"id":c["id"],"name":c["name"],"symbol":c["symbol"]} for c in data.get("coins",[])[:10]]

    @staticmethod
    def stock_price(symbol: str) -> dict:
        """سعر سهم من Yahoo Finance"""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
        data = _get_json(url)
        try:
            result = data["chart"]["result"][0]
            meta   = result["meta"]
            return {
                "symbol":   symbol,
                "price":    meta.get("regularMarketPrice",0),
                "prev_close":meta.get("previousClose",0),
                "currency": meta.get("currency",""),
                "change":   round(meta.get("regularMarketPrice",0)-meta.get("previousClose",0),3),
                "change%":  round((meta.get("regularMarketPrice",0)/meta.get("previousClose",1)-1)*100,2),
            }
        except Exception: return {"error":"فشل جلب السهم","raw":str(data)[:100]}

    @staticmethod
    def stock_history(symbol: str, period="1mo") -> list:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range={period}"
        data = _get_json(url)
        try:
            result    = data["chart"]["result"][0]
            timestamps = result["timestamp"]
            closes    = result["indicators"]["quote"][0]["close"]
            return [{"date":datetime.fromtimestamp(t).strftime("%Y-%m-%d"),
                     "close":round(c,3)} for t,c in zip(timestamps,closes) if c]
        except Exception: return []

    @staticmethod
    def exchange_rate(from_cur: str, to_cur: str) -> dict:
        data = _get_json(f"https://open.er-api.com/v6/latest/{from_cur.upper()}")
        if data.get("result") == "success":
            rate = data["rates"].get(to_cur.upper())
            return {"from":from_cur.upper(),"to":to_cur.upper(),"rate":rate,
                    "updated":data.get("time_last_update_utc","")}
        return {"error":"فشل جلب سعر الصرف"}

    @staticmethod
    def convert_currency(amount: float, from_cur: str, to_cur: str) -> str:
        data = CryptoFinanceTools.exchange_rate(from_cur, to_cur)
        if "rate" in data and data["rate"]:
            result = amount * data["rate"]
            return f"{amount} {from_cur.upper()} = {round(result,4)} {to_cur.upper()}"
        return f"❌ {data.get('error','')}"

    @staticmethod
    def multi_currency(base: str, currencies: list) -> dict:
        data = _get_json(f"https://open.er-api.com/v6/latest/{base.upper()}")
        if data.get("result") == "success":
            rates = data["rates"]
            return {c.upper():rates.get(c.upper(),"N/A") for c in currencies}
        return {"error":"فشل"}

    @staticmethod
    def add_to_portfolio(symbol: str, amount: float, buy_price: float) -> str:
        with _db() as db:
            db.execute("INSERT INTO portfolio (symbol,amount,buy_price,date) VALUES (?,?,?,?)",
                       (symbol.upper(),amount,buy_price,datetime.now().strftime("%Y-%m-%d")))
        return f"✅ أضيف {amount} {symbol.upper()} بسعر {buy_price}"

    @staticmethod
    def portfolio_value() -> list:
        with _db() as db:
            rows = db.execute("SELECT id,symbol,amount,buy_price,date FROM portfolio").fetchall()
        result = []
        for r in rows:
            sym   = r[1]
            price_data = CryptoFinanceTools.crypto_price(sym)
            curr_price = price_data.get("usd",0) if not price_data.get("error") else 0
            if not curr_price:
                stock = CryptoFinanceTools.stock_price(sym)
                curr_price = stock.get("price",0)
            buy_val  = r[2] * r[3]
            curr_val = r[2] * curr_price
            pnl      = curr_val - buy_val
            result.append({
                "symbol":sym,"amount":r[2],"buy_price":r[3],
                "current_price":curr_price,"buy_value":round(buy_val,2),
                "current_value":round(curr_val,2),"PnL":round(pnl,2),
                "PnL%":round(pnl/buy_val*100,2) if buy_val else 0,
                "date":r[4]
            })
        return result

    @staticmethod
    def set_price_alert(symbol: str, target: float, direction="above") -> str:
        """direction: above / below"""
        with _db() as db:
            db.execute("INSERT INTO price_alerts (symbol,target,direction,created) VALUES (?,?,?,?)",
                       (symbol.upper(),target,direction,datetime.now().isoformat()))
        return f"✅ تنبيه: {symbol.upper()} {'فوق' if direction=='above' else 'تحت'} {target}"

    @staticmethod
    def check_price_alerts() -> list:
        with _db() as db:
            rows = db.execute("SELECT id,symbol,target,direction FROM price_alerts WHERE active=1").fetchall()
        triggered = []
        for r in rows:
            price_data = CryptoFinanceTools.crypto_price(r[1])
            curr = price_data.get("usd",0)
            if not curr: continue
            hit = (r[3]=="above" and curr>=r[2]) or (r[3]=="below" and curr<=r[2])
            if hit:
                triggered.append({"id":r[0],"symbol":r[1],"target":r[2],"current":curr,"direction":r[3]})
                with _db() as db:
                    db.execute("UPDATE price_alerts SET active=0 WHERE id=?",(r[0],))
        return triggered

    @staticmethod
    def compound_interest(principal: float, rate: float, years: int, compounds_per_year=12) -> dict:
        n  = compounds_per_year
        r  = rate/100
        A  = principal * (1 + r/n)**(n*years)
        return {"رأس_المال":principal,"معدل_الفائدة":f"{rate}%","السنوات":years,
                "القيمة_النهائية":round(A,2),"الفائدة_المكتسبة":round(A-principal,2)}

    @staticmethod
    def investment_calculator(monthly: float, rate: float, years: int) -> dict:
        """حاسبة الاستثمار الشهري"""
        r    = rate/100/12
        n    = years*12
        FV   = monthly * ((1+r)**n - 1) / r * (1+r) if r else monthly*n
        total_invested = monthly * n
        return {"الاستثمار_الشهري":monthly,"معدل_الفائدة_السنوي":f"{rate}%",
                "السنوات":years,"إجمالي_الاستثمار":total_invested,
                "القيمة_المستقبلية":round(FV,2),"العائد":round(FV-total_invested,2)}

    @staticmethod
    def price_chart_ascii(history: list, width=50) -> str:
        """رسم بياني نصي للأسعار"""
        if not history: return "لا توجد بيانات"
        prices = [h.get("price",h.get("close",0)) for h in history]
        dates  = [h.get("date","") for h in history]
        min_p  = min(prices); max_p = max(prices)
        if max_p == min_p: return "السعر ثابت"
        chart  = []
        for i,p in enumerate(prices):
            bar_len = int((p-min_p)/(max_p-min_p)*width)
            date    = dates[i][-5:] if dates else ""
            change  = "▲" if i>0 and p>prices[i-1] else "▼" if i>0 else " "
            chart.append(f"  {date} {change} {'█'*bar_len}{'░'*(width-bar_len)} ${p:.2f}")
        header = f"\n  {'─'*60}\n  Min: ${min_p:.2f} | Max: ${max_p:.2f}\n  {'─'*60}\n"
        return header + '\n'.join(chart)

if __name__ == "__main__":
    cf = CryptoFinanceTools()
    menu = {
        "1":  ("سعر عملة رقمية",           lambda: print(json.dumps(cf.crypto_price(input("العملة (bitcoin/BTC) => ")), indent=2, ensure_ascii=False))),
        "2":  ("أعلى 10 عملات",            lambda: [print(f"  {c['rank']:>2}. {c['name']:<20} ${c['price']:<12.4f} {c['change_24h']:+.2f}%") for c in cf.crypto_top()]),
        "3":  ("تاريخ أسعار عملة",          lambda: print(cf.price_chart_ascii(cf.crypto_history(input("ID العملة (bitcoin) => "), int(input("أيام (7) => ") or 7))))),
        "4":  ("بحث عن عملة",              lambda: [print(f"  {c['id']:<20} {c['name']:<20} {c['symbol']}") for c in cf.crypto_search(input("البحث => "))]),
        "5":  ("سعر سهم",                  lambda: print(json.dumps(cf.stock_price(input("رمز السهم (AAPL/2222.SR) => ")), indent=2))),
        "6":  ("تاريخ سهم",               lambda: print(cf.price_chart_ascii(cf.stock_history(input("الرمز => "), input("الفترة (1mo/3mo/1y) => ") or "1mo")))),
        "7":  ("سعر صرف",                  lambda: print(json.dumps(cf.exchange_rate(input("من => "), input("إلى => ")), indent=2))),
        "8":  ("تحويل عملة",               lambda: print(cf.convert_currency(float(input("المبلغ => ")), input("من => "), input("إلى => ")))),
        "9":  ("أسعار متعددة",             lambda: print(json.dumps(cf.multi_currency(input("العملة الأساسية => "), input("العملات (مسافة) => ").split()), indent=2))),
        "10": ("إضافة للمحفظة",            lambda: print(cf.add_to_portfolio(input("الرمز => "), float(input("الكمية => ")), float(input("سعر الشراء => "))))),
        "11": ("قيمة المحفظة",             lambda: [print(f"  {p['symbol']:<8} {p['amount']:<8} بسعر ${p['current_price']:<10.4f} PnL: ${p['PnL']:+.2f} ({p['PnL%']:+.2f}%)") for p in cf.portfolio_value()]),
        "12": ("تنبيه سعر",                lambda: print(cf.set_price_alert(input("الرمز => "), float(input("السعر المستهدف => ")), input("فوق/تحت (above/below) => ") or "above"))),
        "13": ("فحص التنبيهات",            lambda: print(json.dumps(cf.check_price_alerts(), indent=2))),
        "14": ("حاسبة الفائدة المركبة",    lambda: print(json.dumps(cf.compound_interest(float(input("رأس المال => ")), float(input("معدل الفائدة% => ")), int(input("السنوات => "))), indent=2, ensure_ascii=False))),
        "15": ("حاسبة الاستثمار الشهري",   lambda: print(json.dumps(cf.investment_calculator(float(input("الاستثمار الشهري => ")), float(input("الفائدة السنوية% => ")), int(input("السنوات => "))), indent=2, ensure_ascii=False))),
    }
    while True:
        print("\n═"*45)
        print("  💰  Crypto & Finance — 15 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
