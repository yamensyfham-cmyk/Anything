"""
أدوات تحليل البيانات — pure Python
يتضمن: MiniFrame (بديل pandas) + TextChart (بديل matplotlib)
صفر مكاتب خارجية — يعمل على Termux مباشرة
"""
import os, sys, json, csv, math, re, collections, statistics
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

class MiniFrame:
    """
    DataFrame مصغر — بديل pandas كامل بـ pure Python
    يدعم: CSV, TSV, JSON, Excel(بدون مكاتب), فلترة، ترتيب، تجميع، إحصاء
    """

    def __init__(self, rows=None, columns=None):
        self._cols = list(columns or [])
        self._rows = [list(r) for r in (rows or [])]

    @classmethod
    def read_csv(cls, path, delimiter=',', encoding='utf-8-sig'):
        with open(path, encoding=encoding, errors='replace', newline='') as f:
            reader = csv.reader(f, delimiter=delimiter)
            rows   = list(reader)
        if not rows: return cls()
        cols = rows[0]
        data = rows[1:]
        return cls(data, cols)

    @classmethod
    def read_tsv(cls, path):
        return cls.read_csv(path, delimiter='\t')

    @classmethod
    def read_json(cls, path):
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list) and data:
            cols = list(data[0].keys())
            rows = [[str(row.get(c,'')) for c in cols] for row in data]
            return cls(rows, cols)
        return cls()

    @classmethod
    def read_excel_simple(cls, path):
        """قراءة xlsx بدون openpyxl — يقرأ كـ zip/xml"""
        import zipfile, xml.etree.ElementTree as ET
        try:
            with zipfile.ZipFile(path) as z:

                shared = []
                if 'xl/sharedStrings.xml' in z.namelist():
                    tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
                    ns = {'n':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                    for si in tree.findall('.//n:si',ns):
                        t = si.find('.//n:t',ns)
                        shared.append(t.text if t is not None else '')

                sheet_name = 'xl/worksheets/sheet1.xml'
                if sheet_name not in z.namelist():
                    sheets = [n for n in z.namelist() if n.startswith('xl/worksheets/sheet')]
                    if not sheets: return cls()
                    sheet_name = sheets[0]
                tree = ET.fromstring(z.read(sheet_name))
                ns = {'n':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
                all_rows = []
                for row in tree.findall('.//n:row',ns):
                    row_data = []
                    for c in row.findall('n:c',ns):
                        t = c.get('t','')
                        v = c.find('n:v',ns)
                        val = ''
                        if v is not None:
                            if t == 's': val = shared[int(v.text)] if v.text else ''
                            else: val = v.text or ''
                        row_data.append(val)
                    all_rows.append(row_data)
                if not all_rows: return cls()

                maxlen = max(len(r) for r in all_rows)
                for r in all_rows:
                    while len(r) < maxlen: r.append('')
                return cls(all_rows[1:], all_rows[0])
        except Exception as e:
            return cls()

    def __len__(self): return len(self._rows)

    @property
    def columns(self): return list(self._cols)

    @property
    def shape(self): return (len(self._rows), len(self._cols))

    def _ci(self, col):
        """فهرس العمود"""
        if isinstance(col, int): return col
        try: return self._cols.index(col)
        except ValueError: raise KeyError(f"عمود غير موجود: '{col}'")

    def col(self, name):
        """إرجاع قيم عمود كقائمة"""
        i = self._ci(name)
        return [r[i] for r in self._rows]

    def head(self, n=10):
        return MiniFrame(self._rows[:n], self._cols)

    def tail(self, n=10):
        return MiniFrame(self._rows[-n:], self._cols)

    def info(self) -> dict:
        nulls = {}
        for col in self._cols:
            vals = self.col(col)
            nulls[col] = sum(1 for v in vals if v in ('','None','nan','NULL',None))
        return {
            "الصفوف":   len(self._rows),
            "الأعمدة":  len(self._cols),
            "الأعمدة_أسماء": self._cols,
            "القيم_الفارغة": nulls,
            "المساحة_KB": round(sum(len(str(r)) for r in self._rows) / 1024, 1),
        }

    def describe(self) -> dict:
        result = {}
        for col in self._cols:
            nums = self._to_nums(col)
            if nums:
                result[col] = {
                    "count": len(nums),
                    "mean":  round(statistics.mean(nums), 4),
                    "std":   round(statistics.stdev(nums), 4) if len(nums)>1 else 0,
                    "min":   min(nums),
                    "25%":   self._percentile(nums, 25),
                    "50%":   self._percentile(nums, 50),
                    "75%":   self._percentile(nums, 75),
                    "max":   max(nums),
                }
            else:
                vals = [v for v in self.col(col) if v not in ('',None)]
                freq = collections.Counter(vals)
                result[col] = {
                    "count":  len(vals),
                    "unique": len(freq),
                    "top":    freq.most_common(1)[0][0] if freq else '',
                    "freq":   freq.most_common(1)[0][1] if freq else 0,
                }
        return result

    def _to_nums(self, col):
        nums = []
        for v in self.col(col):
            try: nums.append(float(str(v).replace(',','')))
            except Exception: pass
        return nums

    @staticmethod
    def _percentile(data, pct):
        s = sorted(data)
        k = (len(s)-1) * pct/100
        f, c = int(k), math.ceil(k)
        if f == c: return round(s[int(k)], 4)
        return round(s[f]*(c-k) + s[c]*(k-f), 4)

    def dropna(self):
        empty = {'','None','nan','NULL','none'}
        rows = [r for r in self._rows if not any(str(v).strip() in empty or v is None for v in r)]
        return MiniFrame(rows, self._cols)

    def fillna(self, value='0'):
        empty = {'','None','nan','NULL','none'}
        rows = [[value if str(v).strip() in empty else v for v in r] for r in self._rows]
        return MiniFrame(rows, self._cols)

    def drop_duplicates(self):
        seen, rows = set(), []
        for r in self._rows:
            key = tuple(r)
            if key not in seen:
                seen.add(key); rows.append(r)
        return MiniFrame(rows, self._cols)

    def drop_column(self, col):
        i = self._ci(col)
        cols = [c for j,c in enumerate(self._cols) if j!=i]
        rows = [[v for j,v in enumerate(r) if j!=i] for r in self._rows]
        return MiniFrame(rows, cols)

    def rename(self, mapping: dict):
        cols = [mapping.get(c,c) for c in self._cols]
        return MiniFrame([r[:] for r in self._rows], cols)

    def filter(self, col, op, value):
        i = self._ci(col)
        rows = []
        for r in self._rows:
            v = r[i]
            try: v_n, val_n = float(str(v).replace(',','')), float(str(value).replace(',',''))
            except Exception: v_n = val_n = None
            if v_n is not None:
                match = (op=='>' and v_n>val_n) or (op=='<' and v_n<val_n) or\
                        (op=='>=' and v_n>=val_n) or (op=='<=' and v_n<=val_n) or\
                        (op=='==' and v_n==val_n) or (op=='!=' and v_n!=val_n)
            else:
                match = (op=='==' and str(v)==str(value)) or (op=='!=' and str(v)!=str(value))
            if match: rows.append(r)
        return MiniFrame(rows, self._cols)

    def search(self, col, query):
        i = self._ci(col)
        q = str(query).lower()
        rows = [r for r in self._rows if q in str(r[i]).lower()]
        return MiniFrame(rows, self._cols)

    def sort(self, col, asc=True):
        i = self._ci(col)
        def key(r):
            try: return (0, float(str(r[i]).replace(',','')))
            except: return (1, str(r[i]))
        rows = sorted(self._rows, key=key, reverse=not asc)
        return MiniFrame(rows, self._cols)

    def groupby(self, col, agg='count'):
        i = self._ci(col)
        groups = collections.defaultdict(list)
        for r in self._rows:
            groups[r[i]].append(r)

        result_rows = []
        result_cols = [col, agg]
        for key, rows in sorted(groups.items()):
            if agg == 'count':
                val = len(rows)
            elif agg == 'sum':
                nums = [float(str(r[0]).replace(',','')) for r in rows for v in r if v != r[i]]
                val  = sum(nums) if nums else 0
            elif agg == 'mean':
                all_nums = []
                for r in rows:
                    for j,v in enumerate(r):
                        if j != i:
                            try: all_nums.append(float(str(v).replace(',','')))\
                            ; break
                            except: pass
                val = round(statistics.mean(all_nums), 4) if all_nums else 0
            else:
                val = len(rows)
            result_rows.append([key, val])
        return MiniFrame(result_rows, result_cols)

    def column_stats(self, col) -> dict:
        nums = self._to_nums(col)
        vals = self.col(col)
        result = {"عمود":col, "عدد":len(vals)}
        if nums:
            result.update({
                "متوسط":   round(statistics.mean(nums), 4),
                "وسيط":   round(statistics.median(nums), 4),
                "انحراف": round(statistics.stdev(nums), 4) if len(nums)>1 else 0,
                "أدنى":   min(nums), "أعلى":  max(nums),
                "مجموع":  round(sum(nums), 4),
            })
        else:
            freq = collections.Counter(v for v in vals if v not in ('',None))
            result["أكثر_تكراراً"] = dict(freq.most_common(5))
        return result

    def correlation(self) -> dict:
        """حساب الارتباط بين الأعمدة الرقمية"""
        num_cols = [(c, self._to_nums(c)) for c in self._cols if len(self._to_nums(c)) > 1]
        if len(num_cols) < 2: return {"note":"يحتاج عمودين رقميين على الأقل"}
        result = {}
        for c1, n1 in num_cols:
            result[c1] = {}
            for c2, n2 in num_cols:
                n  = min(len(n1),len(n2))
                if n < 2: result[c1][c2] = None; continue
                a, b = n1[:n], n2[:n]
                ma, mb = sum(a)/n, sum(b)/n
                num  = sum((x-ma)*(y-mb) for x,y in zip(a,b))
                dena = math.sqrt(sum((x-ma)**2 for x in a))
                denb = math.sqrt(sum((y-mb)**2 for y in b))
                result[c1][c2] = round(num/(dena*denb),4) if dena*denb else None
        return result

    @staticmethod
    def concat(frames):
        if not frames: return MiniFrame()
        cols = frames[0]._cols
        rows = []
        for f in frames:
            for r in f._rows:
                if len(r) < len(cols): r = r + ['']*(len(cols)-len(r))
                rows.append(r[:len(cols)])
        return MiniFrame(rows, cols)

    def to_csv(self, path, encoding='utf-8-sig'):
        with open(path, 'w', encoding=encoding, newline='') as f:
            w = csv.writer(f)
            w.writerow(self._cols)
            w.writerows(self._rows)
        return f"✅ {path} ({len(self._rows)} صف)"

    def to_json(self, path):
        data = [{c: r[i] if i < len(r) else '' for i,c in enumerate(self._cols)} for r in self._rows]
        json.dump(data, open(path,'w',encoding='utf-8'), indent=2, ensure_ascii=False)
        return f"✅ {path}"

    def to_excel(self, path):
        """كتابة xlsx بدون openpyxl — XML خالص"""
        import zipfile, datetime
        NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        shared_strs, str_idx = [], {}

        def si(val):
            v = str(val)
            if v not in str_idx:
                str_idx[v] = len(shared_strs)
                shared_strs.append(v)
            return str_idx[v]

        def col_letter(n):
            s = ''
            while n >= 0:
                s = chr(n%26+65) + s; n = n//26 - 1
            return s

        rows_xml = ''
        all_rows = [self._cols] + self._rows
        for ri, row in enumerate(all_rows, 1):
            cells = ''
            for ci, val in enumerate(row):
                cl  = f"{col_letter(ci)}{ri}"
                try:
                    float(str(val).replace(',',''))
                    cells += f'<c r="{cl}"><v>{val}</v></c>'
                except Exception:
                    idx = si(val)
                    cells += f'<c r="{cl}" t="s"><v>{idx}</v></c>'
            rows_xml += f'<row r="{ri}">{cells}</row>'

        sheet_xml = f'<?xml version="1.0" encoding="UTF-8"?><worksheet {NS}><sheetData>{rows_xml}</sheetData></worksheet>'
        ss_xml    = f'<?xml version="1.0" encoding="UTF-8"?><sst {NS} count="{len(shared_strs)}" uniqueCount="{len(shared_strs)}">'
        for s in shared_strs: ss_xml += f'<si><t>{s.replace("&","&amp;").replace("<","&lt;")}</t></si>'
        ss_xml += '</sst>'
        wb_xml = f'<?xml version="1.0" encoding="UTF-8"?><workbook {NS}><sheets><sheet name="Sheet1" sheetId="1" r:id="rId1" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/></sheets></workbook>'
        rels_wb = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/></Relationships>'
        rels_root= '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'
        ct = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/></Types>'

        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('[Content_Types].xml', ct)
            z.writestr('_rels/.rels', rels_root)
            z.writestr('xl/workbook.xml', wb_xml)
            z.writestr('xl/_rels/workbook.xml.rels', rels_wb)
            z.writestr('xl/worksheets/sheet1.xml', sheet_xml)
            z.writestr('xl/sharedStrings.xml', ss_xml)
        return f"✅ {path}"

    def to_string(self, max_rows=20, max_col_width=20) -> str:
        cols   = self._cols
        widths = [min(max_col_width, max(len(str(c)), max((len(str(r[i] if i<len(r) else '')) for r in self._rows[:max_rows]), default=0))) for i,c in enumerate(cols)]
        def fmt(v, w): return str(v)[:w].ljust(w)
        sep  = '─' * (sum(widths) + 3*len(widths))
        head = ' │ '.join(fmt(c,w) for c,w in zip(cols,widths))
        rows = [' │ '.join(fmt(r[i] if i<len(r) else '', w) for i,w in enumerate(widths)) for r in self._rows[:max_rows]]
        suffix = f"\n  ... ({len(self._rows)-max_rows} صف إضافي)" if len(self._rows)>max_rows else ""
        return f"{sep}\n{head}\n{sep}\n" + '\n'.join(rows) + suffix + f"\n{sep}"

def read_file(path: str) -> MiniFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext == '.csv':   return MiniFrame.read_csv(path)
    if ext in ('.xlsx','.xls'): return MiniFrame.read_excel_simple(path)
    if ext == '.json':  return MiniFrame.read_json(path)
    if ext in ('.tsv','.txt'): return MiniFrame.read_tsv(path)
    raise ValueError(f"صيغة غير مدعومة: {ext}")

class TextChart:
    WIDTH  = 50
    HEIGHT = 15

    @staticmethod
    def bar(labels, values, title="", width=50):
        if not values: return "لا بيانات"
        max_v = max(values) or 1
        out   = [f"\n  {'─'*60}"]
        if title: out.append(f"  📊 {title}")
        out.append(f"  {'─'*60}")
        for label, val in zip(labels, values):
            bar_len = int(val / max_v * width)
            bar     = '█' * bar_len + '░' * (width - bar_len)

            if val >= 1e9:       val_s = f"{val/1e9:.2f}B"
            elif val >= 1e6:     val_s = f"{val/1e6:.2f}M"
            elif val >= 1000:    val_s = f"{val/1000:.1f}K"
            elif isinstance(val,float): val_s = f"{val:.2f}"
            else:                val_s = str(val)
            out.append(f"  {str(label)[:15]:<15} │{bar}│ {val_s}")
        out.append(f"  {'─'*60}")
        return '\n'.join(out)

    @staticmethod
    def line(labels, values, title="", width=50, height=12):
        if not values: return "لا بيانات"
        min_v, max_v = min(values), max(values)
        if max_v == min_v: max_v = min_v + 1
        out = [f"\n  {'─'*60}"]
        if title: out.append(f"  📈 {title}")
        out.append(f"  {'─'*60}")

        grid = [[' '] * width for _ in range(height)]
        n    = len(values)
        for i, v in enumerate(values):
            x = int(i / (n-1) * (width-1)) if n > 1 else 0
            y = int((v - min_v) / (max_v - min_v) * (height-1))
            y = height - 1 - y
            grid[y][x] = '●'

            if i > 0:
                px = int((i-1)/(n-1)*(width-1)) if n>1 else 0
                py = int((values[i-1]-min_v)/(max_v-min_v)*(height-1))
                py = height-1-py
                for xx in range(min(x,px)+1, max(x,px)):
                    t = (xx-px)/(x-px) if x!=px else 0
                    yy = int(py + t*(y-py))
                    if 0<=yy<height: grid[yy][xx] = '·'
        for row in grid:
            out.append('  │' + ''.join(row) + '│')

        step  = max(1, len(labels)//5)
        x_ax  = ' ' * 3
        for i in range(0, len(labels), step):
            x = int(i/(n-1)*(width-1)) if n>1 else 0
            lbl = str(labels[i])[:6]
            x_ax += lbl.ljust(max(1,width//max(1,len(range(0,len(labels),step)))))
        out.append(f"  └{'─'*width}┘")
        out.append(f"  {x_ax}")
        out.append(f"  min:{min_v:.2f}  max:{max_v:.2f}")
        return '\n'.join(out)

    @staticmethod
    def pie(labels, values, title=""):
        if not values: return "لا بيانات"
        total = sum(values) or 1
        out   = [f"\n  {'─'*50}"]
        if title: out.append(f"  🥧 {title}")
        out.append(f"  {'─'*50}")
        icons = ['█','▓','▒','░','▪','▫','●','○','◆','◇']
        for i, (label, val) in enumerate(zip(labels, values)):
            pct = val / total * 100
            bar = icons[i % len(icons)] * int(pct / 2)
            out.append(f"  {icons[i%len(icons)]} {str(label)[:20]:<20} {bar:<50} {pct:.1f}%")
        out.append(f"  {'─'*50}  المجموع: {total:.2f}")
        return '\n'.join(out)

    @staticmethod
    def histogram(values, bins=15, title=""):
        if not values: return "لا بيانات"
        min_v, max_v = min(values), max(values)
        if max_v == min_v: return f"كل القيم = {min_v}"
        bin_size = (max_v - min_v) / bins
        counts   = [0] * bins
        for v in values:
            idx = min(int((v - min_v) / bin_size), bins-1)
            counts[idx] += 1
        labels = [f"{min_v + i*bin_size:.1f}" for i in range(bins)]
        return TextChart.bar(labels, counts, title or "Histogram")

    @staticmethod
    def save_html(chart_type, labels, values, title, out_path):
        """تصدير رسم بياني كـ HTML تفاعلي بدون مكاتب"""
        colors = ['#3498db','#e74c3c','#2ecc71','#f39c12','#9b59b6',
                  '#1abc9c','#e67e22','#95a5a6','#2c3e50','#e91e63']
        total = sum(values) or 1
        if chart_type == 'bar':
            bars = ''
            for i,(l,v) in enumerate(zip(labels,values)):
                h   = int(v/max(values)*200) if max(values) else 0
                bars += f'<div class="bar" style="height:{h}px;background:{colors[i%len(colors)]}" title="{l}: {v}"><span>{v:.1f}</span></div>'
            body = f'<div class="chart bar-chart">{bars}</div>'
            lbls = ''.join(f'<span>{l}</span>' for l in labels)
            body += f'<div class="labels">{lbls}</div>'
        elif chart_type == 'pie':

            svg  = '<svg viewBox="0 0 200 200" width="300" height="300">'
            cx,cy,r = 100,100,80
            start = 0
            for i,(l,v) in enumerate(zip(labels,values)):
                angle = v/total * 360
                end   = start + angle
                sr,er = math.radians(start-90), math.radians(end-90)
                x1,y1 = cx+r*math.cos(sr), cy+r*math.sin(sr)
                x2,y2 = cx+r*math.cos(er), cy+r*math.sin(er)
                lg    = 1 if angle > 180 else 0
                svg  += f'<path d="M{cx},{cy} L{x1:.1f},{y1:.1f} A{r},{r},0,{lg},1,{x2:.1f},{y2:.1f} Z" fill="{colors[i%len(colors)]}" title="{l}:{v:.1f}"/>'
                start = end
            svg += '</svg>'
            legend = ''.join(f'<span style="color:{colors[i%len(colors)]}">■ {l} ({v/total*100:.1f}%)</span><br>' for i,(l,v) in enumerate(zip(labels,values)))
            body  = svg + f'<div style="margin-top:10px">{legend}</div>'
        else:
            body = TextChart.line(labels, values, title)

        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{title}</title><style>
body{{font-family:Arial;padding:20px;background:#1a1a2e;color:#eee}}
h2{{color:#00d4ff}} .chart{{display:flex;align-items:flex-end;gap:5px;height:220px;padding:10px;background:#16213e;border-radius:8px}}
.bar{{width:40px;display:flex;align-items:flex-end;justify-content:center;border-radius:4px 4px 0 0;transition:.3s;cursor:pointer;position:relative}}
.bar:hover{{opacity:.8}} .bar span{{position:absolute;top:-20px;font-size:10px}}
.labels{{display:flex;gap:5px;margin-top:5px}} .labels span{{width:40px;text-align:center;font-size:10px;overflow:hidden}}
</style></head><body>
<h2>{title}</h2>{body}
<p style="color:#666;font-size:12px">UAS Data Analysis — {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</body></html>"""
        with open(out_path,'w',encoding='utf-8') as f: f.write(html)
        return f"✅ {out_path}"

class DataTools:

    @staticmethod
    def info(path): return read_file(path).info()

    @staticmethod
    def head(path, n=10): return read_file(path).head(n).to_string()

    @staticmethod
    def tail(path, n=10): return read_file(path).tail(n).to_string()

    @staticmethod
    def describe(path): return json.dumps(read_file(path).describe(), indent=2, ensure_ascii=False)

    @staticmethod
    def column_stats(path, col):
        return read_file(path).column_stats(col)

    @staticmethod
    def search(path, col, query):
        df = read_file(path).search(col, query)
        return f"نتائج ({len(df)}):\n{df.to_string()}"

    @staticmethod
    def filter_rows(path, col, op, value, out=None):
        df = read_file(path).filter(col, op, value)
        if out: df.to_csv(out); return f"✅ {len(df)} صف → {out}"
        return df.to_string()

    @staticmethod
    def sort(path, col, asc=True, out=None):
        df = read_file(path).sort(col, asc)
        if out: df.to_csv(out); return f"✅ مرتّب → {out}"
        return df.to_string()

    @staticmethod
    def group_by(path, col, agg="count"):
        return read_file(path).groupby(col, agg).to_string()

    @staticmethod
    def correlation(path):
        return json.dumps(read_file(path).correlation(), indent=2, ensure_ascii=False)

    @staticmethod
    def drop_nulls(path, out=None):
        df = read_file(path).dropna()
        out = out or path
        df.to_csv(out)
        return f"✅ {out}"

    @staticmethod
    def remove_duplicates(path, out=None):
        df = read_file(path).drop_duplicates()
        out = out or path
        df.to_csv(out)
        return f"✅ {out}"

    @staticmethod
    def merge_files(paths, out):
        frames = [read_file(p) for p in paths]
        merged = MiniFrame.concat(frames)
        merged.to_csv(out)
        return f"✅ {len(merged)} صف → {out}"

    @staticmethod
    def to_csv(path, out):   return read_file(path).to_csv(out)
    @staticmethod
    def to_excel(path, out): return read_file(path).to_excel(out)
    @staticmethod
    def to_json(path, out):  return read_file(path).to_json(out)

    @staticmethod
    def plot_bar(path, x_col, y_col, out=None):
        df  = read_file(path)
        xs  = df.col(x_col)
        ys  = df._to_nums(y_col)
        if len(xs) != len(ys): ys = ys[:len(xs)]
        chart = TextChart.bar(xs, ys, f"{y_col} by {x_col}")
        print(chart)
        if out: TextChart.save_html('bar', xs, ys, f"{y_col} by {x_col}", out)
        return chart

    @staticmethod
    def plot_line(path, x_col, y_col, out=None):
        df  = read_file(path)
        xs  = df.col(x_col)
        ys  = df._to_nums(y_col)
        chart = TextChart.line(xs, ys, f"{y_col} over {x_col}")
        print(chart)
        if out: TextChart.save_html('line', xs, ys, f"{y_col} over {x_col}", out)
        return chart

    @staticmethod
    def plot_pie(path, col, out=None):
        df   = read_file(path)
        freq = collections.Counter(df.col(col))
        top  = dict(freq.most_common(8))
        chart = TextChart.pie(list(top.keys()), [float(v) for v in top.values()], col)
        print(chart)
        if out: TextChart.save_html('pie', list(top.keys()), list(top.values()), col, out)
        return chart

    @staticmethod
    def plot_histogram(path, col, out=None):
        df    = read_file(path)
        nums  = df._to_nums(col)
        chart = TextChart.histogram(nums, title=f"Histogram — {col}")
        print(chart)
        return chart

    @staticmethod
    def quick_report(path, out="report.txt"):
        df  = read_file(path)
        lines = [
            f"═══ تقرير: {os.path.basename(path)} ═══",
            f"الصفوف: {len(df)} | الأعمدة: {len(df.columns)}",
            f"الأعمدة: {', '.join(df.columns)}",
            "",
            "إحصاءات:",
        ]
        desc = df.describe()
        for col, stats in desc.items():
            if 'mean' in stats:
                lines.append(f"  {col}: min={stats['min']} avg={stats['mean']} max={stats['max']}")
        info = df.info()
        lines.append("\nقيم فارغة:")
        for c, n in info['القيم_الفارغة'].items():
            if n > 0: lines.append(f"  {c}: {n}")
        report = '\n'.join(lines)
        with open(out,'w',encoding='utf-8') as f: f.write(report)
        return f"✅ {out}\n\n{report[:400]}"

if __name__ == "__main__":
    dt = DataTools()
    menu = {
        "1":  ("معلومات ملف",            lambda: print(json.dumps(dt.info(input("المسار => ")), indent=2, ensure_ascii=False))),
        "2":  ("أول صفوف",               lambda: print(dt.head(input("المسار => "), int(input("العدد (10) => ") or 10)))),
        "3":  ("آخر صفوف",               lambda: print(dt.tail(input("المسار => "), int(input("العدد (10) => ") or 10)))),
        "4":  ("إحصاءات وصفية",          lambda: print(dt.describe(input("المسار => ")))),
        "5":  ("إحصاء عمود",             lambda: print(json.dumps(dt.column_stats(input("المسار => "), input("العمود => ")), indent=2, ensure_ascii=False))),
        "6":  ("بحث في عمود",            lambda: print(dt.search(input("المسار => "), input("العمود => "), input("البحث => ")))),
        "7":  ("فلترة",                  lambda: print(dt.filter_rows(input("المسار => "), input("العمود => "), input("العملية (>/</==/!=) => "), input("القيمة => "), input("حفظ (فارغ=عرض) => ") or None))),
        "8":  ("ترتيب",                  lambda: print(dt.sort(input("المسار => "), input("العمود => "), input("تصاعدي (نعم/لا) => ").lower() != "لا"))),
        "9":  ("تجميع",                  lambda: print(dt.group_by(input("المسار => "), input("العمود => "), input("العملية (count/sum/mean) => ") or "count"))),
        "10": ("ارتباط الأعمدة",          lambda: print(dt.correlation(input("المسار => ")))),
        "11": ("حذف فارغ",               lambda: print(dt.drop_nulls(input("المسار => ")))),
        "12": ("حذف مكرر",               lambda: print(dt.remove_duplicates(input("المسار => ")))),
        "13": ("دمج ملفات",              lambda: print(dt.merge_files(input("المسارات (مسافة) => ").split(), input("الإخراج => ")))),
        "14": ("تحويل لـ CSV",            lambda: print(dt.to_csv(input("المسار => "), input("الإخراج => ")))),
        "15": ("تحويل لـ Excel",          lambda: print(dt.to_excel(input("المسار => "), input("الإخراج => ")))),
        "16": ("رسم شريطي (نص+HTML)",    lambda: dt.plot_bar(input("المسار => "), input("عمود X => "), input("عمود Y => "), input("حفظ HTML (اختياري) => ") or None)),
        "17": ("رسم خطي",                lambda: dt.plot_line(input("المسار => "), input("عمود X => "), input("عمود Y => "))),
        "18": ("رسم دائري",              lambda: dt.plot_pie(input("المسار => "), input("العمود => "))),
        "19": ("مدرج تكراري",            lambda: dt.plot_histogram(input("المسار => "), input("العمود => "))),
        "20": ("تقرير شامل",             lambda: print(dt.quick_report(input("المسار => ")))),
    }
    print("\n═"*45)
    print("  📊  Data Analysis — pure Python")
    print("  بدون pandas/numpy/matplotlib")
    print("═"*45)
    while True:
        print()
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
