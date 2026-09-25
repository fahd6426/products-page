import os, json, time, html, requests
from playwright.sync_api import sync_playwright

p = json.loads(os.environ['PAYLOAD'])
UA = {'User-Agent': 'RzdinhoBot/1.0 (lineup cards)'}
API = 'https://en.wikipedia.org/w/api.php'

def thumb_by_title(title):
    try:
        r = requests.get(API, params={'action': 'query', 'titles': title, 'prop': 'pageimages|pageprops', 'piprop': 'thumbnail', 'pithumbsize': 500, 'redirects': 1, 'format': 'json', 'formatversion': 2}, headers=UA, timeout=10).json()
        pg = ((r.get('query') or {}).get('pages') or [{}])[0]
        if 'disambiguation' in (pg.get('pageprops') or {}):
            return None
        t = pg.get('thumbnail')
        return t['source'] if t else None
    except Exception as e:
        print('ERR', e)
        return None

def find_img(name, team):
    for t in (name, name + ' (footballer)', name + ' (footballer, born)'):
        s = thumb_by_title(t)
        if s:
            return s
        time.sleep(0.3)
    for q in (name + ' ' + team + ' national team footballer', name + ' footballer'):
        try:
            r = requests.get(API, params={'action': 'query', 'generator': 'search', 'gsrsearch': q, 'gsrlimit': 1, 'prop': 'pageimages', 'piprop': 'thumbnail', 'pithumbsize': 500, 'format': 'json', 'formatversion': 2}, headers=UA, timeout=10).json()
            pages = (r.get('query') or {}).get('pages') or []
            if pages and pages[0].get('thumbnail'):
                return pages[0]['thumbnail']['source']
        except Exception as e:
            print('ERR', e)
        time.sleep(0.4)
    return None

rows = p['rows']
for row in rows:
    for pl in row:
        pl['img'] = find_img(pl['en'], p['team_en'])
        print(pl['en'], pl['img'])
        time.sleep(0.3)

def card(pl):
    if pl.get('img'):
        ph = '<img src="' + html.escape(pl['img']) + '">'
    else:
        ph = '<div class="num">' + str(pl.get('num', '')) + '</div>'
    return ('<div class="pl"><div class="ph">' + ph + '<span class="no">' + str(pl.get('num', '')) + '</span></div>'
            '<div class="nm">' + html.escape(pl['ar']) + '</div></div>')

rows_html = ''.join('<div class="row">' + ''.join(card(pl) for pl in row) + '</div>' for row in rows)
c1 = p.get('color', '#0b3d91')
css = ('*{box-sizing:border-box}'
  'body{margin:0;width:1080px;height:1350px;font-family:Cairo,sans-serif;color:#fff;overflow:hidden;background:radial-gradient(circle at 50% -10%,' + c1 + ' 0%,#0a1433 55%,#040816 100%)}'
  '.head{text-align:center;padding:30px 0 0}'
  '.pill{display:inline-block;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.25);padding:4px 22px;border-radius:40px;font-size:24px;font-weight:700;letter-spacing:1px}'
  '.t{font-size:66px;font-weight:900;line-height:1.15;margin-top:8px;text-shadow:0 4px 18px rgba(0,0,0,.5)}'
  '.s{font-size:30px;opacity:.85;margin-top:2px}'
  '.pitch{position:relative;margin:22px 40px 0;height:1010px;border-radius:28px;overflow:hidden;background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.02));border:2px solid rgba(255,255,255,.18);display:flex;flex-direction:column;justify-content:space-around;padding:20px 0}'
  '.ln{position:absolute;border:2px solid rgba(255,255,255,.10)}'
  '.mid{left:0;right:0;top:50%;border-width:2px 0 0 0}'
  '.cc{width:220px;height:220px;border-radius:50%;left:50%;top:50%;transform:translate(-50%,-50%)}'
  '.bx1{width:440px;height:150px;left:50%;top:-2px;transform:translateX(-50%)}'
  '.bx2{width:440px;height:150px;left:50%;bottom:-2px;transform:translateX(-50%)}'
  '.row{position:relative;display:flex;justify-content:space-evenly;direction:ltr;z-index:2}'
  '.pl{display:flex;flex-direction:column;align-items:center;width:190px}'
  '.ph{position:relative;width:132px;height:132px;border-radius:50%;background:linear-gradient(160deg,#ffffff,#dfe6f3);border:4px solid #fff;box-shadow:0 10px 24px rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center}'
  '.ph img{width:100%;height:100%;border-radius:50%;object-fit:cover;object-position:center 15%}'
  '.no{position:absolute;right:-6px;bottom:-4px;width:44px;height:44px;border-radius:50%;background:#f5c518;color:#0a1433;font-weight:900;font-size:22px;display:flex;align-items:center;justify-content:center;border:3px solid #0a1433}'
  '.num{font-size:58px;font-weight:900;color:#0a1433}'
  '.nm{margin-top:12px;background:#fff;color:#0a1433;font-weight:900;font-size:24px;padding:4px 16px;border-radius:8px;white-space:nowrap;direction:rtl;box-shadow:0 6px 14px rgba(0,0,0,.35)}'
  '.foot{position:absolute;bottom:0;left:0;right:0;height:62px;display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:700;background:rgba(0,0,0,.35);letter-spacing:.5px}')
sub_html = html.escape(p['sub']) + ' • <span dir="ltr">' + html.escape(p['formation']) + '</span>'
page = ('<html dir="rtl"><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet"><style>' + css + '</style></head><body>'
  '<div class="head"><div class="pill">التشكيلة الرسمية</div><div class="t">' + html.escape(p['title']) + '</div><div class="s">' + sub_html + '</div></div>'
  '<div class="pitch"><div class="ln mid"></div><div class="ln cc"></div><div class="ln bx1"></div><div class="ln bx2"></div>' + rows_html + '</div>'
  '<div class="foot">' + html.escape(p['brand']) + '</div></body></html>')
with open('card.html', 'w', encoding='utf-8') as f:
    f.write(page)
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={'width': 1080, 'height': 1350})
    pg.goto('file://' + os.path.abspath('card.html'))
    pg.wait_for_load_state('networkidle')
    pg.wait_for_timeout(2500)
    pg.screenshot(path='lineup.png')
    b.close()
