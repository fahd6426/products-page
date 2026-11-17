#!/usr/bin/env python3
"""ربط المقالات ببعض (روابط داخلية) لموقع dlilc.com.

- يضيف تحت كل مقال قسم "مقالات ذات صلة" (4 روابط من نفس المجال).
- يضيف في الصفحة الرئيسية قسم "أحدث المقالات" (آخر 8 مقالات).

السكربت يكتب فقط بين علامات ثابتة، فيقدر يشتغل كل مرة بدون ما يكرر شي:
  <!--RELATED-START--> ... <!--RELATED-END-->   داخل كل مقال
  <!--POSTS-START--> ... <!--POSTS-END-->       داخل index.html
"""
import html
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BLOG = os.path.join(ROOT, 'blog')
RELATED_COUNT = 4
LATEST_COUNT = 8

# المجالات: كلمات تدل على كل مجال (تتطابق مع اسم المنتج وعنوان المقال)
TOPICS = [
    ('coffee', ['قهوة', 'القهوة', 'v60', 'إسبريسو', 'الإسبريسو', 'مطحنة']),
    ('car', ['سيارة', 'السيارة', 'للسيارة', 'عفريته', 'مسند ذراع']),
    ('kids', ['أطفال', 'الأطفال', 'اطفال', 'للأطفال', 'لعبة', 'ألعاب', 'مونتيسوري', 'مكعبات', 'قطار', 'رضاعة', 'تنين', 'مسدس', 'مسدسات', 'سبايدرمان']),
    ('phone', ['هاتف', 'الهاتف', 'جوال', 'الجوال', 'ايفون', 'آيفون', 'ايباد', 'آيباد', 'السماعات', 'سماعات', 'الساعات الذكية', 'بروجكتر', 'تلفزيون', 'تلفاز', 'تتبع']),
    ('light', ['إضاءة', 'مصباح', 'led', 'ليد', 'القمر']),
    ('camping', ['تخييم', 'التخييم', 'البر', 'برية']),
    ('office', ['مكتب', 'المكتب', 'الكمبيوتر', 'طابعة', 'ملصقات', 'أوراق', 'رسائل', 'ملاحظات', 'حقيبة ظهر', 'منقلة', 'مقياس']),
    ('cleaning', ['تنظيف', 'التنظيف', 'منظف', 'مكنسة', 'غسل', 'منفضة', 'بخاخ', 'مهملات', 'مصيدة', 'تجفيف']),
    ('storage', ['تخزين', 'منظم', 'رف', 'صناديق', 'صينية', 'سلة']),
    ('kitchen', ['مطبخ', 'المطبخ', 'للمطبخ', 'قطاعة', 'سكاكين', 'تقطيع', 'مقلاة', 'البيض', 'الخضروات', 'الخضار', 'فتاحة', 'مسخن', 'مشروبات', 'الأطباق', 'الصحون', 'صنبور', 'مصفاة', 'تغليف', 'ثلاجة', 'أكواب', 'إبريق', 'كوب', 'التقطيع', 'للاصابع', 'أصابع']),
    ('care', ['البشرة', 'لوشن', 'عطور', 'العطور', 'أظافر', 'الأظافر', 'أسنان', 'الأسنان', 'اسنان', 'مزيل عرق', 'الشعر', 'الاستحمام', 'قطنية', 'صابون', 'بيلاتس', 'حزام ظهر', 'الضغط', 'العناية', 'بالبشرة', 'بالأظافر']),
    ('home', ['ديكور', 'مزهريات', 'منزل', 'المنزل', 'المنزلية', 'منزلك', 'السرير', 'مروحة', 'حائط', 'وسادة', 'منقي', 'حديقة', 'ذكي']),
]


def words(text):
    return set(w for w in re.findall(r'[\w]+', text.lower()) if len(w) > 2)


def topics_of(text):
    t = ' ' + ' '.join(re.findall(r'[\w]+', text.lower())) + ' '
    found = []
    for name, keys in TOPICS:
        # نطابق كلمة كاملة (مثلاً "ليد" ما تنطبق على "اليدوية")
        if any((' ' + k.lower() + ' ') in t for k in keys):
            found.append(name)
    return found


def load_articles():
    with open(os.path.join(BLOG, 'articles.json'), encoding='utf-8') as f:
        data = json.load(f)
    items, seen = [], set()
    for a in data:  # الترتيب في الملف: الأحدث أولاً
        slug = a.get('slug', '')
        if not slug or slug in seen:
            continue
        if not os.path.exists(os.path.join(BLOG, slug + '.html')):
            continue
        seen.add(slug)
        text = (a.get('name', '') + ' ' + a.get('title', ''))
        items.append({
            'slug': slug,
            'name': a.get('name') or a.get('title') or slug,
            'img': a.get('img', ''),
            'topics': topics_of(text),
            'words': words(text),
            'deals': slug.startswith('deals-'),
        })
    return items


def pick_related(art, items, inbound):
    scored = []
    for i, o in enumerate(items):
        if o['slug'] == art['slug']:
            continue
        shared_topics = len(set(art['topics']) & set(o['topics']))
        shared_words = len(art['words'] & o['words'])
        # نفضّل نفس المجال، ثم الكلمات المشتركة، ثم الأحدث
        # صفحات العروض ما نربطها بمقالات المنتجات إلا إذا نفس المجال
        if o['deals'] != art['deals'] and shared_topics == 0:
            continue
        # نخفف التكرار: المقال اللي جاته روابط كثيرة ينزل شوي عشان كل المقالات تاخذ نصيبها
        score = shared_topics * 10 + shared_words - min(inbound.get(o['slug'], 0), 4) * 1.5
        if shared_topics == 0 and shared_words == 0:
            score = 0
        scored.append((score, -i, o))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    picked = [o for s, _, o in scored if s > 0][:RELATED_COUNT]
    for o in picked:
        inbound[o['slug']] = inbound.get(o['slug'], 0) + 1
    if len(picked) < RELATED_COUNT:  # نكمّل بأحدث المقالات
        for o in items:
            if len(picked) >= RELATED_COUNT:
                break
            if o['slug'] != art['slug'] and o not in picked and not o['deals']:
                picked.append(o)
                inbound[o['slug']] = inbound.get(o['slug'], 0) + 1
    return picked


RELATED_CSS = ('<style>.rel{margin:34px 0 8px;padding-top:22px;border-top:1px solid #e5e7eb}'
               '.rel h2{font-size:20px;font-weight:800;margin:0 0 14px}'
               '.rgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}'
               '.rcard{display:flex;flex-direction:column;background:#fff;border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;text-decoration:none;color:#1f2937}'
               '.rcard img{width:100%;height:120px;object-fit:contain;background:#fff;padding:10px;border-bottom:1px solid #e5e7eb}'
               '.rcard span{font-size:14px;font-weight:700;padding:10px 12px;line-height:1.6}'
               '.rcard:hover{border-color:#ff9900}</style>')


def related_block(related):
    cards = ''.join(
        f'<a class="rcard" href="{o["slug"]}.html">'
        f'<img src="{html.escape(o["img"], quote=True)}" alt="{html.escape(o["name"], quote=True)}" loading="lazy">'
        f'<span>{html.escape(o["name"])}</span></a>'
        for o in related)
    return (f'<!--RELATED-START-->{RELATED_CSS}<section class="rel"><h2>مقالات ذات صلة</h2>'
            f'<div class="rgrid">{cards}</div></section><!--RELATED-END-->')


def put_block(page, block, start, end, anchors):
    pat = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.S)
    if pat.search(page):
        return pat.sub(lambda m: block, page, count=1)
    for anchor, before in anchors:
        i = page.find(anchor)
        if i != -1:
            pos = i if before else i + len(anchor)
            return page[:pos] + block + page[pos:]
    return None


POSTS_CSS = ('<style>.lposts{margin-top:8px}.lgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:18px}'
             '.lcard{display:flex;flex-direction:column;background:#fff;border:1px solid #e5e7eb;border-radius:18px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.06);transition:transform .18s,box-shadow .18s}'
             '.lcard:hover{transform:translateY(-4px);box-shadow:0 12px 28px rgba(0,0,0,.12)}'
             '.lcard img{width:100%;height:170px;object-fit:contain;background:#fff;padding:14px;border-bottom:1px solid #e5e7eb}'
             '.lcard span{font-size:15px;font-weight:700;padding:14px;line-height:1.7}'
             '.lcard em{font-style:normal;color:#e88b00;font-size:13px;font-weight:700;padding:0 14px 14px}'
             '@media(max-width:600px){.lgrid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}.lcard img{height:130px}.lcard span{font-size:14px}}</style>')


def posts_block(items):
    latest = [o for o in items if not o['deals']][:LATEST_COUNT]
    cards = ''.join(
        f'<a class="lcard" href="/blog/{o["slug"]}.html">'
        f'<img src="{html.escape(o["img"], quote=True)}" alt="{html.escape(o["name"], quote=True)}" loading="lazy">'
        f'<span>{html.escape(o["name"])}</span><em>اقرأ المقال ←</em></a>'
        for o in latest)
    return (f'<!--POSTS-START-->{POSTS_CSS}<section class="lposts"><h2 class="st">📝 أحدث المقالات</h2>'
            f'<p class="ss">مراجعات وأدلة شراء لمنتجات أمازون</p><div class="lgrid">{cards}</div>'
            f'<div class="dmore"><a class="dall" href="/blog/">كل المقالات</a></div></section><!--POSTS-END-->')


def write_if_changed(path, new):
    with open(path, encoding='utf-8') as f:
        old = f.read()
    if old == new:
        return False
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new)
    return True


NOINDEX_TAG = '<!--NOINDEX--><meta name="robots" content="noindex,follow"><!--/NOINDEX-->'
NOINDEX_RE = re.compile(r'<!--NOINDEX-->.*?<!--/NOINDEX-->', re.S)


def load_noindex():
    """المقالات المخفية عن قوقل: data/noindex.json"""
    try:
        with open(os.path.join(ROOT, 'data', 'noindex.json'), encoding='utf-8') as f:
            data = json.load(f)
        return set(data.get('slugs', []) if isinstance(data, dict) else data)
    except (OSError, ValueError):
        return set()


def set_noindex(page, hidden):
    page = NOINDEX_RE.sub('', page)
    if hidden:
        m = re.search(r'<head[^>]*>', page, re.I)
        if m:
            page = page[:m.end()] + NOINDEX_TAG + page[m.end():]
    return page


def clean_sitemap(hidden):
    """نشيل المقالات المخفية من خريطة الموقع (الـ workflow يعيد بناءها كل يوم)."""
    path = os.path.join(ROOT, 'sitemap.xml')
    if not hidden or not os.path.exists(path):
        return False
    with open(path, encoding='utf-8') as f:
        xml = f.read()
    new = xml
    for slug in hidden:
        new = re.sub(r'<url>\s*<loc>[^<]*/blog/' + re.escape(slug) + r'\.html</loc>.*?</url>\s*', '', new, flags=re.S)
    return write_if_changed(path, new) if new != xml else False


def main():
    hidden = load_noindex()
    all_items = load_articles()
    # المقالات المخفية ما نوجه لها روابط، نوجه الروابط للمقالات القوية
    items = [o for o in all_items if o['slug'] not in hidden]
    changed, skipped = 0, []
    inbound = {}
    # نبدأ بالأقدم عشان المقالات الجديدة ما تغيّر روابط القديمة كثير
    for art in reversed(all_items):
        path = os.path.join(BLOG, art['slug'] + '.html')
        with open(path, encoding='utf-8') as f:
            page = f.read()
        new = put_block(page, related_block(pick_related(art, items, inbound)),
                        '<!--RELATED-START-->', '<!--RELATED-END-->',
                        [('</article>', True), ("<footer", True), ('</body>', True)])
        if new is None:
            skipped.append(art['slug'])
            continue
        new = set_noindex(new, art['slug'] in hidden)
        changed += write_if_changed(path, new)

    index = os.path.join(ROOT, 'index.html')
    with open(index, encoding='utf-8') as f:
        page = f.read()
    new = put_block(page, posts_block(items), '<!--POSTS-START-->', '<!--POSTS-END-->',
                    [('<!--DEALS-END-->', False), ('<h2 class="st">اختياراتنا لك', True)])
    home = new is not None and write_if_changed(index, new)
    smap = clean_sitemap(hidden)

    print(f'articles: {len(all_items)} | hidden: {len(hidden)} | updated: {changed} | home updated: {bool(home)} | sitemap cleaned: {bool(smap)} | skipped: {skipped}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
