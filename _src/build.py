#!/usr/bin/env python3
"""EasyCalc 사이트 생성기 / site generator.

사용법 (프로젝트 폴더에서):  python3 _src/build.py
- _src/calc.html        : 계산기 원본 (번역 window.I18N 포함)
- _src/guides/<lang>/   : 가이드 글 (첫 줄 <!--{json}--> 메타데이터)
- _src/pages/<lang>/    : 소개·문의·개인정보처리방침
결과물은 프로젝트 폴더(이 파일의 상위 폴더)에 생성됩니다.
GitHub Pages(Jekyll)는 밑줄(_)로 시작하는 폴더를 공개하지 않습니다.
"""
import json, os, re, subprocess, sys, html as H
from datetime import date

SRC = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('OUT') or os.path.dirname(SRC)
SITE = 'https://easycalc.co.kr'
TODAY = os.environ.get('BUILD_DATE') or date.today().isoformat()
LANGS = ['ko', 'en', 'vi', 'zh', 'ne', 'id', 'km', 'uz', 'th', 'my']
HREFLANG = {'zh': 'zh-Hans'}
OGLOC = {'ko': 'ko_KR', 'en': 'en_US', 'vi': 'vi_VN', 'zh': 'zh_CN', 'ne': 'ne_NP', 'id': 'id_ID',
         'km': 'km_KH', 'uz': 'uz_UZ', 'th': 'th_TH', 'my': 'my_MM'}
TOOLS = ['salary', 'severance', 'leave', 'loan', 'dutch']
TOOL_H = {'salary': 'salH', 'severance': 'svH', 'leave': 'lvH', 'loan': 'loanH', 'dutch': 'dutchH'}
TOOL_LEDE = {'salary': 'salLede', 'severance': 'svLede', 'leave': 'lvLede', 'loan': 'loanLede', 'dutch': 'dutchLede'}
TOOL_TAB = {'salary': 'tabSalary', 'severance': 'tabSev', 'leave': 'tabLeave', 'loan': 'tabLoan', 'dutch': 'tabDutch'}

# 사이트 공통 메뉴 문구 / chrome strings
CH = {
 'ko': ['가이드', '소개', '문의', '개인정보처리방침', '계산하기', '전체 가이드', 'EasyCalc 편집', '이 글은 일반적인 정보를 제공하며 세무·법률 자문이 아닙니다.', '함께 읽기', '홈'],
 'en': ['Guides', 'About', 'Contact', 'Privacy Policy', 'Open calculator', 'All guides', 'EasyCalc editors', 'This article is general information, not tax or legal advice.', 'Related', 'Home'],
 'vi': ['Hướng dẫn', 'Giới thiệu', 'Liên hệ', 'Chính sách quyền riêng tư', 'Mở máy tính', 'Tất cả hướng dẫn', '', '', '', 'Trang chủ'],
 'zh': ['指南', '关于', '联系', '隐私政策', '打开计算器', '全部指南', '', '', '', '首页'],
 'ne': ['गाइड', 'हाम्रोबारे', 'सम्पर्क', 'गोपनीयता नीति', 'क्याल्कुलेटर खोल्नुहोस्', 'सबै गाइड', '', '', '', 'गृहपृष्ठ'],
 'id': ['Panduan', 'Tentang', 'Kontak', 'Kebijakan Privasi', 'Buka kalkulator', 'Semua panduan', '', '', '', 'Beranda'],
 'km': ['មគ្គុទ្ទេសក៍', 'អំពីយើង', 'ទំនាក់ទំនង', 'គោលការណ៍ឯកជនភាព', 'បើកម៉ាស៊ីនគិតលេខ', 'មគ្គុទ្ទេសក៍ទាំងអស់', '', '', '', 'ទំព័រដើម'],
 'uz': ['Qoʻllanmalar', 'Biz haqimizda', 'Aloqa', 'Maxfiylik siyosati', 'Kalkulyatorni ochish', 'Barcha qoʻllanmalar', '', '', '', 'Bosh sahifa'],
 'th': ['คู่มือ', 'เกี่ยวกับเรา', 'ติดต่อ', 'นโยบายความเป็นส่วนตัว', 'เปิดเครื่องคิดเลข', 'คู่มือทั้งหมด', '', '', '', 'หน้าแรก'],
 'my': ['လမ်းညွှန်', 'ကျွန်ုပ်တို့အကြောင်း', 'ဆက်သွယ်ရန်', 'ကိုယ်ရေးအချက်အလက်မူဝါဒ', 'တွက်စက်ဖွင့်ရန်', 'လမ်းညွှန်အားလုံး', '', '', '', 'ပင်မစာမျက်နှာ'],
}
GUIDES, ABOUT, CONTACT, PRIVACY, OPEN, ALLG, BYLINE, DISCLAIM, RELATED, HOME = range(10)
# 홈 화면 추가(PWA) 문구: [버튼, 아이폰 안내]
PWA = {
 'ko': ['홈 화면에 앱 추가', '아이폰: 공유 버튼 → ‘홈 화면에 추가’를 누르면 앱처럼 쓸 수 있어요.'],
 'en': ['Add to home screen', 'On iPhone, tap Share, then “Add to Home Screen” to use it like an app.'],
 'vi': ['Thêm vào màn hình chính', 'Trên iPhone, chạm Chia sẻ rồi chọn “Thêm vào MH chính” để dùng như ứng dụng.'],
 'zh': ['添加到主屏幕', '在 iPhone 上，点按“分享”，再选择“添加到主屏幕”，即可像应用一样使用。'],
 'ne': ['होम स्क्रिनमा थप्नुहोस्', 'iPhone मा Share थिच्नुहोस्, अनि “Add to Home Screen” छान्नुहोस्। यो एप जस्तै चल्छ।'],
 'id': ['Tambahkan ke layar utama', 'Di iPhone, ketuk Bagikan lalu pilih “Tambah ke Layar Utama” agar bisa dipakai seperti aplikasi.'],
 'km': ['បន្ថែមទៅអេក្រង់ដើម', 'នៅលើ iPhone ចុច Share រួចជ្រើស “Add to Home Screen” ដើម្បីប្រើដូចកម្មវិធី។'],
 'uz': ['Bosh ekranga qoʻshish', 'iPhone’da Share tugmasini bosing, soʻng “Add to Home Screen”ni tanlang — ilova kabi ishlaydi.'],
 'th': ['เพิ่มไปยังหน้าจอโฮม', 'บน iPhone แตะปุ่มแชร์ แล้วเลือก “เพิ่มไปยังหน้าจอโฮม” เพื่อใช้งานเหมือนแอป'],
 'my': ['ပင်မမျက်နှာပြင်သို့ ထည့်ရန်', 'iPhone တွင် Share ကိုနှိပ်ပြီး “Add to Home Screen” ကိုရွေးပါ။ အက်ပ်ကဲ့သို့ သုံးနိုင်ပါသည်။'],
}
THEME = '#0E6A55'

CONTENT_LANGS = ['ko', 'en']  # 가이드·소개 등이 있는 언어


def ch(l, i):
    v = CH[l][i]
    return v or CH['en'][i]


def base(l):
    return '/' if l == 'ko' else f'/{l}/'


def clang(l):
    """소개·가이드 등이 없는 언어는 영어판으로 연결"""
    return l if l in CONTENT_LANGS else 'en'


def esc(s):
    return H.escape(s, quote=True)


# ---------- 번역 읽기 / load translations ----------
calc = open(os.path.join(SRC, 'calc.html'), encoding='utf-8').read()
cache = os.path.join(SRC, 'i18n-cache.json')
try:
    js = re.search(r'<script>\s*/\*[^*]*번역[^*]*\*/\s*(.*?)</script>', calc, re.S).group(1)
    node = ("const window={};" + js + ";process.stdout.write(JSON.stringify({I18N:window.I18N,FONT:window.I18N_FONT},"
            "(k,v)=>typeof v==='function'?undefined:v))")
    data = json.loads(subprocess.run(['node', '-e', node], capture_output=True, text=True, check=True).stdout)
    json.dump(data, open(cache, 'w', encoding='utf-8'), ensure_ascii=False)
except Exception as e:  # node가 없으면 마지막 캐시 사용
    print('node 실행 실패, 캐시 사용:', e, file=sys.stderr)
    data = json.load(open(cache, encoding='utf-8'))
I18N, FONT = data['I18N'], data['FONT']

style_css = re.search(r'<style>(.*?)</style>', calc, re.S).group(1)
head_links = calc[:calc.index('<style>')]
head_links = re.sub(r'<title>.*?</title>\n?', '', head_links)
head_links = re.sub(r'<meta name="(description|claude:viewport-fit-sides)"[^>]*>\n?', '', head_links)
calc_body = calc[calc.index('</style>') + len('</style>'):].lstrip()

EXTRA_CSS = r"""
.pwa{margin:0 0 10px}
.pwa-btn{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--accent);background:var(--accent-soft);color:var(--ink);border-radius:999px;padding:7px 14px;font:inherit;font-size:13px;font-weight:600;cursor:pointer}
.pwa-btn:hover{background:var(--accent);color:var(--accent-ink)}
.pwa-ios{margin:0;font-size:12px;color:var(--muted)}
.wrap.wide{max-width:720px}
.sitenav{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:14px}
.sitenav a{color:var(--muted);text-decoration:none;padding:2px 0}
.sitenav a:hover,.sitenav a[aria-current="page"]{color:var(--ink)}
.sitenav a[aria-current="page"]{font-weight:700}
footer .footlinks{display:flex;justify-content:center;flex-wrap:wrap;gap:6px 16px;margin-bottom:8px}
footer .footlinks a{color:var(--muted)}
main.page{display:flex;flex-direction:column;gap:18px}
.crumb{font-size:13px;color:var(--muted)}.crumb a{color:var(--muted)}
.page h1{font:700 28px/1.3 var(--f-body);margin:0;text-wrap:balance;letter-spacing:-.3px}
.byline{font-size:13px;color:var(--muted)}
.prose{display:flex;flex-direction:column;gap:14px;font-size:16px;line-height:1.75}
.prose > *{margin:0}
.prose p,.prose ul{max-width:68ch}
.prose ul{padding-left:1.2em;display:flex;flex-direction:column;gap:6px}
.prose h2{font:700 20px/1.4 var(--f-body);margin-top:14px;letter-spacing:-.2px}
.prose h3{font:700 16.5px/1.4 var(--f-body);margin-top:4px}
.prose .lede{font-size:17px}
.prose a{color:var(--accent)}
.prose a.btn{color:var(--accent-ink)}
.prose table{min-width:0;font-size:14.5px}
.prose th,.prose td{text-align:left;white-space:normal;font-family:var(--f-body);vertical-align:top}
.prose td+td{font-variant-numeric:tabular-nums}
.prose tr.strong td{font-weight:700;color:var(--ink)}
.small{font-size:13px!important;color:var(--muted)}
.cta{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;border:1px solid var(--accent);background:var(--accent-soft);border-radius:var(--r);padding:16px 18px;margin-top:8px}
.cta b{display:block;font-size:16px}.cta span{color:var(--muted);font-size:14px}
.cta .btn,.card .btn{text-decoration:none;display:inline-block}
.callout{border:1px solid var(--line);background:var(--surface);border-radius:var(--r);padding:16px 18px;display:flex;flex-direction:column;gap:4px}
.callout .mail{font:600 20px var(--f-num);overflow-wrap:anywhere}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:18px;display:flex;flex-direction:column;gap:8px;min-width:0}
.card h3{margin:0;font:700 17px/1.4 var(--f-body)}
.card p{margin:0;color:var(--muted);font-size:14px;flex:1}
.glist{display:flex;flex-direction:column;gap:0;border:1px solid var(--line);border-radius:var(--r);background:var(--surface)}
.glist a{display:flex;flex-direction:column;gap:2px;padding:14px 18px;text-decoration:none;color:var(--ink);border-bottom:1px solid var(--line)}
.glist a:last-child{border-bottom:0}
.glist a:hover b{color:var(--accent)}
.glist b{font-size:15.5px}.glist span{font-size:13.5px;color:var(--muted)}
.sec-h{font:700 18px var(--f-body);margin:6px 0 0}
"""


def html_attrs(l, page=None):
    a = f' lang="{l}"'
    if l not in ('ko', 'en'):
        a += ' data-lx=""'
    f = FONT.get(l)
    if f:
        a += f' style="--f-lang:&quot;{f[0]}&quot;"'
    if page:
        a += f' data-page="{page}"'
    return a


def alt_links(alts):
    s = ''.join(f'<link rel="alternate" hreflang="{HREFLANG.get(l, l)}" href="{SITE}{u}">\n' for l, u in alts.items())
    if 'ko' in alts:
        s += f'<link rel="alternate" hreflang="x-default" href="{SITE}{alts["ko"]}">\n'
    return s


def head(l, title, desc, path, alts, extra=''):
    f = FONT.get(l)
    fl = f'<link id="font-{l}" rel="stylesheet" href="https://fonts.googleapis.com/css2?family={f[1]}&display=swap">\n' if f else ''
    return f'''<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{path}">
{alt_links(alts)}<meta property="og:type" content="{'article' if extra else 'website'}">
<meta property="og:site_name" content="EasyCalc">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:locale" content="{OGLOC[l]}">
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
<link rel="manifest" href="{base(l)}manifest.webmanifest">
<meta name="theme-color" content="{THEME}">
<link rel="icon" type="image/png" sizes="32x32" href="/icons/favicon-32.png">
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="EasyCalc">
{fl}{head_links}{extra}'''


def nav(l, current=None, tools=True):
    items = []
    if tools:
        items += [(base(l) + t + '/', I18N[l][TOOL_TAB[t]], t) for t in TOOLS]
    c = clang(l)
    items += [(base(c) + 'guide/', ch(l, GUIDES), 'guide'), (base(c) + 'about/', ch(l, ABOUT), 'about')]
    cur = ' aria-current="page"'
    return '<nav class="sitenav">' + ''.join(
        f'<a href="{u}"{cur if k == current else ""}>{esc(t)}</a>' for u, t, k in items) + '</nav>'


def footer(l, with_data_t=False):
    c = clang(l)
    links = f'<nav class="footlinks"><a href="{base(c)}about/">{esc(ch(l, ABOUT))}</a><a href="{base(c)}contact/">{esc(ch(l, CONTACT))}</a><a href="{base(c)}privacy/">{esc(ch(l, PRIVACY))}</a></nav>'
    txt = f'<div data-t="footer"></div>' if with_data_t else f'<div>{esc(I18N[l]["footer"])}</div>'
    return f'<footer>{links}{pwa_ui(l)}{txt}<div style="margin-top:4px">© 2026 EasyCalc</div></footer>'


def pwa_ui(l):
    btn, ios = PWA[l]
    pre = json.dumps([base(l)] + [base(l) + t + '/' for t in TOOLS])
    return f'''<div class="pwa"><button type="button" id="pwa-install" class="pwa-btn" hidden>
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></svg>{esc(btn)}</button>
<p id="pwa-ios" class="pwa-ios" hidden>{esc(ios)}</p></div>
<script>(function(){{
var ok=/(^|\\.)easycalc\\.co\\.kr$|^localhost$|^127\\./.test(location.hostname);
if(ok&&'serviceWorker' in navigator){{addEventListener('load',function(){{navigator.serviceWorker.register('/sw.js').then(function(){{return navigator.serviceWorker.ready}}).then(function(r){{r.active&&r.active.postMessage({{precache:{pre}}})}}).catch(function(){{}})}})}}
if(matchMedia('(display-mode: standalone)').matches||navigator.standalone)return;
var b=document.getElementById('pwa-install'),ev=null;
addEventListener('beforeinstallprompt',function(e){{e.preventDefault();ev=e;b.hidden=false}});
b.onclick=function(){{if(!ev)return;ev.prompt();ev.userChoice.then(function(){{ev=null;b.hidden=true}})}};
addEventListener('appinstalled',function(){{b.hidden=true}});
if(/iphone|ipad|ipod/i.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1))document.getElementById('pwa-ios').hidden=false;
}})()</script>'''


def lang_select(l, targets):
    opts = ''.join(f'<option value="{targets[x]}" lang="{x}"{" selected" if x == l else ""}>{esc(I18N[x]["langName"])}</option>' for x in LANGS)
    return f'''<label class="langsel">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/></svg>
      <select aria-label="Language / 언어" onchange="location.href=this.value">{opts}</select>
    </label>'''


def page_shell(l, title, desc, path, alts, targets, main_html, current=None, extra_head=''):
    return f'''<!doctype html>
<html{html_attrs(l)}>
<head>
{head(l, title, desc, path, alts, extra_head)}<style>{style_css}{EXTRA_CSS}</style>
</head>
<body>
<div class="wrap wide">
  <header>
    <div class="brandbox"><a class="brand" href="{base(l)}">Easy<b>Calc</b></a><div class="tag">{esc(I18N[l]["tag"])}</div></div>
    {lang_select(l, targets)}
  </header>
  {nav(l, current)}
  <main class="page">
{main_html}
  </main>
  {footer(l)}
</div>
</body>
</html>
'''


def write(path, content):
    p = os.path.join(OUT, path.lstrip('/'), 'index.html') if path.endswith('/') else os.path.join(OUT, path.lstrip('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(content)


SITEMAP = []  # (path, alts)


# ---------- 콘텐츠 읽기 / load guides & pages ----------
def load_dir(kind, l):
    d = os.path.join(SRC, kind, l)
    out = []
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not fn.endswith('.html'):
            continue
        raw = open(os.path.join(d, fn), encoding='utf-8').read()
        m = re.match(r'\s*<!--(\{.*?\})-->\s*', raw, re.S)
        meta = json.loads(m.group(1))
        meta['slug'] = fn[:-5]
        meta['body'] = raw[m.end():]
        out.append(meta)
    return sorted(out, key=lambda g: g.get('order', 99))


GUIDE = {l: load_dir('guides', l) for l in CONTENT_LANGS}
PAGES = {l: {p['slug']: p for p in load_dir('pages', l)} for l in CONTENT_LANGS}


def cta(l, tool):
    t = I18N[l]
    return (f'<div class="cta"><div><b>{esc(t[TOOL_H[tool]])}</b><span>{esc(t["tag"])}</span></div>'
            f'<a class="btn" href="{base(l)}{tool}/">{esc(ch(l, OPEN))}</a></div>')


def glist(l, guides):
    return '<div class="glist">' + ''.join(
        f'<a href="{base(l)}guide/{g["slug"]}/"><b>{esc(g["title"])}</b><span>{esc(g["desc"])}</span></a>' for g in guides) + '</div>'


# ---------- 1. 계산기 페이지 / calculator pages ----------
for l in LANGS:
    t = I18N[l]
    for tool in TOOLS:
        path = base(l) + tool + '/'
        alts = {x: base(x) + tool + '/' for x in LANGS}
        body = calc_body.replace('<div class="brand">Easy<b>Calc</b></div>', f'<a class="brand" href="{base(l)}">Easy<b>Calc</b></a>')
        body = body.replace('</header>', '</header>\n  ' + nav(l, tools=False), 1)
        body = body.replace('<footer data-t="footer"></footer>', footer(l, True))
        title = t['titles'][tool]
        page = f'''<!doctype html>
<html{html_attrs(l, tool)}>
<head>
{head(l, title, t[TOOL_LEDE[tool]], path, alts)}<style>{style_css}{EXTRA_CSS}</style>
</head>
<body>
{body}
</body>
</html>
'''
        write(path, page)
        SITEMAP.append((path, alts))

# ---------- 2. 언어별 홈 / hub per language ----------
for l in LANGS:
    t = I18N[l]
    cards = ''.join(f'''<div class="card"><h3>{esc(t[TOOL_H[x]])}</h3><p>{esc(t[TOOL_LEDE[x]])}</p><div><a class="btn" href="{base(l)}{x}/">{esc(ch(l, OPEN))}</a></div></div>''' for x in TOOLS)
    c = clang(l)
    gs = GUIDE[c]
    gsec = f'<h2 class="sec-h">{esc(ch(l, GUIDES))}</h2>{glist(c, gs)}' if gs else ''
    main = f'''<h1>{esc(t["metaTitle"].split(" | ")[0])}</h1>
<div class="cards">{cards}</div>
{gsec}'''
    alts = {x: base(x) for x in LANGS}
    write(base(l), page_shell(l, t['metaTitle'], t['metaDesc'], base(l), alts, alts, main))
    SITEMAP.append((base(l), alts))

# ---------- 3. 가이드 / guides ----------
for l in CONTENT_LANGS:
    gs = GUIDE[l]
    targets = {x: (base(x) + 'guide/' if x in CONTENT_LANGS else base(x)) for x in LANGS}
    alts = {x: base(x) + 'guide/' for x in CONTENT_LANGS}
    main = f'<div class="crumb"><a href="{base(l)}">{esc(ch(l, HOME))}</a> › {esc(ch(l, GUIDES))}</div><h1>{esc(ch(l, ALLG))}</h1>{glist(l, gs)}'
    write(base(l) + 'guide/', page_shell(l, f'{ch(l, ALLG)} | EasyCalc', I18N[l]['metaDesc'], base(l) + 'guide/', alts, targets, main, 'guide'))
    SITEMAP.append((base(l) + 'guide/', alts))
    for g in gs:
        path = f'{base(l)}guide/{g["slug"]}/'
        body = re.sub(r'\{\{tool:(\w+)\}\}', lambda m: cta(l, m.group(1)), g['body'])
        rel = [x for x in gs if x['slug'] != g['slug'] and x.get('tool') == g.get('tool')][:3] or [x for x in gs if x['slug'] != g['slug']][:3]
        relsec = f'<h2 class="sec-h">{esc(ch(l, RELATED))}</h2>{glist(l, rel)}' if rel else ''
        ld = json.dumps({'@context': 'https://schema.org', '@type': 'Article', 'headline': g['title'], 'description': g['desc'],
                         'datePublished': g['date'], 'dateModified': g.get('updated', g['date']), 'inLanguage': l,
                         'author': {'@type': 'Organization', 'name': 'EasyCalc'}, 'publisher': {'@type': 'Organization', 'name': 'EasyCalc'},
                         'mainEntityOfPage': SITE + path}, ensure_ascii=False)
        main = f'''<div class="crumb"><a href="{base(l)}">{esc(ch(l, HOME))}</a> › <a href="{base(l)}guide/">{esc(ch(l, GUIDES))}</a></div>
<article class="prose">
<h1>{esc(g["title"])}</h1>
<div class="byline">{esc(ch(l, BYLINE))} · <time datetime="{g.get("updated", g["date"])}">{g.get("updated", g["date"])}</time></div>
{body}
<p class="small">{esc(ch(l, DISCLAIM))}</p>
</article>
{relsec}'''
        targets = {x: (base(x) if x != l else path) for x in LANGS}
        write(path, page_shell(l, f'{g["title"]} | EasyCalc', g['desc'], path, {l: path}, targets, main, 'guide',
                               f'<script type="application/ld+json">{ld}</script>\n'))
        SITEMAP.append((path, {l: path}))

# ---------- 4. 소개·문의·개인정보 / static pages ----------
for slug in ['about', 'contact', 'privacy']:
    alts = {x: base(x) + slug + '/' for x in CONTENT_LANGS if slug in PAGES[x]}
    for l in alts:
        p = PAGES[l][slug]
        path = alts[l]
        targets = {x: alts.get(x, base(x)) for x in LANGS}
        main = f'<article class="prose"><h1>{esc(p["title"])}</h1>\n{p["body"]}</article>'
        write(path, page_shell(l, f'{p["title"]} | EasyCalc', p['desc'], path, alts, targets, main, slug if slug == 'about' else None))
        SITEMAP.append((path, alts))

# ---------- 5. 사이트맵 / sitemap ----------
x = ['<?xml version="1.0" encoding="UTF-8"?>',
     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for path, alts in SITEMAP:
    x.append(f'  <url><loc>{SITE}{path}</loc><lastmod>{TODAY}</lastmod>')
    if len(alts) > 1:
        x += [f'    <xhtml:link rel="alternate" hreflang="{HREFLANG.get(k, k)}" href="{SITE}{u}"/>' for k, u in alts.items()]
    x.append('  </url>')
x.append('</urlset>')
open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write('\n'.join(x) + '\n')
# ---------- 6. 홈 화면 앱(PWA) / manifest, service worker, icons ----------
import shutil
ST = os.path.join(SRC, 'static')
os.makedirs(os.path.join(OUT, 'icons'), exist_ok=True)
for fn in os.listdir(os.path.join(ST, 'icons')):
    shutil.copyfile(os.path.join(ST, 'icons', fn), os.path.join(OUT, 'icons', fn))
for l in LANGS:
    t = I18N[l]
    m = {
        'id': base(l), 'name': 'EasyCalc', 'short_name': 'EasyCalc', 'description': t['metaDesc'],
        'lang': HREFLANG.get(l, l), 'dir': 'ltr', 'start_url': base(l), 'scope': '/',
        'display': 'standalone', 'background_color': '#F2F5F3', 'theme_color': THEME,
        'icons': [
            {'src': '/icons/icon-192.png', 'sizes': '192x192', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/icons/icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any'},
            {'src': '/icons/maskable-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'maskable'},
        ],
        'shortcuts': [{'name': t[TOOL_TAB[x]], 'url': base(l) + x + '/',
                       'icons': [{'src': '/icons/icon-192.png', 'sizes': '192x192'}]} for x in TOOLS],
        'categories': ['finance', 'utilities'],
    }
    write(base(l) + 'manifest.webmanifest', json.dumps(m, ensure_ascii=False, indent=1))
pre = ['/'] + ['/' + x + '/' for x in TOOLS] + ['/icons/icon-192.png', '/icons/favicon-32.png']
sw = open(os.path.join(ST, 'sw.js'), encoding='utf-8').read()
sw = sw.replace("'__VERSION__'", json.dumps(TODAY + '-' + __import__('hashlib').md5(open(os.path.join(SRC, 'calc.html'), 'rb').read()).hexdigest()[:8])).replace('__PRECACHE__', json.dumps(pre))
open(os.path.join(OUT, 'sw.js'), 'w', encoding='utf-8').write(sw)

print(f'{len(SITEMAP)} pages built into {OUT}')
