"""Wrap the timeline's HTML (a Claude Doc export, links already rewritten) in a readable page.

Used by build_index.py, and runnable on its own to restyle an existing index.html:

    python3 tools/page.py index.html index.html

Re-running it is safe: it takes only the content between the CONTENT markers when they are present.
"""
import html, re, sys

PDF = 'geert-greydanus-timeline.pdf'
START, END = '<!-- CONTENT START -->', '<!-- CONTENT END -->'
SI_START, SI_END = '<!-- SOURCE INDEX START -->', '<!-- SOURCE INDEX END -->'

# The war years at a glance, from the section headings. The doc draws this as a chart that does not export.
GLANCE = [
    ('In hiding', 'Apr 1943 – Apr 1944', 12, 'hiding', 'april-1943-april-1944-in-hiding-oom-geert-in-the-achterhoek'),
    ('Arrest, Vught', 'Apr – Aug 1944', 4, 'vught', 'april-august-1944-arrest-the-vught-bunker-transport'),
    ('Buchenwald, Niederorschel', 'Aug 1944 – May 1945', 9, 'camp', 'august-1944-may-1945-buchenwald-niederorschel-and-liberation'),
    ('Back in Rotterdam', 'May 1945 – Sep 1947', 28, 'home', 'may-1945-september-1947-back-in-rotterdam'),
]


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
    total = sum(g[2] for g in GLANCE)
    bars = ''.join(
        '<a class="glance-seg glance-%s" href="#%s" style="flex:%d"><span class="glance-label">%s</span>'
        '<span class="glance-dates">%s</span></a>' % (cls, anchor, months, label, dates)
        for label, dates, months, cls, anchor in GLANCE)
    return ('<figure class="glance"><figcaption>Geert’s war years at a glance, April 1943 – September 1947'
            '</figcaption><div class="glance-bar">%s</div><p class="glance-note">Widths are to scale: '
            'the arrest on 20 April 1944 ends a year in hiding; the camps take most of the next year.</p></figure>' % bars)


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
    body = body.strip()
    toc_html = toc(body + '<h2 id="archive-sources">Source index</h2>')
    rev_note = ' (revision %s)' % html.escape(str(rev)) if rev and rev != '?' else ''
    return TEMPLATE.format(toc=toc_html, body=body, source_index=source_index, pdf=PDF, rev=rev_note,
                           start=START, end=END, si_start=SI_START, si_end=SI_END, css=CSS)


CSS = r"""
:root{--paper:#faf7f0;--card:#fffdf8;--ink:#2a2622;--muted:#6b635a;--rule:#e4ddcf;--accent:#8a3324;--accent-soft:#f3e6df;
--hiding:#b5873a;--vught:#8a3324;--camp:#4a3f3a;--home:#5b7a6a;--serif:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
@media (prefers-color-scheme:dark){:root{--paper:#1b1917;--card:#24211e;--ink:#ebe5da;--muted:#a69d91;--rule:#3a3530;--accent:#e08a6d;
--accent-soft:#3a2a24;--hiding:#c99a4b;--vught:#b8523f;--camp:#7a6c64;--home:#6f9584}}
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
.glance{margin:32px 0;padding:20px;background:var(--card);border:1px solid var(--rule);border-radius:8px}
.glance figcaption{font:600 15px var(--sans);margin-bottom:12px}
.glance-bar{display:flex;gap:3px;min-height:72px}
.glance-seg{display:flex;flex-direction:column;justify-content:flex-end;padding:8px 10px;color:#fff;text-decoration:none;border-radius:4px;min-width:0;font-family:var(--sans)}
.glance-seg:hover{filter:brightness(1.1)}
.glance-label{font-weight:700;font-size:14px;line-height:1.2}
.glance-dates{font-size:12px;opacity:.9}
.glance-hiding{background:var(--hiding)}.glance-vught{background:var(--vught)}.glance-camp{background:var(--camp)}.glance-home{background:var(--home)}
.glance-note{font:13px/1.4 var(--sans);color:var(--muted);margin:10px 0 0}
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
 .glance-bar{flex-direction:column;min-height:0}
 .glance-seg{flex:none!important;padding:10px 12px;flex-direction:row;justify-content:space-between;gap:8px}
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
