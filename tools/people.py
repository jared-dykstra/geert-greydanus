"""Separate pages for the key people in Geert's story, and the sitemap.

Each page in PEOPLE is cut from the laid-out index.html: the section under the heading with the given
id, up to the next heading of the same or higher level. So a page always says what the timeline says;
edit the timeline, never the files in people/. tools/page.py calls build() after it lays out index.html.

A page gets its own title, description and structured data, so a search for that person's name can
find it. Its "Last updated" stamp changes only when its text changes, and the sitemap's <lastmod>
follows the stamps.
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


# slug, heading id, page title (None: the heading's own text), description, people the page is about.
# Dates and places are only those the section states; where its sources disagree, the field is left out.
PEOPLE = [
    ('willy-markus', 'the-betrayal-willy-markus', 'Willy Markus, the SD informer who betrayed the Achterhoek resistance (1944)',
     'Willem (Willy) Markus, the Arnhem café owner turned SD informer whose betrayal led to the arrests of 20 April 1944 '
     'in the Achterhoek, among them Geert Greydanus and Hendrik Satter.',
     [person('Willem Markus', ['Willy Markus'], '1902-03-24', 'Ambt Doetinchem', '1978-03-24', 'Enschede')]),
    ('kurt-gerstein', 'the-gerstein-report-in-the-chicken-coop', 'Kurt Gerstein and the Gerstein report in the Satter chicken coop',
     "How Kurt Gerstein's account of the gas chambers reached the Satter farm near Sinderen, where Geert Greydanus hid, "
     'and was found under a roof tile of the chicken coop after the war.',
     [person('Kurt Gerstein', (), '1905-08-11', 'Münster', '1945-07-25', 'Paris')]),
    ('willem-arnold-rohaan', 'willem-arnold-rohaan', None,
     'Willem Arnold Rohaan of Neede, farmer and deputy commander of the local Ordedienst, arrested after the betrayal by '
     'Willy Markus, held in Kamp Vught with Geert Greydanus and shot at Overveen on 6 June 1944.',
     [person('Willem Arnold Rohaan', (), '1912-10-26', 'Neede', '1944-06-06', 'Overveen')]),
    ('hendrik-pieter-heinen', 'hendrik-pieter-heinen', None,
     'Hendrik Pieter (Henk) Heinen of Eibergen, printer of the underground paper Trouw, arrested through Willy Markus on '
     '20 April 1944, held in Kamp Vught with Geert Greydanus and shot at Overveen on 6 June 1944.',
     [person('Hendrik Pieter Heinen', ['Henk Heinen'], '1914-11-28', 'Eibergen', '1944-06-06', 'Overveen')]),
    ('martinus-antonius-lelivelt', 'martinus-antonius-lelivelt', None,
     'Martinus Antonius (Martin) Lelivelt, Lichtenvoorde builder who hid Jews, onderduikers and airmen, held in Kamp '
     'Vught with Geert Greydanus and shot at Fort Rhijnauwen on 25 July 1944.',
     [person('Martinus Antonius Lelivelt', ['Martin Lelivelt'], '1896-01-17', 'Lichtenvoorde', '1944-07-25', 'Fort Rhijnauwen')]),
    ('teunis-klaas-wortman', 'teunis-klaas-wortman', None,
     'Teunis Klaas Wortman, opperwachtmeester der marechaussee at Neede, held in Kamp Vught with Geert Greydanus and '
     'shot at Overveen on 6 June 1944.',
     [person('Teunis Klaas Wortman', (), '1911-11-27', 'Geldermalsen', '1944-06-06', 'Overveen')]),
    ('cornelis-coenraad-poulie', 'cornelis-coenraad-poulie', None,
     'Cornelis Coenraad (Kees) Poulie, the Varsseveld marechaussee who brought an Allied airman to the Satter farm, held '
     'in Kamp Vught with Geert Greydanus and shot at Overveen on 6 June 1944, aged 24.',
     [person('Cornelis Coenraad Poulie', ['Kees Poulie'], '1919-07-05', 'Den Helder', '1944-06-06', 'Overveen')]),
    ('albertus-hendrikus-marcusse', 'albertus-hendrikus-marcusse', None,
     'Albertus Hendrikus (Albert) Marcusse, chief detective of the Nijmegen police and member of its resistance group, '
     'held in Kamp Vught with Geert Greydanus and shot at Overveen on 6 June 1944.',
     [person('Albertus Hendrikus Marcusse', ['Albert Marcusse'], '1903-11-02', 'Batenburg', '1944-06-06', 'Overveen')]),
    ('gerrit-jan-van-den-boogerd', 'gerrit-jan-van-den-boogerd', None,
     'Gerrit Jan van den Boogerd ("Oom Gert"), candidaat-notaris and resistance leader deceived by Willy Markus, '
     'arrested in Zutphen on 20 April 1944 and shot at Fort Rhijnauwen on 25 July 1944.',
     [person('Gerrit Jan van den Boogerd', ['Oom Gert'], '1908-08-22', 'Zwartewaal', '1944-07-25', 'Fort Rhijnauwen')]),
    ('willem-en-jacobus-westland', 'willem-en-jacobus-westland', None,
     'The brothers Willem and Jacobus Westland, owners of the Oranje hotel and the Luxor cinema in Wageningen, held in '
     'Kamp Vught with Geert Greydanus and shot at Overveen on 6 June 1944.',
     [person('Willem Westland', (), '1900-04-08', 'Wageningen', '1944-06-06', 'Overveen'),
      person('Jacobus Westland', (), None, 'Wageningen', '1944-06-06', 'Overveen')]),
    ('johannes-berlijn', 'johannes-berlijn', None,
     'Johannes (Jo) Berlijn, Rotterdam trader and forger for the LO, whose house was Geert Greydanus\'s first hiding '
     'place in April 1943; killed in Kamp Vught on 30 August 1944.',
     [person('Johannes Berlijn', ['Jo Berlijn'], '1906-02-16', 'Rotterdam', '1944-08-30', 'Kamp Vught')]),
    ('johan-gerard-westerweel', 'johan-gerard-westerweel', None,
     'Johan Gerard (Joop) Westerweel, head of the Montessori school in Rotterdam who helped Jews escape to Spain, held '
     'in the Vught bunker with Geert Greydanus and shot there on 11 August 1944.',
     [person('Johan Gerard Westerweel', ['Joop Westerweel'], None, 'Zutphen', '1944-08-11', 'Kamp Vught')]),
    ('karel-roelof-verschuur', 'carel-verschuur', None,
     'Karel Roelof Verschuur, a painter from Wageningen, the one Karel known to have been in the Vught bunker in June '
     '1944, where Geert Greydanus remembered a "Karel" in the next cell; shot at Overveen on 6 June 1944.',
     [person('Karel Roelof Verschuur', ['Carel Verschuur'], '1919-04-15', 'Wageningen', '1944-06-06', 'Overveen')]),
    ('eemke-van-der-veen', 'eemke-van-der-veen', None,
     'Eemke van der Veen, town-hall clerk in Haren, possibly Geert Greydanus\'s cellmate in Kamp Vught; arrested on '
     '2 May 1944 for supplying identity papers and shot in Kamp Vught on 22 August 1944.',
     [person('Eemke van der Veen', (), '1902-06-05', 'Nieuweschans', '1944-08-22', 'Kamp Vught')]),
    ('aaron-akker', 'aaron-akker', None,
     'Aaron Akker of Leeuwarden, one of the Dutch Jews with Geert Greydanus at Niederorschel, who died during the death '
     'march to Buchenwald in April 1945.',
     [person('Aaron Akker', (), '1895-11-24', 'Sneek', '1945-04-06', 'Buchenwald')]),
    ('johannes-antonius-schepen', 'johannes-antonius-anton-schepen-the-third-man',
     'Johannes Antonius (Anton) Schepen (Joure, 1899 – 1984), with Geert Greydanus at Niederorschel',
     'Johannes Antonius (Anton) Schepen, electrician of Groningen, the only other Dutchman in Geert Greydanus\'s '
     'Niederorschel group, and a witness to the death march of April 1945.',
     [person('Johannes Antonius Schepen', ['Anton Schepen'], '1899-11-09', 'Joure', '1984-10-02')]),
]

STAMP = re.compile(r'<p class="updated">.*?</p>\n?')


def url(slug):
    return '%s%s/%s.html' % (BASE, DIR, slug)


def mentions():
    """The people with pages, for the main page's structured data."""
    out = []
    for slug, _, _, _, people in PEOPLE:
        for p in people:
            out.append(dict(p, url=url(slug)))
    return out


def cut(body, hid):
    m = re.search(r'<h([2-6]) id="%s"[^>]*>(.*?)</h\1>' % re.escape(hid), body, flags=re.S)
    if not m:
        raise SystemExit('people.py: no heading with id "%s"' % hid)
    level = int(m.group(1))
    end = re.compile(r'<h[2-%d][ >]' % level).search(body, m.end())
    frag = body[m.end():end.start() if end else len(body)]
    frag = re.sub(r'<!--.*?-->\n?', '', frag, flags=re.S).strip()
    # The cut heading becomes the page's h1; what was under it moves up to h2.
    frag = re.sub(r'<(/?)h([2-6])', lambda t: '<%sh%d' % (t.group(1), max(2, int(t.group(2)) - level + 1)), frag)
    return m.group(2), frag


def rebase(frag):
    """Point the cut section's links at the right place from people/: local files one folder up, and
    links into the rest of the timeline at index.html."""
    ids = set(re.findall(r'\sid="([^"]+)"', frag))
    def one(m):
        attr, v = m.group(1), m.group(2)
        if v.startswith('#'):
            return m.group(0) if v[1:] in ids else '%s="../index.html%s"' % (attr, v)
        if re.match(r'[a-z][a-z0-9+.-]*:', v, re.I) or v.startswith('//'):
            return m.group(0)
        return '%s="../%s"' % (attr, v)
    return re.sub(r'(?<![\w-])(href|src)="([^"]*)"', one, frag)


def links_list(current=None, prefix=''):
    items = []
    for slug, hid, title, _, people in PEOPLE:
        name = ' and '.join(p['name'] for p in people) if len(people) < 3 else people[0]['name']
        if slug == current:
            continue
        items.append('<a href="%s%s.html">%s</a>' % (prefix, slug, html.escape(name)))
    return ', '.join(items)


def page(slug, title, desc, people, heading, frag, updated, saved, css, script):
    h1 = title and html.escape(title) or heading
    plain = html.unescape(re.sub(r'<[^>]+>', '', h1))
    ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': plain, 'url': url(slug),
          'inLanguage': 'en', 'description': desc, 'author': {'@type': 'Person', 'name': 'Jared Dykstra'},
          'license': 'https://creativecommons.org/licenses/by/4.0/',
          'isPartOf': {'@type': 'Article', 'headline': 'Geert Greydanus (1899–1965): a timeline from the family papers',
                       'url': BASE},
          'about': people[0] if len(people) == 1 else people}
    e = lambda s: html.escape(s, quote=True)
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
<p>This page is one section of <a href="../index.html"><em>Geert Greydanus (1899–1965): a timeline from the family papers</em></a>, shown on its own. Geert Greydanus was a Rotterdam police detective who went into hiding in 1943, helped Allied airmen in the Achterhoek, and survived Kamp Vught, Buchenwald and Niederorschel. Wherever a source was saved, its link offers the original or the copy saved in this archive.</p>
<p>Other people in the timeline: {others}.</p>
<p>The timeline text is licensed under <a href="https://creativecommons.org/licenses/by/4.0/" rel="license">CC BY 4.0</a>, with credit to Jared Dykstra. The family papers and the saved copies of other people&rsquo;s work are not covered by this license (<a href="https://github.com/jared-dykstra/geert-greydanus#license">details</a>).</p>
</section>
</main>
</div>
<script>window.SAVED={saved};</script>
{script}
</body>
</html>
""".format(t=e(plain), d=e(desc), dh=html.escape(desc), u=url(slug), h1=h1, frag=frag, updated=updated, css=css,
           ld=json.dumps(ld, ensure_ascii=False, separators=(',', ':')), others=links_list(slug), saved=saved,
           script=script)


def build(root, body, updated, now, css, script, saved_dates):
    """Write people/*.html and sitemap.xml."""
    os.makedirs(os.path.join(root, DIR), exist_ok=True)
    stamp_iso = now.strftime('%Y-%m-%dT%H:%MZ')
    lastmods, wanted = {}, set()
    for slug, hid, title, desc, people in PEOPLE:
        heading, frag = cut(body, hid)
        saved = json.dumps({'../' + k: v for k, v in saved_dates(frag).items()}, sort_keys=True, separators=(',', ':'))
        frag = rebase(frag)
        path = os.path.join(root, DIR, slug + '.html')
        wanted.add(slug + '.html')
        new = page(slug, title, desc, people, heading, frag, updated, saved, css, script)
        lastmods[slug] = stamp_iso
        if os.path.exists(path):
            old = open(path, encoding='utf-8').read()
            if STAMP.sub('', old) == STAMP.sub('', new):
                new = old
                m = re.search(r'<time datetime="([^"]+)"', old)
                lastmods[slug] = m.group(1) if m else stamp_iso
        open(path, 'w', encoding='utf-8').write(new)
    for f in os.listdir(os.path.join(root, DIR)):
        if f.endswith('.html') and f not in wanted:
            os.remove(os.path.join(root, DIR, f))
    rows = ['<url><loc>%s</loc><lastmod>%s</lastmod></url>' % (BASE, stamp_iso),
            '<url><loc>%sgeert-greydanus-timeline.pdf</loc><lastmod>%s</lastmod></url>' % (BASE, stamp_iso)]
    rows += ['<url><loc>%s</loc><lastmod>%s</lastmod></url>' % (url(s), lastmods[s]) for s, *_ in PEOPLE]
    open(os.path.join(root, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n'
        % '\n'.join(rows))
