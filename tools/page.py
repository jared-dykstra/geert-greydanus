"""Lay out index.html: the page shell, styles, contents list, and the sections kept in tools/sections/.

index.html is the source of truth. Edit its content directly, then run:

    python3 tools/page.py index.html index.html

The script keeps everything between the CONTENT and SOURCE INDEX markers, re-inserts the sections, and
rebuilds the rest of the page around them. Apart from the "Last updated" stamp under the title, which
is set to the current UTC time on every run, running it twice gives the same file. tools/build_pdf.sh
runs this script first, so every page or PDF build carries a fresh stamp.
"""
import html, json, os, re, subprocess, sys
from urllib.parse import unquote
from datetime import datetime, timezone

PDF = 'geert-greydanus-timeline.pdf'
START, END = '<!-- CONTENT START -->', '<!-- CONTENT END -->'
SI_START, SI_END = '<!-- SOURCE INDEX START -->', '<!-- SOURCE INDEX END -->'

# Sections kept as separate files. Each is inserted before the h2 named here, between markers, so a
# re-run replaces it with the current file.
EXTRA_SECTIONS = [('journey.html', '18991943-friesland-rotterdam-and-the-police'),
                  ('gerstein.html', 'the-airman-helping-network-around-varsseveld-janmay-1944'),
                  ('markus.html', 'april-august-1944-arrest-the-vught-bunker-transport'),
                  ('fellowprisoners.html', 'august-1944-may-1945-buchenwald-niederorschel-and-liberation'),
                  ('deathmarch.html', 'may-1945-september-1947-back-in-rotterdam')]
SECTIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sections')


def add_sections(body):
    for name, before in EXTRA_SECTIONS:
        start, end = '<!-- SECTION %s START -->' % name, '<!-- SECTION %s END -->' % name
        body = re.sub(re.escape(start) + '.*?' + re.escape(end) + r'\n?', '', body, flags=re.S)
        frag = open(os.path.join(SECTIONS_DIR, name), encoding='utf-8').read().strip()
        anchor = '<h2 id="%s">' % before
        if anchor not in body:
            sys.exit('page.py: no <h2 id="%s"> to put %s before' % (before, name))
        body = body.replace(anchor, '%s\n%s\n%s\n%s' % (start, frag, end, anchor), 1)
    return body


def classify_tables(body):
    """Style a table that has no class yet: a timeline if it has Date and Event columns, else facts."""
    def one(m):
        t = m.group(0)
        head = re.sub(r'<[^>]+>', '|', t[:400])
        cls = 'timeline' if '|Date|' in head and '|Event|' in head else 'facts'
        return '<div class="table-wrap">%s</div>' % re.sub(r'^<table[^>]*>', '<table class="%s">' % cls, t)
    return re.sub(r'<table(?![^>]*class=).*?</table>', one, body, flags=re.S)


def label_cells(body):
    """Give each bare cell its column name, so a table can stack into cards on a phone."""
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


def slug(text):
    text = html.unescape(re.sub(r'<[^>]+>', '', text)).lower()
    return re.sub(r'[^0-9a-z]+', '-', text).strip('-') or 'section'


def add_anchors(*parts):
    """Give every heading and every timeline row an id, so each can be linked to. An id, once written,
    stays: index.html is rewritten with it, so links keep working when rows are added later."""
    taken = set(re.findall(r'\sid="([^"]+)"', ''.join(parts)))
    def new_id(text):
        base = slug(text)
        i, n = base, 2
        while i in taken:
            i, n = '%s-%d' % (base, n), n + 1
        taken.add(i)
        return i
    def heading(m):
        return '<h%s id="%s"%s>%s</h%s>' % (m.group(1), new_id(m.group(3)), m.group(2), m.group(3), m.group(1))
    def table(m):
        return re.sub(r'<tr>(?=<td data-label="Date">(.*?)</td>)',
                      lambda r: '<tr id="%s">' % new_id(r.group(1)), m.group(0), flags=re.S)
    out = []
    for part in parts:
        part = re.sub(r'<h([2-6])((?:(?!\sid=)[^>])*)>(.*?)</h\1>', heading, part, flags=re.S)
        out.append(re.sub(r'<table class="timeline">.*?</table>', table, part, flags=re.S))
    return out


SKIP_LINKS = ('https://github.com/jared-dykstra/geert-greydanus/issues', 'https://www.openstreetmap.org/')
SAVED_FROM = re.compile(r'saved from (\S+?)(?: |\)| -->|$)', re.I | re.M)
ONLINE_ONLY = [('https://collections.arolsen-archives.org/', 'Arolsen card images not bundled'),
               ('https://www.oorlogsbronnen.nl/zoeken', 'search page'),
               ('https://www.oorlogsbronnen.nl/tijdlijn/', 'page loads by script'),
               ('https://oorlogvoorderechter.nl/', 'page loads by script'),
               ('https://hdl.handle.net/', 'database page'),
               ('https://vha.usc.edu/', 'restricted testimony; cited by tape and timecode')]


def build_source_index(body, old):
    """Rebuild the source-index table from every link in the page, so it never falls behind. A local copy
    is listed with its original link (from data-original, else the index as it stood, else the copy's own
    "saved from" header); a link
    with no local copy keeps the reason already given for it, else a default by site."""
    reasons, known, old_rows = {}, {}, []
    for first, second in re.findall(r'<tr><td>(.*?)</td><td>(.*?)</td></tr>', old, flags=re.S):
        old_rows.append((first, second))
        text = html.unescape(re.sub(r'<[^>]+>', '', first))
        if second.startswith('online only'):
            reasons[text] = second
        elif text != 'No online original':
            for href in re.findall(r'href="([^"]+)"', second):
                known.setdefault(html.unescape(href), text)
    order, local, external = [], {}, set()
    for attrs in re.findall(r'<a\s([^>]*)>', body):
        m = re.search(r'href="([^"]*)"', attrs)
        if not m:
            continue
        href = html.unescape(m.group(1))
        if href.startswith(('#', 'mailto:')) or href.startswith(SKIP_LINKS):
            continue
        o = re.search(r'data-original="([^"]*)"', attrs)
        if href.startswith(('http://', 'https://')):
            key = href
            external.add(key)
        else:
            key = href
            if o and not local.get(key):
                local[key] = html.unescape(o.group(1))
            local.setdefault(key, None)
        if key not in order:
            order.append(key)
    rows = []
    for key in order:
        if key in local:
            orig = local[key] or known.get(key) or known.get(key.split('#')[0])
            if not orig:
                try:
                    with open(os.path.join(ROOT, unquote(key.split('#')[0])), 'rb') as f:
                        m = SAVED_FROM.search(f.read(2000).decode('utf-8', 'ignore'))
                    orig = m.group(1) if m else None
                except OSError:
                    orig = None
            a = '<a href="%s">%s</a>' % (html.escape(key, quote=True), html.escape(orig) if orig else 'No online original')
            rows.append('<tr><td>%s</td><td><a href="%s">%s</a></td></tr>'
                        % (a, html.escape(key, quote=True), html.escape(unquote(key))))
        else:
            reason = reasons.get(key) or 'online only: ' + next(
                (why for site, why in ONLINE_ONLY if key.startswith(site)), 'not snapshotted')
            rows.append('<tr><td><a href="%s">%s</a></td><td>%s</td></tr>'
                        % (html.escape(key, quote=True), html.escape(key), reason))
    # Keep rows for links no longer on the page, so no saved copy loses the record of where it came from.
    listed = set(order)
    for first, second in old_rows:
        hrefs = [html.unescape(h) for h in re.findall(r'href="([^"]+)"', first + second)]
        if not listed.intersection(hrefs) and html.unescape(re.sub(r'<[^>]+>', '', first)) not in listed:
            rows.append('<tr><td>%s</td><td>%s</td></tr>' % (first, second))
    head = '<tr><th>Original link</th><th>Local copy</th></tr>'
    return re.sub(r'<table class="facts index">.*?</table>',
                  lambda _: '<table class="facts index">%s%s</table>' % (head, ''.join(rows)), old, count=1, flags=re.S)


def toc(body):
    items = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    lis = ''.join('<li><a href="#%s">%s</a></li>' % (i, re.sub(r'<[^>]+>', '', t)) for i, t in items)
    return ('<nav class="toc" aria-label="Contents"><details open><summary class="toc-title">Contents</summary>'
            '<ol>%s</ol></details></nav>' % lis)


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVED_ON = re.compile(r'saved from \S+.*? on (\d{4}-\d{2}-\d{2})', re.I)


def first_added():
    """Map each file in git to the date of the commit that first added it."""
    try:
        out = subprocess.run(['git', '-c', 'core.quotePath=false', 'log', '--reverse', '--diff-filter=A',
                              '--format=%x00%cs', '--name-only'], cwd=ROOT, capture_output=True, text=True,
                             check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return {}
    added = {}
    for chunk in out.split('\x00')[1:]:
        lines = chunk.strip().split('\n')
        for f in lines[1:]:
            added.setdefault(f.strip(), lines[0].strip())
    return added


def saved_dates(text):
    """Map the local copy behind each link that has a data-original to the date it was saved: the date in
    the copy's own "saved from" header, else the date it was first committed, else its file date."""
    added, dates = first_added(), {}
    for href in re.findall(r'<a [^>]*?href="([^"#]+)[^"]*"[^>]*\bdata-original=', text):
        path = unquote(html.unescape(href))
        if href in dates or not os.path.isfile(os.path.join(ROOT, path)):
            continue
        with open(os.path.join(ROOT, path), 'rb') as f:
            m = SAVED_ON.search(f.read(2000).decode('utf-8', 'ignore'))
        dates[href] = (m.group(1) if m else added.get(path) or
                       datetime.fromtimestamp(os.path.getmtime(os.path.join(ROOT, path)), timezone.utc).strftime('%Y-%m-%d'))
    return dates


def render(doc):
    if START not in doc or SI_START not in doc:
        sys.exit('page.py: the input has no CONTENT or SOURCE INDEX markers')
    body = doc.split(START, 1)[1].split(END, 1)[0].strip()
    source_index = doc.split(SI_START, 1)[1].split(SI_END, 1)[0]
    body = label_cells(classify_tables(add_sections(body)))
    source_index = build_source_index(body, source_index)
    body, source_index = add_anchors(body, source_index)
    toc_html = toc(body + '<h2 id="archive-sources">Source index</h2>')
    now = datetime.now(timezone.utc)
    updated = ('<p class="updated">Last updated <time datetime="%s">%s</time></p>'
               % (now.strftime('%Y-%m-%dT%H:%MZ'), now.strftime('%-d %B %Y, %H:%M UTC')))
    saved = json.dumps(saved_dates(body + source_index), sort_keys=True, separators=(',', ':'))
    return TEMPLATE.format(toc=toc_html, body=body, source_index=source_index, pdf=PDF, updated=updated, saved=saved,
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
.lede{font-size:20px;max-width:46em;margin:0 0 12px;color:var(--ink)}
.updated{font:500 14px/1.4 var(--sans);color:var(--muted);margin:0 0 24px}
.photo{margin:24px 0;max-width:640px}.photo img{display:block;width:100%;height:auto;border-radius:4px}.photo figcaption{font:400 14px/1.5 var(--sans);color:var(--muted);margin-top:8px}.photo-pair{display:grid;grid-template-columns:1.944fr .75fr;gap:12px;align-items:start;margin:24px 0}.photo-pair .photo{margin:0;max-width:none}@media (max-width:600px){.photo-pair{grid-template-columns:1fr}}@media print{.photo-pair{break-inside:avoid}}
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
.feature{margin:20px 0 28px;padding:20px 24px;border:1px solid var(--rule);border-left:4px solid var(--accent);border-radius:8px;background:var(--accent-soft)}
.feature p{margin:0 0 8px}.feature p:last-child{margin:0}
.feature-kicker{font:700 12px var(--sans);text-transform:uppercase;letter-spacing:.08em;color:var(--accent)}
.feature-title{font-size:22px;line-height:1.3;font-weight:600}
.feature-links{font:14px/1.5 var(--sans)}
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
details.steps{margin:16px 0;border:1px solid var(--rule);border-radius:8px;background:var(--card);padding:12px 16px}
details.steps summary{cursor:pointer;font:600 15px var(--sans);color:var(--accent)}
details.steps[open] summary{margin-bottom:8px}
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
.src-pop{position:absolute;z-index:50;width:max-content;max-width:min(340px,calc(100vw - 16px));background:var(--card);border:1px solid var(--rule);border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.18);padding:6px;font:14px/1.4 var(--sans)}
.src-opt{display:block;padding:8px 12px;border-radius:6px;text-decoration:none;color:var(--ink)}
.src-opt:hover,.src-opt:focus{background:var(--accent-soft);outline:none}
.src-opt strong{display:block;color:var(--accent);font-weight:600}
.src-opt span{display:block;color:var(--muted);font-size:13px;overflow-wrap:anywhere}
@media print{.src-pop{display:none}}
.anchor{margin-left:.35em;font:400 .8em var(--sans);color:var(--muted);text-decoration:none;opacity:0;transition:opacity .15s}
h2:hover .anchor,h3:hover .anchor,h4:hover .anchor,tr:hover .anchor,.anchor:focus{opacity:1}
.anchor:hover{color:var(--accent)}
@media (hover:none){.anchor{opacity:.6}}
tr:target{background:var(--accent-soft)}
h2:target,h3:target,h4:target{color:var(--accent)}
@media print{.anchor{display:none}}
@media print{details.steps::details-content{content-visibility:visible;display:block}.toc,.top,.actions,#archive-sources{display:none}.layout{display:block}body{background:#fff;font-size:12pt}h2{break-after:avoid}tr{break-inside:avoid}}
"""

SCRIPT = """<script>
(function(){var saved=window.SAVED||{},pop=null,cur=null;
var months=['January','February','March','April','May','June','July','August','September','October','November','December'];
function host(u){try{return new URL(u).hostname.replace(/^www\\./,'')}catch(e){return u}}
function day(d){var p=d.split('-');return +p[2]+' '+months[+p[1]-1]+' '+p[0]}
function opt(href,title,note,local){var o=document.createElement('a');o.className='src-opt';o.href=href;o.target='_blank';if(!local)o.rel='noopener';
var t=document.createElement('strong');t.textContent=title;var n=document.createElement('span');n.textContent=note;o.appendChild(t);o.appendChild(n);
o.addEventListener('click',function(){close(false)});return o}
function close(refocus){if(!pop)return;pop.remove();pop=null;cur.setAttribute('aria-expanded','false');if(refocus)cur.focus();cur=null}
function open(a){var href=a.getAttribute('href'),d=saved[href.split('#')[0]];cur=a;a.setAttribute('aria-expanded','true');
pop=document.createElement('div');pop.className='src-pop';pop.setAttribute('role','dialog');pop.setAttribute('aria-label','Open this source');
pop.appendChild(opt(a.getAttribute('data-original'),'Original source',host(a.getAttribute('data-original')),false));
pop.appendChild(opt(href,'Saved copy in this archive',d?'Saved '+day(d):'Saved copy',true));
document.body.appendChild(pop);var r=a.getClientRects()[0]||a.getBoundingClientRect(),w=pop.offsetWidth,h=pop.offsetHeight,vw=document.documentElement.clientWidth;
var left=Math.max(8,Math.min(r.left,vw-w-8)),top=r.bottom+6;if(top+h>window.innerHeight&&r.top-h-6>0)top=r.top-h-6;
pop.style.left=(left+window.scrollX)+'px';pop.style.top=(top+window.scrollY)+'px';pop.querySelector('a').focus({preventScroll:true})}
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[data-original]');
if(pop&&!pop.contains(e.target)){var same=a===cur;close(false);if(same){e.preventDefault();return}}
if(!a||e.button||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey)return;e.preventDefault();open(a)});
document.addEventListener('keydown',function(e){if(!pop)return;if(e.key==='Escape'){close(true);return}
if(e.key==='ArrowDown'||e.key==='ArrowUp'){var o=[].slice.call(pop.querySelectorAll('a')),i=o.indexOf(document.activeElement);e.preventDefault();o[(i+(e.key==='ArrowDown'?1:o.length-1))%o.length].focus()}
if(e.key==='Tab'&&!pop.contains(document.activeElement))close(false)});
window.addEventListener('resize',function(){close(false)});
[].forEach.call(document.querySelectorAll('a[data-original]'),function(a){a.setAttribute('aria-haspopup','dialog');a.setAttribute('aria-expanded','false')});})();
(function(){function mark(el,id,label){var a=document.createElement('a');a.className='anchor';a.href='#'+id;a.textContent='#';
a.setAttribute('aria-label',label);a.title=label;el.appendChild(a)}
[].forEach.call(document.querySelectorAll('main h2[id],main h3[id],main h4[id]'),function(h){mark(h,h.id,'Link to this section')});
[].forEach.call(document.querySelectorAll('table.timeline tr[id] > td:first-child'),function(td){mark(td,td.parentNode.id,'Link to this date')});})();
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
<meta name="google-site-verification" content="_0uzc1kWQpNCWJH8MbeLqkACc4nvKDGC8PqsCSC1Q7o" />
<style>{css}</style>
</head>
<body>
<header class="hero"><div class="hero-inner">
<p class="kicker">A timeline from the family papers</p>
<h1>Geert Greydanus <span class="years">1899–1965</span></h1>
<p class="lede">A Rotterdam police detective who went into hiding in April 1943 rather than arrest Jews, helped Allied airmen in the Achterhoek, where the Varsseveld group called him <a href="#pseudonyms-exact-wording">&ldquo;Oom Geert&rdquo;</a>, survived Vught, Buchenwald and Niederorschel, and later farmed near Clinton, Ontario.</p>
{updated}
<div class="actions">
<a class="btn btn-primary" href="{pdf}" download>""" + DOWNLOAD_ICON + """Download as PDF</a>
<a class="btn btn-secondary" href="sources/Hoekstra_2020_Geert-Greydanus-a-man-of-principles.pdf" download>""" + DOWNLOAD_ICON + """Download Jurjen Hoekstra&rsquo;s 2020 Booklet</a>
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
<section class="about"><h2 id="about-this-page">About this page</h2>
<p>This page is the timeline <em>Geert Greydanus — Timeline from the Family Papers</em>, written from the family papers and the sources saved with it. Wherever a source was saved (family papers, published articles, archive records and web pages), its link offers a choice: the original source, or the copy saved in this archive with the date it was saved. The saved copy keeps the page working if the original site changes or disappears. Links to sources that could not be saved still go to the original site.</p>
<p>The <a href="{pdf}">PDF</a> is the same document, for printing or keeping.</p>
</section>
</main>
</div>
<a class="top" href="#">↑ Top</a>
<script>window.SAVED={saved};</script>
""" + SCRIPT.replace('{', '{{').replace('}', '}}') + """
</body>
</html>
"""

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    doc = open(src, encoding='utf-8').read()
    open(out, 'w', encoding='utf-8').write(render(doc))
