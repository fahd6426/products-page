import os, json, time, html, requests
from playwright.sync_api import sync_playwright

p = json.loads(os.environ['PAYLOAD'])
UA = {'User-Agent': 'RzdinhoBot/1.0 (lineup cards)'}

def find_img(name, team):
    for q in (name + ' ' + team + ' footballer', name + ' footballer'):
        try:
            r = requests.get('https://en.wikipedia.org/w/api.php', params={'action': 'query', 'generator': 'search', 'gsrsearch': q, 'gsrlimit': 1, 'prop': 'pageimages', 'piprop': 'thumbnail', 'pithumbsize': 400, 'format': 'json', 'formatversion': 2}, headers=UA, timeout=10).json()
            pages = (r.get('query') or {}).get('pages') or []
            if pages and pages[0].get('thumbnail'):
                return pages[0]['thumbnail']['source']
        except Exception as e:
            print('ERR', e)
        time.sleep(0.5)
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
    return '<div class="pl"><div class="ph">' + ph + '</div><div class="nm">' + html.escape(pl['ar']) + '</div></div>'

rows_html = ''.join('<div class="row">' + ''.join(card(pl) for pl in row) + '</div>' for row in rows)
css = ('body{margin:0;width:1080px;height:1350px;font-family:Cairo,sans-serif;background:linear-gradient(180deg,#0b2a6b,#1747a6 45%,#0b2a6b);color:#fff}'
  '.head{text-align:center;padding:34px 0 6px}'
  '.t{font-size:60px;font-weight:900;line-height:1.2}'
  '.s{font-size:32px;opacity:.9}'
  '.pitch{margin:16px 44px;height:1050px;border:4px solid rgba(255,255,255,.22);border-radius:26px;display:flex;flex-direction:column;justify-content:space-around;background:repeating-linear-gradient(180deg,rgba(255,255,255,.05) 0 90px,rgba(255,255,255,0) 90px 180px)}'
  '.row{display:flex;justify-content:space-around;direction:ltr}'
  '.pl{display:flex;flex-direction:column;align-items:center;width:185px}'
  '.ph{width:135px;height:135px;border-radius:50%;overflow:hidden;background:#fff;border:5px solid #c8f542;display:flex;align-items:center;justify-content:center}'
  '.ph img{width:100%;height:100%;object-fit:cover;object-position:center top}'
  '.num{font-size:60px;font-weight:900;color:#0b2a6b}'
  '.nm{margin-top:10px;background:#c8f542;color:#0b1d3a;font-weight:900;font-size:25px;padding:3px 14px;border-radius:6px;white-space:nowrap;direction:rtl}'
  '.foot{text-align:center;font-size:28px;opacity:.85;margin-top:4px}')
sub_html = html.escape(p['sub']) + ' | <span dir="ltr">' + html.escape(p['formation']) + '</span>'
page = ('<html dir="rtl"><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet"><style>' + css + '</style></head><body>'
  '<div class="head"><div class="t">' + html.escape(p['title']) + '</div><div class="s">' + sub_html + '</div></div>'
  '<div class="pitch">' + rows_html + '</div><div class="foot">' + html.escape(p['brand']) + '</div></body></html>')
with open('card.html', 'w', encoding='utf-8') as f:
    f.write(page)
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={'width': 1080, 'height': 1350})
    pg.goto('file://' + os.path.abspath('card.html'))
    pg.wait_for_load_state('networkidle')
    pg.wait_for_timeout(2000)
    pg.screenshot(path='lineup.png')
    b.close()
