"""
أدوات الرياضيات والعلوم — 25 ميزة
مكاتب: stdlib فقط (math, statistics, random)
"""
import os, sys, math, statistics, random, json, re, itertools
from fractions import Fraction
from decimal   import Decimal, getcontext
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix
getcontext().prec = 50

class MathTools:

    @staticmethod
    def evaluate(expr: str) -> str:
        safe = {k:getattr(math,k) for k in dir(math) if not k.startswith('_')}
        safe.update({'abs':abs,'round':round,'min':min,'max':max,'sum':sum,
                     'Fraction':Fraction,'pow':pow,'sqrt':math.sqrt})
        try:
            result = eval(expr.replace('^','**'), {"__builtins__":{}}, safe)
            return f"{result}"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def prime_check(n: int) -> bool:
        if n < 2: return False
        if n < 4: return True
        if n % 2 == 0 or n % 3 == 0: return False
        i = 5
        while i*i <= n:
            if n%i==0 or n%(i+2)==0: return False
            i += 6
        return True

    @staticmethod
    def prime_factors(n: int) -> list:
        factors = []
        d = 2
        while d*d <= n:
            while n%d == 0: factors.append(d); n //= d
            d += 1
        if n > 1: factors.append(n)
        return factors

    @staticmethod
    def primes_up_to(n: int) -> list:
        """الأعداد الأولية حتى n (Sieve of Eratosthenes)"""
        sieve = [True]*(n+1)
        sieve[0]=sieve[1]=False
        for i in range(2, int(n**0.5)+1):
            if sieve[i]:
                for j in range(i*i, n+1, i): sieve[j]=False
        return [i for i,v in enumerate(sieve) if v]

    @staticmethod
    def gcd_lcm(a: int, b: int) -> dict:
        g = math.gcd(a,b)
        return {"GCD":g, "LCM":abs(a*b)//g}

    @staticmethod
    def fibonacci(n: int) -> list:
        if n<=0: return []
        if n==1: return [0]
        fibs = [0,1]
        while len(fibs)<n: fibs.append(fibs[-1]+fibs[-2])
        return fibs[:n]

    @staticmethod
    def factorial(n: int) -> int:
        return math.factorial(n)

    @staticmethod
    def power_mod(base: int, exp: int, mod: int) -> int:
        return pow(base, exp, mod)

    @staticmethod
    def base_convert(number: str, from_base: int, to_base: int) -> str:
        try:
            decimal = int(number, from_base)
            if to_base == 2:  return bin(decimal)[2:]
            if to_base == 8:  return oct(decimal)[2:]
            if to_base == 16: return hex(decimal)[2:].upper()
            if to_base == 10: return str(decimal)

            digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            result = ""
            while decimal:
                result = digits[decimal%to_base] + result
                decimal //= to_base
            return result or "0"
        except Exception as e: return f"❌ {e}"

    @staticmethod
    def matrix_multiply(a: list, b: list) -> list:
        rows_a, cols_a = len(a), len(a[0])
        rows_b, cols_b = len(b), len(b[0])
        if cols_a != rows_b: raise ValueError("أبعاد غير متوافقة")
        result = [[0]*cols_b for _ in range(rows_a)]
        for i in range(rows_a):
            for j in range(cols_b):
                for k in range(cols_a):
                    result[i][j] += a[i][k]*b[k][j]
        return result

    @staticmethod
    def solve_quadratic(a: float, b: float, c: float) -> dict:
        """حل المعادلة التربيعية ax²+bx+c=0"""
        disc = b*b - 4*a*c
        if disc > 0:
            x1 = (-b+math.sqrt(disc))/(2*a)
            x2 = (-b-math.sqrt(disc))/(2*a)
            return {"x1":round(x1,6),"x2":round(x2,6),"نوع":"حلان حقيقيان"}
        elif disc == 0:
            x = -b/(2*a)
            return {"x":round(x,6),"نوع":"حل واحد"}
        else:
            real = -b/(2*a)
            imag = math.sqrt(-disc)/(2*a)
            return {"x1":f"{round(real,4)}+{round(imag,4)}i",
                    "x2":f"{round(real,4)}-{round(imag,4)}i","نوع":"حلان مركبان"}

    @staticmethod
    def polynomial_eval(coeffs: list, x: float) -> float:
        """تقييم كثير الحدود عند x"""
        return sum(c * x**i for i,c in enumerate(reversed(coeffs)))

    @staticmethod
    def pi_digits(n: int) -> str:
        """حساب n رقم من π"""
        getcontext().prec = n + 10
        mp_one = Decimal(1)
        mp_two = Decimal(2)
        mp_four= Decimal(4)
        def bs(a,b):
            if b-a == 1:
                p = -(6*a-5)*(2*a-1)*(6*a-1)
                q = Decimal(10939058860032000) * a**3
                t = p*(13591409+545140134*a)
                return p,q,t
            m = (a+b)//2
            p1,q1,t1 = bs(a,m)
            p2,q2,t2 = bs(m,b)
            return p1*p2, q1*q2, t1*q2+p1*t2
        try:
            p,q,t = bs(1, max(2,n//14+2))
            return str(mp_four*mp_one/(Decimal(13591409)*q+t/q)*Decimal(426880)*Decimal(10005).sqrt())[:n+2]
        except Exception:
            return str(Decimal(math.pi))[:n+2]

    @staticmethod
    def permutations_count(n: int, r: int) -> int:
        return math.perm(n,r)

    @staticmethod
    def combinations_count(n: int, r: int) -> int:
        return math.comb(n,r)

    @staticmethod
    def probability(favorable: int, total: int) -> dict:
        p = favorable/total
        return {"احتمالية":round(p,4),"نسبة%":round(p*100,2),"نسبة":f"{favorable}/{total}"}

class StatisticsTools:

    @staticmethod
    def analyze(data: list) -> dict:
        if not data: return {"error":"البيانات فارغة"}
        n = len(data)
        return {
            "العدد":       n,
            "المجموع":     sum(data),
            "المتوسط":    round(statistics.mean(data),4),
            "الوسيط":    round(statistics.median(data),4),
            "المنوال":    statistics.mode(data) if n>1 else data[0],
            "الانحراف_المعياري": round(statistics.stdev(data),4) if n>1 else 0,
            "التباين":    round(statistics.variance(data),4) if n>1 else 0,
            "الأدنى":     min(data),
            "الأعلى":     max(data),
            "المدى":      max(data)-min(data),
            "الربيع_الأول":  round(statistics.quantiles(data,n=4)[0],4) if n>3 else min(data),
            "الربيع_الثالث": round(statistics.quantiles(data,n=4)[2],4) if n>3 else max(data),
        }

    @staticmethod
    def regression_linear(x: list, y: list) -> dict:
        """الانحدار الخطي"""
        n = len(x)
        sx,sy = sum(x),sum(y)
        sxy   = sum(xi*yi for xi,yi in zip(x,y))
        sx2   = sum(xi**2 for xi in x)
        slope = (n*sxy-sx*sy)/(n*sx2-sx**2)
        inter = (sy-slope*sx)/n

        xm,ym = sx/n, sy/n
        r_num = sum((xi-xm)*(yi-ym) for xi,yi in zip(x,y))
        r_den = math.sqrt(sum((xi-xm)**2 for xi in x)*sum((yi-ym)**2 for yi in y))
        r     = r_num/r_den if r_den else 0
        return {"slope":round(slope,4),"intercept":round(inter,4),
                "r":round(r,4),"r2":round(r**2,4),
                "equation":f"y = {round(slope,4)}x + {round(inter,4)}"}

    @staticmethod
    def z_score(value: float, data: list) -> float:
        m = statistics.mean(data)
        s = statistics.stdev(data)
        return round((value-m)/s,4) if s else 0

    @staticmethod
    def percentile(data: list, p: float) -> float:
        data = sorted(data)
        idx  = (len(data)-1)*p/100
        lo   = int(idx)
        hi   = lo+1
        if hi >= len(data): return data[-1]
        return round(data[lo]+(data[hi]-data[lo])*(idx-lo),4)

    @staticmethod
    def frequency_table(data: list) -> dict:
        freq = {}
        for v in data: freq[v] = freq.get(v,0)+1
        return dict(sorted(freq.items(),key=lambda x:-x[1]))

    @staticmethod
    def moving_average(data: list, window=3) -> list:
        return [round(sum(data[i:i+window])/window,4) for i in range(len(data)-window+1)]

class RandomTools:
    @staticmethod
    def dice(sides=6, count=1) -> list:
        return [random.randint(1,sides) for _ in range(count)]

    @staticmethod
    def coin_flip(count=1) -> list:
        return [random.choice(["صورة","كتابة"]) for _ in range(count)]

    @staticmethod
    def random_from_list(items: list, count=1) -> list:
        return random.choices(items, k=count)

    @staticmethod
    def shuffle(items: list) -> list:
        result = items.copy()
        random.shuffle(result)
        return result

    @staticmethod
    def random_name() -> str:
        first = ["محمد","أحمد","علي","عمر","خالد","سالم","ياسر","طارق","فيصل","نواف"]
        last  = ["الأحمد","العمري","الخالد","السالم","المحمد","البكر","الرشيد"]
        return f"{random.choice(first)} {random.choice(last)}"

if __name__ == "__main__":
    mt = MathTools()
    st = StatisticsTools()
    rt = RandomTools()
    menu = {
        "1":  ("حاسبة رياضية",           lambda: print(mt.evaluate(input("التعبير => ")))),
        "2":  ("فحص عدد أولي",            lambda: print("✅ أولي" if mt.prime_check(int(input("العدد => "))) else "❌ ليس أولياً")),
        "3":  ("العوامل الأولية",          lambda: print(mt.prime_factors(int(input("العدد => "))))),
        "4":  ("الأعداد الأولية حتى n",    lambda: print(mt.primes_up_to(int(input("n => "))))),
        "5":  ("GCD و LCM",               lambda: print(json.dumps(mt.gcd_lcm(int(input("a => ")), int(input("b => "))), indent=2))),
        "6":  ("متتالية فيبوناتشي",        lambda: print(mt.fibonacci(int(input("العدد => "))))),
        "7":  ("المضروب n!",               lambda: print(mt.factorial(int(input("n => "))))),
        "8":  ("تحويل الأرقام",            lambda: print(mt.base_convert(input("الرقم => "), int(input("من أساس => ")), int(input("إلى أساس => "))))),
        "9":  ("حل معادلة تربيعية",        lambda: print(json.dumps(mt.solve_quadratic(float(input("a => ")), float(input("b => ")), float(input("c => "))), indent=2, ensure_ascii=False))),
        "10": ("التباديل P(n,r)",           lambda: print(mt.permutations_count(int(input("n => ")), int(input("r => "))))),
        "11": ("التوافيق C(n,r)",           lambda: print(mt.combinations_count(int(input("n => ")), int(input("r => "))))),
        "12": ("الاحتمالية",               lambda: print(json.dumps(mt.probability(int(input("المواتية => ")), int(input("الكلية => "))), indent=2, ensure_ascii=False))),
        "13": ("أرقام π",                 lambda: print(mt.pi_digits(int(input("عدد الأرقام (50) => ") or 50)))),
        "14": ("تحليل إحصائي",            lambda: print(json.dumps(st.analyze([float(x) for x in input("الأرقام (مسافة) => ").split()]), indent=2, ensure_ascii=False))),
        "15": ("انحدار خطي",              lambda: print(json.dumps(st.regression_linear([float(x) for x in input("X (مسافة) => ").split()],[float(x) for x in input("Y (مسافة) => ").split()]), indent=2, ensure_ascii=False))),
        "16": ("جدول التكرار",            lambda: print(json.dumps(st.frequency_table([float(x) for x in input("الأرقام (مسافة) => ").split()]), indent=2))),
        "17": ("المتوسط المتحرك",          lambda: print(st.moving_average([float(x) for x in input("الأرقام (مسافة) => ").split()], int(input("النافذة (3) => ") or 3)))),
        "18": ("رمي نرد",                 lambda: print(rt.dice(int(input("عدد الأوجه (6) => ") or 6), int(input("عدد المرات (1) => ") or 1)))),
        "19": ("رمي عملة",                lambda: print(rt.coin_flip(int(input("عدد المرات => "))))),
        "20": ("اختيار عشوائي",           lambda: print(rt.random_from_list(input("العناصر (مسافة) => ").split(), int(input("العدد (1) => ") or 1)))),
    }
    while True:
        print("\n═"*45)
        print("  📐  Math & Science — 20 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
