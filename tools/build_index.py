import json,re,html,os,sys,base64,urllib.parse as up
exp=sys.argv[1]; out=sys.argv[2]
d=json.load(open(exp)); t=[x['text'] for x in d if '"bytes_b64"' in x['text']][0]
m=re.search(r'"bytes_b64"\s*:\s*"([^"]+)"',t); rev=re.search(r'"rev"\s*:\s*(\d+)',t)
h=base64.b64decode(m.group(1)).decode()
dm=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'drive_map.json')))
local={k:'drive/'+os.path.basename(v) for k,v in dm.items()}
local.update({'1J4Qqlhn9Kf_VPsKlXljRWZ_DPJoWK6Pm':'drive/1.jpg','1HN1k88ytG7V3RbE_MFt1JPycGMZrsnmd':'drive/5.jpg','1JJFEBC8yi2yCAVgRH_y6ZmabRaB74H2w':'drive/6.jpg',
 '1JDShKBqkb2GczcMofIDSv1NTgxmuh59y':'drive/1JDShKBqkb_form-p4.jpg','1JHnKX24O-aE812_OlVVBDZZKxxMmED_B':'drive/1JHnKX24O-_5.jpg'})
nara={'286685637':'Satter_Hendrik','286685646':'Satter_Johannes','286685701':'Schaap_Anne','286697307':'vanBraak_TheodoorChristiaan','286672718':'LoweyBall_JohnJames',
 '286712299':'vanWijngaarden_Lucas','286689024':'Slotboom_GC','286659333':'Helmink_Willem','286661150':'Hofs_GH','286667652':'Knottnerus_RB','286670537':'Lammers_Dien',
 '286657435':'Gussinklo_GW','286671112':'Leemreize_HJA','286702134':'vanderHooft_CorneliusAdriana'}
web={'greydanus.blogspot.com/p/aan-de-wieg-van-een-yerzetskrantwilllem.html':'geertweb__blogspot_aan-de-wieg-trouw-2014.html',
'joodsmonument.nl/en/page/471746/isaac-leo-palache':'geertweb__joodsmonument_isaac-leo-palache.html','micode=249-0225':'geertweb__niod_249-0225-executie-varsseveld.html',
'mizk_alle=Greydanus&micode=250m':'geertweb__niod_250m-greydanus.html','micode=251a&minr=1505414':'geertweb__niod_251a-inv7-lo-friesland.html',
'miview=lst&milang=nl&mizk_alle=Greidanus':'geertweb__niod_search-greidanus.html','miview=lst&milang=nl&mizk_alle=Greydanus':'geertweb__niod_search-greydanus.html',
'stigter-jacob':'geertweb__nmkampvught_stigter-jacob.html','93f49057-f62c':'geertweb__oorlogsbronnen_geert-greijdanus.html','e76c8a62-9529':'geertweb__oorlogsbronnen_jacob-greydanus.html',
'7f437a75-b35d':'geertweb__oorlogsbronnen_johannes-antonius-schepen.html','799BBD5E804C41F3A8426BD307D72E88':'geertweb__oorlogsbronnen_ovcg-card-schepen.html',
'8e23c53a-4d88':'geertweb__oorlogsbronnen_theodoor-van-braak.html','134708/hendrik-satter':'geertweb__oorlogsgravenstichting_hendrik-satter.html',
'53320/jacob-greydanus':'geertweb__oorlogsgravenstichting_jacob-greydanus.html','timesofisrael.com/how-a-volunteer':'geertweb__timesofisrael_fire-brigade-leo-palache.html',
'catalog/irn516733':'geertweb__ushmm_irn516733.html','catalog/irn713250':'geertweb__ushmm_irn713250.html','catalog/vha4503':'geertweb__ushmm_vha4503-leo-palache.html',
'wiki/Joop_Westerweel':'geertweb__wikipedia_joop-westerweel.html','wiki/Juda_Lion_Palache':'geertweb__wikipedia_juda-lion-palache.html','righteous/8067103':'geertweb__yadvashem_baron-8067103.html'}
src={'DDD_010448593':'ddd_010448593.pdf','ddd:010448593':'ddd_010448593.pdf','RG-50.030.0494':'RG-50.030.0494_trs_en.pdf','Necrologie-II-617-642':'Necrologie-II-617-642.pdf',
'HGGI-H2-465-477':'HGGI-H2-465-477.pdf','HGGI-H2-478-485':'HGGI-H2-478-485.pdf','bcrfj/3022':'bcrfj-3022.pdf','bcrfj/pdf/3022':'bcrfj-3022.pdf',
'aan-de-wieg-van-een-verzetskrant':'At the cradle of a resistance newspaper _ Trouw.pdf','de-waarheid-bleef-liggen':'THE TRUTH REMAINED UNDER A ROOF TILE _ Trouw.pdf',
'museum-zwangsarbeit':'Niederorschel_Englisch_museum-zwangsarbeit.pdf'}
reasons={'arolsen':'online only: Arolsen card images not bundled','nl.wikipedia':'online only: domain not reachable when archiving','jolink':'online only: domain not reachable',
'eindhoven4044':'online only: domain not reachable','holocaust.cz':'online only: domain not reachable','officielebekendmakingen':'online only: domain not reachable',
'resourcessgd':'online only: link returns "not found"','stiftung-gedenkstaetten':'online only: download blocked','amazon':'online only: book listing',
'micode=528':'online only: not snapshotted','mizig=435':'online only: not snapshotted','oorlogsbronnen.nl/bronnen':'online only: search page','zoeken?term':'online only: search page',
'eerebegraafplaats':'online only: not snapshotted','wikiclud1':'online only: not snapshotted','ushmm.org/remember':'online only: not snapshotted',
'greydanus.blogspot.com/':'online only: blog home page','docs.google.com':'online only: Google Doc (text export in drive/ where present)','drive.google':'online only: Drive folder','archive/1-1-5-3':'online only'}
def resolve(u):
  m=re.search(r'catalog\.archives\.gov/id/(\d+)',u)
  if m and m.group(1) in nara: return 'sources/nara_helper_files/NARA_helperfile_%s.pdf'%nara[m.group(1)]
  m=re.search(r'studiegroepluchtoorlog.*enummer=(E\d+)',u)
  if m: return 'web/geertweb__sglo_evaders.html#'+m.group(1)
  m=re.search(r'/d/([A-Za-z0-9_-]{20,})|id=([A-Za-z0-9_-]{20,})',u)
  if m:
    i=next(g for g in m.groups() if g)
    if i in local: return local[i]
  for k,v in src.items():
    if k in u: return 'sources/'+v
  for k,v in web.items():
    if k in u: return 'web/'+v
  return None
rows=[];seen=set()
def q(l): p,_,f=l.partition('#'); return up.quote(p)+('#'+f if f else '')
def rep(m):
  u=html.unescape(m.group(1)); l=resolve(u)
  if u not in seen:
    seen.add(u); rows.append((u,l,next((v for k,v in reasons.items() if k in u),'online only')))
  return 'href="%s" data-original="%s"'%(html.escape(q(l)),html.escape(u)) if l else m.group(0)
h2=re.sub(r'href="([^"]+)"',rep,h)
tbl=''.join('<tr><td><a href="%s">%s</a></td><td>%s</td></tr>'%(html.escape(q(l) if l else u),html.escape(u),('<a href="%s">%s</a>'%(html.escape(q(l)),html.escape(l))) if l else html.escape(r)) for u,l,r in rows)
r=rev.group(1) if rev else '?'
banner='<div style="border:1px solid #999;padding:12px;margin:12px 0;font-family:sans-serif;background:#f6f4ef"><b>Offline archive copy.</b> Built from the Claude Doc <i>Geert Greydanus — Timeline from the Family Papers</i> (rev %s). Links to archived files open the local copy in <code>drive/</code>, <code>sources/</code> or <code>web/</code>; the original URL is kept in each link\'s <code>data-original</code> attribute. Other links still go online. <a href="#archive-sources">Source index</a>.</div>'%r
extra='<li><a href="sources/YadVashem_JeroensVersion.pdf">sources/YadVashem_JeroensVersion.pdf</a>: Jurjen Hoekstra\'s 2020 Yad Vashem proposal</li><li><a href="sources/nara_helper_files/">sources/nara_helper_files/</a>: US Army helper files (NARA RG 498, series 5709392). The four largest were re-rendered at 110 dpi to stay under GitHub\'s file-size limit; originals are at catalog.archives.gov.</li>'
app='<h2 id="archive-sources">Archive source index</h2><p>Every link in the timeline, with the local copy or the reason there is none.</p><table border="1" cellpadding="4" style="border-collapse:collapse;font-size:13px"><tr><th>Original link</th><th>Local copy</th></tr>'+tbl+'</table><h3>Other files in this archive</h3><ul>'+extra+'</ul>'
h2=re.sub(r'(<body[^>]*>)',lambda mm:mm.group(1)+banner,h2,count=1) if '<body' in h2 else banner+h2
h2=h2.replace('</body>',app+'</body>') if '</body>' in h2 else h2+app
open(out,'w').write(h2)
print('rev',r,len(rows),'links;',sum(1 for x in rows if x[1]),'local')
print('\n'.join(sorted(set(x[1] for x in rows if x[1]))))
