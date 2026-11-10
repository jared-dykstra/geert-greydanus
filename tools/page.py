"""Wrap the timeline's HTML (a Claude Doc export, links already rewritten) in a readable page.

Used by build_index.py, and runnable on its own to restyle an existing index.html:

    python3 tools/page.py index.html index.html

Re-running it is safe: it takes only the content between the CONTENT markers when they are present.
"""
import html, os, re, sys

PDF = 'geert-greydanus-timeline.pdf'
START, END = '<!-- CONTENT START -->', '<!-- CONTENT END -->'
SI_START, SI_END = '<!-- SOURCE INDEX START -->', '<!-- SOURCE INDEX END -->'

# The war years at a glance, as drawn in the doc's chart (which the HTML export leaves out; the PDF has it).
# Positions are months after 1 April 1943. Bars are (start, end); markers have end None.
GLANCE_SPAN = 54
GLANCE_YEARS = [(9, '1944'), (21, '1945'), (33, '1946'), (45, '1947')]
GLANCE = [
    ('In hiding, Achterhoek', 0, 12, 'Apr 1943 to Apr 1944', 'april-1943-april-1944-in-hiding-oom-geert-in-the-achterhoek'),
    ('Family held in Vught', 8.05, 8.6, '2–18 Dec 1943', None),
    ('Arrested at Satter farm', 12.65, None, '20 Apr 1944', 'april-august-1944-arrest-the-vught-bunker-transport'),
    ('Vught camp and bunker', 12.65, 16, 'Apr 1944 to Aug 1944', 'april-august-1944-arrest-the-vught-bunker-transport'),
    ('Buchenwald, Niederorschel', 16, 24, 'Aug 1944 to Apr 1945', 'august-1944-may-1945-buchenwald-niederorschel-and-liberation'),
    ('Back in Rotterdam police', 25, 53, 'May 1945 to Sep 1947', 'may-1945-september-1947-back-in-rotterdam'),
    ('Sails for Canada', 53.25, None, '8 Sep 1947', '19471967-canada'),
]


# Sections written for this page that are not (yet) in the Claude Doc. Each is inserted before the
# h2 named here, between markers, so a rebuild from a fresh export keeps it and a re-run replaces it.
EXTRA_SECTIONS = [('journey.html', '18991943-friesland-rotterdam-and-the-police'),
                  ('gerstein.html', 'the-airman-helping-network-around-varsseveld-janmay-1944')]
SECTIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sections')


def add_sections(body):
    for name, before in EXTRA_SECTIONS:
        start, end = '<!-- SECTION %s START -->' % name, '<!-- SECTION %s END -->' % name
        body = re.sub(re.escape(start) + '.*?' + re.escape(end) + r'\n?', '', body, flags=re.S)
        frag = open(os.path.join(SECTIONS_DIR, name), encoding='utf-8').read().strip()
        anchor = '<h2 id="%s">' % before
        if anchor in body:
            body = body.replace(anchor, '%s\n%s\n%s\n%s' % (start, frag, end, anchor), 1)
    return body


def content_of(doc):
    """The timeline's own HTML, without anything an earlier run of this script or build_index.py added."""
    if START in doc:
        doc = doc.split(START, 1)[1].split(END, 1)[0]
    doc = re.sub(r'^\s*<div style="border:1px solid #999.*?</div>', '', doc, count=1, flags=re.S)
    return doc.strip()


def nice_date(iso):
    y, mo, d = iso.split('-')
    months = 'January February March April May June July August September October November December'.split()
    return '%d %s %s' % (int(d), months[int(mo) - 1], y)


def glance():
    pct = lambda m: '%.2f%%' % (100.0 * m / GLANCE_SPAN)
    ticks = ''.join('<span class="g-tick" style="left:%s">%s</span>' % (pct(m), y) for m, y in GLANCE_YEARS)
    rows = []
    for label, start, end, dates, anchor in GLANCE:
        if end is None:
            mark = '<span class="g-mark%s" style="left:%s"></span>' % (' g-key' if 'Arrest' in label else '', pct(start))
            note_at = start + 1
        else:
            mark = '<span class="g-bar" style="left:%s;width:%s"></span>' % (pct(start), pct(max(end - start, 0.5)))
            note_at = end + 1
        right = note_at > GLANCE_SPAN - 12
        note = '<span class="g-note%s" style="%s:%s">%s</span>' % (
            ' g-left' if right else '', 'right' if right else 'left',
            pct(GLANCE_SPAN - start + 1.5) if right else pct(note_at - 0.4), dates)
        name = '<a href="#%s">%s</a>' % (anchor, label) if anchor else label
        rows.append('<div class="g-row%s"><div class="g-name">%s</div><div class="g-track">%s%s</div></div>'
                    % (' g-strong' if 'Arrest' in label else '', name, mark, note))
    arrest = '<span class="g-line" style="left:calc(190px + (100%% - 194px) * %.4f)"></span>' % (12.65 / GLANCE_SPAN)
    return ('<figure class="glance"><figcaption><strong>A year in hiding, a year in the camps, two years back in the police</strong>'
            '<span>Geert Greydanus, April 1943 to September 1947, to scale</span></figcaption>'
            '<div class="g-chart">%s<div class="g-row g-axis"><div class="g-name"></div><div class="g-track">%s</div></div>%s</div>'
            '</figure>' % (arrest, ticks, ''.join(rows)))


def classify_tables(body):
    def one(m):
        head = re.sub(r'<[^>]+>', '|', m.string[m.start():m.start() + 400])
        cls = 'timeline' if '|Date|' in head and '|Event|' in head else 'facts'
        return '<div class="table-wrap"><table class="%s">' % cls
    body = re.sub(r'<table(?![^>]*class=)[^>]*>(?=<thead>|<tr>)', one, body)
    return re.sub(r'</table>', '</table></div>', body)


def label_cells(body):
    """Give each cell its column name, so a table can stack into cards on a phone."""
    def table(m):
        t = m.group(0)
        heads = [re.sub(r'<[^>]+>', '', h) for h in re.findall(r'<th[^>]*>(.*?)</th>', t)]
        if not heads:
            return t
        def row(r):
            i = iter(heads)
            return re.sub(r'<td>', lambda _: '<td data-label="%s">' % html.escape(next(i, ''), quote=True), r.group(0))
        return re.sub(r'<tbody>.*?</tbody>', lambda b: re.sub(r'<tr>.*?</tr>', row, b.group(0), flags=re.S), t, flags=re.S)
    return re.sub(r'<table.*?</table>', table, body, flags=re.S)


def toc(body):
    items = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    lis = ''.join('<li><a href="#%s">%s</a></li>' % (i, re.sub(r'<[^>]+>', '', t)) for i, t in items)
    return ('<nav class="toc" aria-label="Contents"><details open><summary class="toc-title">Contents</summary>'
            '<ol>%s</ol></details></nav>' % lis)


def render(doc, rev='?'):
    if SI_START in doc:  # an earlier run of this script: keep its source index as it is
        rendered_index = doc.split(SI_START, 1)[1].split(SI_END, 1)[0]
        return _page(content_of(doc), rendered_index, rev)
    body, source_index = content_of(doc), ''
    m = re.search(r'<h2 id="archive-sources">', body)
    if m:
        body, source_index = body[:m.start()], body[m.start():]
    # The doc's byline names an internal user id; the date alone is useful.
    body = re.sub(r'<p><time[^>]*datetime="([^"]+)"[^>]*>.*?</time>.*?</p>',
                  lambda m: '<p class="updated">Last updated <time datetime="%s">%s</time></p>' % (m.group(1), nice_date(m.group(1))),
                  body, count=1, flags=re.S)
    body = re.sub(r'<h1[^>]*>.*?</h1>', '', body, count=1, flags=re.S)
    body = re.sub(r'<figure data-embed="[^"]*">.*?</figure>', glance(), body, count=1, flags=re.S)
    body = label_cells(classify_tables(body))
    if source_index:
        source_index = re.sub(r'<h2 id="archive-sources">.*?</h2>', '', source_index, count=1, flags=re.S)
        source_index = re.sub(r'<table[^>]*>', '<div class="table-wrap"><table class="facts index">', source_index, count=1)
        source_index = source_index.replace('</table>', '</table></div>', 1)
        source_index = ('<section id="archive-sources" class="archive"><h2>Source index</h2>'
                        '<details><summary>Show every link in the timeline, with its saved copy</summary>%s</details></section>'
                        % source_index)
    return _page(body, source_index, rev)


def _page(body, source_index, rev):
    body = add_sections(body.strip())
    toc_html = toc(body + '<h2 id="archive-sources">Source index</h2>')
    rev_note = ' (revision %s)' % html.escape(str(rev)) if rev and rev != '?' else ''
    return TEMPLATE.format(toc=toc_html, body=body, source_index=source_index, pdf=PDF, rev=rev_note,
                           start=START, end=END, si_start=SI_START, si_end=SI_END, css=CSS)


CSS = r"""
:root{--paper:#faf7f0;--card:#fffdf8;--ink:#2a2622;--muted:#6b635a;--rule:#e4ddcf;--accent:#8a3324;--accent-soft:#f3e6df;
--serif:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
@media (prefers-color-scheme:dark){:root{--paper:#1b1917;--card:#24211e;--ink:#ebe5da;--muted:#a69d91;--rule:#3a3530;--accent:#e08a6d;
--accent-soft:#3a2a24}}
*{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:16px}
body{margin:0;background:var(--paper);color:var(--ink);font:18px/1.6 var(--serif);-webkit-text-size-adjust:100%}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}
a:hover{text-decoration-thickness:2px}
.hero{border-bottom:1px solid var(--rule);background:var(--card)}
.hero-inner{max-width:1180px;margin:0 auto;padding:48px 24px 36px}
.kicker{font:600 13px/1.4 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
h1{font-size:clamp(34px,5vw,52px);line-height:1.1;margin:0 0 12px;font-weight:600;letter-spacing:-.01em}
.years{font-weight:400;color:var(--muted);white-space:nowrap}
.lede{font-size:20px;max-width:46em;margin:0 0 24px;color:var(--ink)}
.actions{display:flex;flex-wrap:wrap;gap:12px;font-family:var(--sans)}
.btn{display:inline-flex;align-items:center;gap:8px;padding:10px 16px;border-radius:6px;font:600 15px/1 var(--sans);text-decoration:none;border:1px solid var(--accent)}
.btn-primary{background:var(--accent);color:var(--paper)}
.btn-secondary{color:var(--accent);background:transparent}
.btn svg{width:16px;height:16px}
.layout{max-width:1180px;margin:0 auto;padding:0 24px;display:grid;grid-template-columns:240px minmax(0,1fr);gap:56px}
.toc{position:sticky;top:0;align-self:start;max-height:100vh;overflow:auto;padding:32px 0;font:14px/1.4 var(--sans)}
.toc summary{list-style:none;cursor:default}.toc summary::-webkit-details-marker{display:none}
.toc-title{font-weight:700;text-transform:uppercase;letter-spacing:.08em;font-size:12px;color:var(--muted);margin:0 0 12px}
.toc ol{list-style:none;margin:0;padding:0;border-left:2px solid var(--rule)}
.toc li a{display:block;padding:6px 0 6px 14px;margin-left:-2px;border-left:2px solid transparent;color:var(--muted);text-decoration:none}
.toc li a:hover{color:var(--ink)}
.toc li a.active{color:var(--accent);border-left-color:var(--accent);font-weight:600}
main{padding:24px 0 80px;min-width:0}
main>p,main>ul,main>ol,main section>p{max-width:42em}
.updated{font:14px var(--sans);color:var(--muted)}
h2{font-size:30px;line-height:1.2;margin:64px 0 12px;padding-top:24px;border-top:1px solid var(--rule);font-weight:600}
h3{font-size:22px;line-height:1.3;margin:40px 0 8px;font-weight:600}
main>h2:first-of-type{border-top:0;margin-top:16px}
li{margin:6px 0}
li>p{margin:0}
ol li::marker{color:var(--muted)}
.table-wrap{margin:20px 0 28px;overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:16px;line-height:1.5}
th{font:700 12px/1.3 var(--sans);text-transform:uppercase;letter-spacing:.06em;color:var(--muted);text-align:left;padding:8px 12px;border-bottom:2px solid var(--rule)}
td{padding:12px;vertical-align:top;border-bottom:1px solid var(--rule)}
table.facts td:first-child{font-weight:600}
table.timeline td:first-child{white-space:nowrap;font:600 15px/1.5 var(--sans);color:var(--accent);width:9.5em;position:relative;padding-left:22px}
table.timeline td:first-child::before{content:"";position:absolute;left:4px;top:19px;width:9px;height:9px;border-radius:50%;background:var(--accent)}
table.timeline td:first-child{white-space:normal}
table.timeline td:last-child,table.facts td:last-child{font:14px/1.5 var(--sans);color:var(--muted);width:15em}
table.timeline td:last-child a,table.facts td:last-child a{color:var(--muted)}
table.timeline td:last-child a:hover,table.facts td:last-child a:hover{color:var(--accent)}
table.facts.index td{font:13px/1.4 var(--sans);word-break:break-all;width:auto}
tbody tr:hover{background:var(--accent-soft)}
code{font-size:.85em;background:var(--accent-soft);padding:1px 5px;border-radius:3px}
em{font-style:italic}
.glance{margin:32px 0;padding:20px 24px;background:var(--card);border:1px solid var(--rule);border-radius:8px;font-family:var(--sans)}
.glance figcaption{margin-bottom:16px}.glance figcaption strong{display:block;font-size:16px}.glance figcaption span{font-size:13px;color:var(--muted)}
.g-chart{position:relative}
.g-row{display:grid;grid-template-columns:190px 1fr;align-items:center;min-height:32px;font-size:14px}
.g-name a{color:var(--ink);text-decoration:none}.g-name a:hover{color:var(--accent);text-decoration:underline}
.g-strong .g-name,.g-strong .g-note{font-weight:700}
.g-track{position:relative;height:32px;margin-right:4px}
.g-track::before{content:"";position:absolute;left:0;right:0;top:50%;border-top:1px solid var(--rule)}
.g-axis{min-height:24px;border-bottom:1px solid var(--rule);margin-bottom:4px}.g-axis .g-track::before{display:none}
.g-tick{position:absolute;bottom:4px;transform:translateX(-50%);font-size:12px;color:var(--muted)}
.g-line{position:absolute;top:24px;bottom:0;border-left:1.5px dashed var(--accent);opacity:.6;z-index:0}
.g-bar{position:absolute;top:9px;height:14px;border-radius:7px;background:var(--accent-soft);border:1px solid var(--accent);z-index:1}
.g-mark{position:absolute;top:10px;width:12px;height:12px;margin-left:-6px;transform:rotate(45deg);background:var(--muted);z-index:1}
.g-mark.g-key{background:var(--accent)}
.g-note{position:absolute;top:6px;white-space:nowrap;font-size:13px;line-height:20px;color:var(--muted);z-index:2;background:var(--card);padding:0 4px}
.chain{list-style:none;padding:0;margin:20px 0;counter-reset:step;max-width:42em}
.chain li{position:relative;padding:0 0 18px 44px;margin:0;counter-increment:step}
.chain li::before{content:counter(step);position:absolute;left:0;top:2px;width:28px;height:28px;border-radius:50%;background:var(--accent);color:var(--paper);font:700 14px/28px var(--sans);text-align:center}
.chain li::after{content:"";position:absolute;left:13.5px;top:34px;bottom:4px;border-left:1px solid var(--rule)}
.chain li:last-child::after{display:none}
.sources-note{font:14px/1.5 var(--sans);color:var(--muted)}
.archive details{margin-top:12px}
.archive summary{cursor:pointer;font:600 15px var(--sans);color:var(--accent)}
.about{margin-top:64px;padding:20px 24px;background:var(--card);border:1px solid var(--rule);border-radius:8px;font:15px/1.6 var(--sans);color:var(--muted);max-width:none}
.about h2{font:700 13px var(--sans);text-transform:uppercase;letter-spacing:.08em;margin:0 0 8px;padding:0;border:0;color:var(--muted)}
.about p{margin:6px 0}
.top{position:fixed;right:16px;bottom:16px;padding:10px 14px;border-radius:20px;background:var(--card);border:1px solid var(--rule);font:600 13px var(--sans);text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.08)}
@media (max-width:900px){
 .layout{display:block;padding:0 16px}
 .hero-inner{padding:32px 16px 24px}
 .toc{position:static;max-height:none;padding:16px 0 0}
 .toc details{border:1px solid var(--rule);border-radius:8px;background:var(--card);padding:12px 16px}
 .toc summary{cursor:pointer;margin:0}
 .toc summary::after{content:" ▾"}
 .toc details[open] ol{margin-top:12px}
 .toc ol{columns:1}
 body{font-size:17px}
 .years{font-weight:400;color:var(--muted);white-space:nowrap}
.lede{font-size:18px}
 h2{font-size:25px;margin-top:48px}
 .glance{padding:16px}
 .g-row{grid-template-columns:1fr;min-height:0;margin-bottom:6px}
 .g-axis{display:none}.g-line{display:none}
 .g-name{font-size:13px}
 .g-track{height:24px}.g-bar{top:5px}.g-mark{top:6px}.g-note{top:3px;font-size:12px}
 table,thead,tbody,tr,td{display:block;width:auto!important}
 thead{display:none}
 tbody tr{padding:14px 0;border-bottom:1px solid var(--rule)}
 td{border:0;padding:2px 0}
 table.timeline td:first-child{padding-left:0;white-space:normal}
 table.timeline td:first-child::before{display:none}
 table.facts td:not(:first-child)::before,table.timeline td:last-child::before{content:attr(data-label) ": ";font:700 11px var(--sans);text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
 table.timeline td:last-child,table.facts td:last-child{width:auto;margin-top:4px}
 tbody tr:hover{background:none}
}
@media print{.toc,.top,.actions{display:none}.layout{display:block}body{background:#fff;font-size:12pt}h2{break-after:avoid}tr{break-inside:avoid}}
"""

SCRIPT = """<script>
(function(){var links=[].slice.call(document.querySelectorAll('.toc a'));var map={};links.forEach(function(a){map[a.getAttribute('href').slice(1)]=a});
if(!('IntersectionObserver' in window))return;var cur;var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){if(cur)cur.classList.remove('active');cur=map[e.target.id];if(cur)cur.classList.add('active')}})},{rootMargin:'0px 0px -75% 0px'});
Object.keys(map).forEach(function(id){var h=document.getElementById(id);if(h)io.observe(h)});
if(window.matchMedia('(max-width:900px)').matches){var t=document.querySelector('.toc details');if(t)t.open=false}
if(location.hash==='#archive-sources'){var d=document.querySelector('#archive-sources details');if(d)d.open=true}
document.querySelector('.toc a[href="#archive-sources"]').addEventListener('click',function(){var d=document.querySelector('#archive-sources details');if(d)d.open=true});})();
</script>"""

DOWNLOAD_ICON = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">'
                 '<path d="M8 2v8m0 0L4.5 6.5M8 10l3.5-3.5M2.5 13.5h11"/></svg>')

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Geert Greydanus (1899–1965): a timeline from the family papers</title>
<meta name="description" content="Rotterdam police detective, resistance helper and camp survivor: Geert Greydanus's life from the family papers, with copies of every source.">
<style>{css}</style>
</head>
<body>
<header class="hero"><div class="hero-inner">
<p class="kicker">A timeline from the family papers</p>
<h1>Geert Greydanus <span class="years">1899–1965</span></h1>
<p class="lede">A Rotterdam police detective who went into hiding in April 1943 rather than arrest Jews, helped Allied airmen in the Achterhoek as &ldquo;Oom Geert&rdquo;, survived Vught, Buchenwald and Niederorschel, and later farmed near Clinton, Ontario.</p>
<div class="actions">
<a class="btn btn-primary" href="{pdf}" download>""" + DOWNLOAD_ICON + """Download as PDF</a>
<a class="btn btn-secondary" href="#archive-sources">Source index</a>
</div>
</div></header>
<div class="layout">
{toc}
<main>
{start}
{body}
{end}
{si_start}{source_index}{si_end}
<section class="about"><h2>About this page</h2>
<p>This is a copy of the research document <em>Geert Greydanus — Timeline from the Family Papers</em>{rev}. Wherever a source was saved, its link opens the saved copy in this archive (family papers, published articles, archive records and web pages), so the page still works if the original site changes. Links to sources that could not be saved still go to the original site.</p>
<p>The <a href="{pdf}">PDF</a> is the same document, for printing or keeping.</p>
</section>
</main>
</div>
<a class="top" href="#">↑ Top</a>
""" + SCRIPT.replace('{', '{{').replace('}', '}}') + """
</body>
</html>
"""

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    doc = open(src, encoding='utf-8').read()
    rev = re.search(r'\(rev (\d+)\)', doc) or re.search(r'\(revision (\d+)\)', doc)
    open(out, 'w', encoding='utf-8').write(render(doc, rev.group(1) if rev else '?'))
