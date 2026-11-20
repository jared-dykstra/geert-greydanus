"""Separate pages for the key people in Geert's story, and the sitemap.

Every page is cut from the laid-out index.html, so it always says what the timeline says: edit the
timeline, never the files in people/. tools/page.py calls build() after it lays out index.html.

A page is one of two kinds:
- a section page, which shows the section under one heading (down to the next heading of the same or
  higher level), with that heading as its title;
- a gathered page, for someone without a section of their own, which shows their rows in "People in
  Geert's story", any sections named, and every timeline row that mentions them.

Each page gets its own title, description and structured data, so a search for that person's name can
find it. Its "Last updated" stamp, and its <lastmod> in the sitemap, change only when its title,
description or text change.
"""
import html, json, os, re

BASE = 'https://jared-dykstra.github.io/geert-greydanus/'
DIR = 'people'


def person(name, alt=(), born=None, born_in=None, died=None, died_in=None):
    p = {'@type': 'Person', 'name': name}
    if alt:
        p['alternateName'] = list(alt)
    if born:
        p['birthDate'] = born
    if born_in:
        p['birthPlace'] = {'@type': 'Place', 'name': born_in}
    if died:
        p['deathDate'] = died
    if died_in:
        p['deathPlace'] = {'@type': 'Place', 'name': died_in}
    return p


def entry(slug, desc, people, section=None, title=None, name=None, rows=None, sections=(), timeline=None):
    """section: the id of the heading a section page is cut from. For a gathered page: rows, a pattern
    for the first cell of their rows in "People in Geert's story"; sections, heading ids to include;
    timeline, a pattern for the timeline rows to include. title overrides the heading as the page title;
    name is the link text used for the page in lists (default: the people's names)."""
    return dict(slug=slug, desc=desc, people=people, section=section, title=title, rows=rows,
                sections=sections, timeline=timeline,
                name=name or ' and '.join(p['name'] for p in people))


# Dates and places are only those the page's own text states; where it leaves a disagreement between sources
# unresolved, the field is left out. Descriptions say no more than the text does.
PEOPLE = [
    entry('wietske-walinga-greydanus',
          "Geert Greydanus's daughter Wietske: hostage in Kamp Vught in 1943, and her diary of a bicycle "
          'journey from Rotterdam to Friesland for food in the hunger winter of 1945.',
          [person('Wietske Walinga-Greydanus', ['Wietske Greydanus', 'Wietske Greijdanus', 'Grietje Wietske Greydanus',
                                                'Wietske Walinga', 'Wilma Walinga'], '1924-03-04', 'Rotterdam', '2008-07-28')],
          title='Wietske Walinga-Greydanus (1924–2008) and her hunger-winter journey',
          name='Wietske Walinga-Greydanus', rows=r'Wietske', timeline=r'Wietske(?! Baron)'),
    entry('satter-family',
          'Hendrik Satter and his children Jo and Wil, who hid Geert Greydanus on their farm near Varsseveld; Hendrik '
          'was arrested with him on 20 April 1944.',
          [person('Hendrik Satter', (), '1885-08-01', 'Haaften', '1949-10-16', 'Doetinchem'),
           person('Johannis Satter', ['Jo Satter']),
           person('Willemien Satter', ['Wil Satter'], '1922-03-07', 'Haaften', '2019-05-12')],
          title='The Satter family, who hid Geert Greydanus near Varsseveld', name='The Satter family',
          rows=r'Satter', sections=['how-his-account-reached-the-satter-farm'], timeline=r'Satter'),
    entry('anne-schaap',
          'Anne (Ane) Schaap, known as "de Jodenman", arrested with Geert Greydanus on 20 April 1944, interrogated '
          'five times in 16 days and released.',
          [person('Anne Schaap', ['Ane Schaap', 'A. Schaap'], '1919-07-08', 'Leeuwarden')],
          title='Anne (Ane) Schaap, arrested with Geert Greydanus on 20 April 1944',
          rows=r'Schaap', timeline=r'(?<!Erik )Schaap'),
    entry('leo-palache',
          'Isaac Leo Palache of Amsterdam, a Jewish prisoner whom Geert Greydanus helped along on the death march to '
          'Buchenwald in April 1945, by family accounts.',
          [person('Isaac Leo Palache', ['Leo Palache', 'Izak Palache', 'Izak Leo Palache'], '1926-01-20', 'Amsterdam',
                  '1996-08-09', 'Amsterdam')],
          title='Isaac Leo Palache (1926–1996) and the Niederorschel death march', name='Leo Palache',
          rows=r'Palache', sections=['geert-and-leo-in-the-interview'], timeline=r'Palache'),
    entry('willy-markus',
          'Willem (Willy) Markus, the Arnhem SD informer whose betrayal led to the arrests of 20 April 1944 in the '
          'Achterhoek, among them Geert Greydanus.',
          [person('Willem Markus', ['Willy Markus'], '1902-03-24', 'Ambt Doetinchem', '1978-03-24', 'Enschede')],
          section='the-betrayal-willy-markus',
          title='Willy Markus, the SD informer who betrayed the Achterhoek (1944)', name='Willy Markus'),
    entry('kurt-gerstein',
          "How Kurt Gerstein's account of the gas chambers reached the Satter farm, where Geert Greydanus hid, and was "
          'found under a tile of its chicken coop after the war.',
          [person('Kurt Gerstein', (), '1905-08-11', 'Münster', '1945-07-25', 'Paris')],
          section='the-gerstein-report-in-the-chicken-coop',
          title='Kurt Gerstein and the Gerstein report in the Satter chicken coop'),
    entry('willem-arnold-rohaan',
          'Willem Arnold Rohaan, Neede farmer and deputy commander of the Ordedienst, named by Geert Greydanus among his '
          'fellow prisoners in Vught; shot at Overveen on 6 June 1944.',
          [person('Willem Arnold Rohaan', (), '1912-10-26', 'Neede', '1944-06-06', 'Overveen')],
          section='willem-arnold-rohaan'),
    entry('hendrik-pieter-heinen',
          'Hendrik Pieter (Henk) Heinen, Eibergen printer of the underground Trouw, arrested on 20 April 1944 through '
          'Willy Markus and shot at Overveen on 6 June 1944.',
          [person('Hendrik Pieter Heinen', ['Henk Heinen'], '1914-11-28', 'Eibergen', '1944-06-06', 'Overveen')],
          section='hendrik-pieter-heinen'),
    entry('martinus-antonius-lelivelt',
          'Martinus Antonius (Martin) Lelivelt, Lichtenvoorde builder who hid Jews and airmen, probably the "Lebbeveld" '
          'Geert Greydanus named from Vught; shot at Fort Rhijnauwen on 25 July 1944.',
          [person('Martinus Antonius Lelivelt', ['Martin Lelivelt'], '1896-01-17', 'Lichtenvoorde', '1944-07-25',
                  'Fort Rhijnauwen')],
          section='martinus-antonius-lelivelt', title='Martinus Antonius (Martin) Lelivelt (Lichtenvoorde, 1896 – 1944)'),
    entry('teunis-klaas-wortman',
          'Teunis Klaas Wortman, the Neede marechaussee whom Geert Greydanus remembered from Vught but could not name; '
          'shot at Overveen on 6 June 1944.',
          [person('Teunis Klaas Wortman', (), '1911-11-27', 'Geldermalsen', '1944-06-06', 'Overveen')],
          section='teunis-klaas-wortman'),
    entry('cornelis-coenraad-poulie',
          'Cornelis Coenraad (Kees) Poulie, the Varsseveld marechaussee who brought an Allied airman to the Satter farm; '
          'shot at Overveen on 6 June 1944, aged 24.',
          [person('Cornelis Coenraad Poulie', ['Kees Poulie'], '1919-07-05', 'Den Helder', '1944-06-06', 'Overveen')],
          section='cornelis-coenraad-poulie'),
    entry('albertus-hendrikus-marcusse',
          'Albertus Hendrikus (Albert) Marcusse, chief detective of the Nijmegen police and member of its resistance '
          'group; shot at Overveen on 6 June 1944.',
          [person('Albertus Hendrikus Marcusse', ['Albert Marcusse'], '1903-11-02', 'Batenburg', '1944-06-06', 'Overveen')],
          section='albertus-hendrikus-marcusse', title='Albertus Hendrikus (Albert) Marcusse (1903–1944)'),
    entry('gerrit-jan-van-den-boogerd',
          'Gerrit Jan van den Boogerd ("Oom Gert"), candidaat-notaris and resistance leader deceived by Willy Markus; '
          'shot at Fort Rhijnauwen on 25 July 1944.',
          [person('Gerrit Jan van den Boogerd', ['Oom Gert'], '1908-08-22', 'Zwartewaal', '1944-07-25', 'Fort Rhijnauwen')],
          section='gerrit-jan-van-den-boogerd'),
    entry('willem-en-jacobus-westland',
          'The brothers Willem and Jacobus Westland, owners of the Oranje hotel and the Luxor cinema in Wageningen; shot '
          'at Overveen on 6 June 1944.',
          [person('Willem Westland', (), '1900-04-08', 'Wageningen', '1944-06-06', 'Overveen'),
           person('Jacobus Westland', (), None, 'Wageningen', '1944-06-06', 'Overveen')],
          section='willem-en-jacobus-westland', title='Willem Westland (1900–1944) and Jacobus Westland (1902–1944)'),
    entry('jacob-stigter',
          'Jacob (Jaap) Stigter of Honselersdijk and KP-Neede, shot in Kamp Vught on 9 August 1944; Geert Greydanus '
          'told his family that Jaap had prayed for the prisoners in Vught.',
          [person('Jacob Stigter', ['Jaap Stigter'], '1924-07-23', 'Honselersdijk', '1944-08-09', 'Kamp Vught')],
          section='jacob-stigter', name='Jaap Stigter', rows=r'Stigter', timeline=r'Stigter'),
    entry('johannes-berlijn',
          "Johannes (Jo) Berlijn, Rotterdam forger for the LO, whose house was Geert Greydanus's first hiding place; "
          'killed in Kamp Vught on 30 August 1944.',
          [person('Johannes Berlijn', ['Jo Berlijn'], None, 'Rotterdam', '1944-08-30', 'Kamp Vught')],
          section='johannes-berlijn'),
    entry('johan-gerard-westerweel',
          'Johan Gerard (Joop) Westerweel, head of the Montessori school in Rotterdam, who helped Jews escape to Spain; '
          'shot in Kamp Vught on 11 August 1944.',
          [person('Johan Gerard Westerweel', ['Joop Westerweel'], None, 'Zutphen', '1944-08-11', 'Kamp Vught')],
          section='johan-gerard-westerweel'),
    entry('karel-roelof-verschuur',
          'Karel Roelof Verschuur, Wageningen-born painter condemned in the Vught bunker and shot at Overveen on 6 June '
          '1944; unlikely to be the "Karel" Geert Greydanus remembered.',
          [person('Karel Roelof Verschuur', ['Carel Verschuur'], None, 'Wageningen', '1944-06-06', 'Overveen')],
          section='carel-verschuur', title='Karel Roelof Verschuur (Wageningen, 1919 – Overveen, 1944)'),
    entry('eemke-van-der-veen',
          "Eemke van der Veen, town-hall clerk in Haren, possibly Geert Greydanus's cellmate in Vught; shot in Kamp "
          'Vught on 22 August 1944.',
          [person('Eemke van der Veen', (), '1902-06-05', 'Nieuweschans', '1944-08-22', 'Kamp Vught')],
          section='eemke-van-der-veen'),
    entry('aaron-akker',
          'Aaron Akker of Leeuwarden, one of the Dutch Jews with Geert Greydanus at Niederorschel, who died during the '
          'death march to Buchenwald in April 1945.',
          [person('Aaron Akker', (), None, 'Sneek', '1945-04-06')],
          section='aaron-akker'),
    entry('johannes-antonius-schepen',
          'Johannes Antonius (Anton) Schepen, Groningen electrician and political prisoner in the Niederorschel subcamp '
          'of Buchenwald with Geert Greydanus; both are on a list of returned prisoners of 11 May 1945.',
          [person('Johannes Antonius Schepen', ['Anton Schepen'], '1899-11-09', 'Joure', '1984-10-02')],
          section='johannes-antonius-anton-schepen-the-third-man',
          title='Johannes Antonius (Anton) Schepen (Joure, 1899 – 1984)'),
]

STAMP = re.compile(r'<p class="updated">.*?</p>\n?')
TIME = re.compile(r'<time datetime="([^"]+)"')


def url(slug):
    return '%s%s/%s.html' % (BASE, DIR, slug)


def mentions():
    """The people with pages, for the main page's structured data."""
    return [dict(p, url=url(e['slug'])) for e in PEOPLE for p in e['people']]


def links_list(current=None, prefix=''):
    return ', '.join('<a href="%s%s.html">%s</a>' % (prefix, e['slug'], html.escape(e['name']))
                     for e in PEOPLE if e['slug'] != current)


def strip_comments(s):
    return re.sub(r'<!--.*?-->\n?', '', s, flags=re.S)


def cut(body, hid, keep_heading=False):
    """The section under heading hid. Without keep_heading, the heading itself is returned apart (it becomes
    the page's h1) and what was under it moves up to h2; with it, the heading is kept and becomes an h2."""
    m = re.search(r'<h([2-6]) id="%s"[^>]*>(.*?)</h\1>' % re.escape(hid), body, flags=re.S)
    if not m:
        raise SystemExit('people.py: no heading with id "%s"' % hid)
    level = int(m.group(1))
    end = re.compile(r'<h[2-%d][ >]' % level).search(body, m.end())
    frag = strip_comments(body[m.start() if keep_heading else m.end():end.start() if end else len(body)]).strip()
    top = 2 if keep_heading else 1
    frag = re.sub(r'<(/?)h([2-6])', lambda t: '<%sh%d' % (t.group(1), min(6, max(2, int(t.group(2)) - level + top))), frag)
    return m.group(2), frag


def text(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s))


def gather(body, e):
    """A gathered page's text: People-table rows, sections, then the timeline rows that mention the person."""
    parts = []
    if e['rows']:
        t = re.search(r'<h2 id="people-in-geerts-story">.*?(<table[^>]*>)(<thead>.*?</thead>)(.*?)</table>', body, re.S)
        rows = [r for r in re.findall(r'<tr(?: id="[^"]*")?>.*?</tr>', t.group(3), re.S)
                if re.search(e['rows'], text(re.search(r'<td[^>]*>(.*?)</td>', r, re.S).group(1)))]
        if rows:
            parts.append('<div class="table-wrap">%s%s<tbody>%s</tbody></table></div>' % (t.group(1), t.group(2), ''.join(rows)))
    for hid in e['sections']:
        parts.append(cut(body, hid, keep_heading=True)[1])
    if e['timeline']:
        rows = []
        for table in re.findall(r'<table class="timeline">.*?</table>', body, re.S):
            rows += [r for r in re.findall(r'<tr id="[^"]+">.*?</tr>', table, re.S) if re.search(e['timeline'], text(r))]
        if rows:
            parts.append('<h2 id="in-the-timeline">In the timeline</h2>\n<div class="table-wrap"><table class="timeline">'
                         '<thead><tr><th>Date</th><th>Event</th><th>Source</th></tr></thead><tbody>%s</tbody></table></div>'
                         % ''.join(rows))
    if not parts:
        raise SystemExit('people.py: nothing found for %s' % e['slug'])
    return '\n'.join(parts)


LINK = re.compile(r'<a class="person-page" href="[^"]*">(.*?)</a>', re.S)
LINK_P = re.compile(r'<p class="person-page-link">.*?</p>\n?', re.S)


def unlink(s):
    """Remove the links to person pages that link_pages() added."""
    return LINK.sub(r'\1', LINK_P.sub('', s))


def site_map(pdf):
    """The main page's site map: the page itself, the PDF, and every person page."""
    items = ''.join('<li><a href="%s/%s.html">%s</a> <span class="desc">%s</span></li>'
                    % (DIR, e['slug'], html.escape(e['name']), html.escape(e['desc'])) for e in PEOPLE)
    return ('<section class="site-map"><h2 id="site-map">Site map</h2>\n'
            '<ul><li><a href="%s">The timeline as a PDF</a> <span class="desc">The same document, for printing or keeping.</span></li></ul>\n'
            '<h3 id="site-map-people">Pages for people in the timeline</h3>\n<ul>%s</ul>\n</section>' % (pdf, items))


def link_pages(body):
    """Link the main page to the person pages: each name in "People in Geert's story" that has a page, and a
    line under each heading a section page is cut from. Earlier links are removed first, so a re-run
    gives the same page."""
    body = unlink(body)
    def table(m):
        def row(r):
            cell = r.group(2)
            name = text(cell)
            for e in PEOPLE:
                pat = e['rows'] or '|'.join(re.escape(p['name'].split()[-1]) for p in e['people'])
                if re.search(pat, name):
                    return '%s<a class="person-page" href="%s/%s.html">%s</a>%s' % (r.group(1), DIR, e['slug'], cell, r.group(3))
            return r.group(0)
        return re.sub(r'(<tr(?: id="[^"]*")?><td data-label="Person">)(.*?)(</td>)', row, m.group(0), flags=re.S)
    body = re.sub(r'<h2 id="people-in-geerts-story">.*?</table>', table, body, count=1, flags=re.S)
    for e in PEOPLE:
        if e['section']:
            m = re.search(r'<h([2-6]) id="%s"[^>]*>.*?</h\1>\n?' % re.escape(e['section']), body, re.S)
            body = body[:m.end()] + ('<p class="person-page-link"><a class="person-page" href="%s/%s.html">Page for %s</a></p>\n'
                                     % (DIR, e['slug'], html.escape(e['name']))) + body[m.end():]
    return body


def rebase(frag):
    """Point the cut text's links at the right place from people/: local files one folder up, and links
    into the rest of the timeline at index.html."""
    ids = set(re.findall(r'\sid="([^"]+)"', frag))
    def one(m):
        attr, v = m.group(1), m.group(2)
        if v.startswith('#'):
            return m.group(0) if v[1:] in ids else '%s="../index.html%s"' % (attr, v)
        if re.match(r'[a-z][a-z0-9+.-]*:', v, re.I) or v.startswith('//'):
            return m.group(0)
        return '%s="../%s"' % (attr, v)
    return re.sub(r'(?<![\w-])(href|src)="([^"]*)"', one, frag)


def page(e, h1, frag, updated, saved, css, script):
    plain = text(h1)
    people = e['people']
    ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': plain, 'url': url(e['slug']),
          'inLanguage': 'en', 'description': e['desc'], 'author': {'@type': 'Person', 'name': 'Jared Dykstra'},
          'license': 'https://creativecommons.org/licenses/by/4.0/',
          'isPartOf': {'@type': 'Article', 'headline': 'Geert Greydanus (1899–1965): a timeline from the family papers',
                       'url': BASE},
          'about': people[0] if len(people) == 1 else people}
    q = lambda s: html.escape(s, quote=True)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{u}">
<link rel="license" href="https://creativecommons.org/licenses/by/4.0/">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Geert Greydanus archive">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:url" content="{u}">
<script type="application/ld+json">
{ld}
</script>
<style>{css}</style>
</head>
<body>
<header class="hero"><div class="hero-inner single">
<p class="kicker"><a href="../index.html">Geert Greydanus archive</a></p>
<h1>{h1}</h1>
<p class="lede">{dh}</p>
{updated}
<div class="actions">
<a class="btn btn-secondary" href="../index.html">The full timeline of Geert Greydanus (1899–1965)</a>
</div>
</div></header>
<div class="single">
<main>
{frag}
<section class="about"><h2 id="about-this-page">About this page</h2>
<p>Taken from <a href="../index.html"><em>Geert Greydanus (1899–1965): a timeline from the family papers</em></a>. Each saved source links to the original and to the copy in this archive.</p>
<p>Other people: {others}.</p>
<p>Text <a href="https://creativecommons.org/licenses/by/4.0/" rel="license">CC BY 4.0</a>, Jared Dykstra; family papers and copies of others&rsquo; work excluded (<a href="https://github.com/jared-dykstra/geert-greydanus#license">details</a>).</p>
</section>
</main>
</div>
<script>window.SAVED={saved};</script>
{script}
</body>
</html>
""".format(t=q(plain), d=q(e['desc']), dh=html.escape(e['desc']), u=url(e['slug']), h1=h1, frag=frag,
           updated=updated, css=css, ld=json.dumps(ld, ensure_ascii=False, separators=(',', ':')),
           others=links_list(e['slug']), saved=saved, script=script)


def content(doc):
    """What a page's stamp tracks: its title, description and text, not the shared styles, scripts or the
    list of other pages."""
    head = re.search(r'<title>.*?<meta name="description"[^>]*>', doc, re.S)
    main = re.search(r'<h1>.*?<section class="about">', doc, re.S)
    return STAMP.sub('', (head.group(0) if head else '') + (main.group(0) if main else ''))


def build(root, body, updated, now, css, script, saved_dates):
    """Write people/*.html and sitemap.xml."""
    os.makedirs(os.path.join(root, DIR), exist_ok=True)
    stamp_iso = now.strftime('%Y-%m-%dT%H:%MZ')
    lastmods, wanted = {}, set()
    for e in PEOPLE:
        if e['section']:
            heading, frag = cut(body, e['section'])
            h1 = html.escape(e['title']) if e['title'] else heading
            if e['rows'] or e['timeline']:
                frag += '\n' + gather(body, e)
        else:
            frag, h1 = gather(body, e), html.escape(e['title'])
        frag = unlink(frag)
        saved = json.dumps({'../' + k: v for k, v in saved_dates(frag).items()}, sort_keys=True, separators=(',', ':'))
        frag = rebase(frag)
        path = os.path.join(root, DIR, e['slug'] + '.html')
        wanted.add(e['slug'] + '.html')
        stamp = updated
        if os.path.exists(path):
            old = open(path, encoding='utf-8').read()
            m = STAMP.search(old)
            if m and content(old) == content(page(e, h1, frag, m.group(0).rstrip('\n'), saved, css, script)):
                stamp = m.group(0).rstrip('\n')
        new = page(e, h1, frag, stamp, saved, css, script)
        lastmods[e['slug']] = TIME.search(stamp).group(1)
        open(path, 'w', encoding='utf-8').write(new)
    for f in os.listdir(os.path.join(root, DIR)):
        if f.endswith('.html') and f not in wanted:
            os.remove(os.path.join(root, DIR, f))
    rows = ['<url><loc>%s</loc><lastmod>%s</lastmod></url>' % (BASE, stamp_iso),
            '<url><loc>%sgeert-greydanus-timeline.pdf</loc><lastmod>%s</lastmod></url>' % (BASE, stamp_iso)]
    rows += ['<url><loc>%s</loc><lastmod>%s</lastmod></url>' % (url(e['slug']), lastmods[e['slug']]) for e in PEOPLE]
    open(os.path.join(root, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n'
        % '\n'.join(rows))
