// Builds tools/sections/journey.html: an inline SVG map of Geert's journey, with a step-through
// timeline. Borders come from Natural Earth (via the world-atlas package) and are projected here,
// so the page needs no map tiles, fonts or scripts from elsewhere and works offline.
//
//   cd tools/map && npm install && npm run build
//
// Places and steps live in stops.json; edit that and rebuild.
import { readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { geoMercator, geoPath } from 'd3-geo';
import { feature } from 'topojson-client';

const require = createRequire(import.meta.url);
const here = new URL('.', import.meta.url);
const data = JSON.parse(readFileSync(new URL('stops.json', here)));
const world = require('world-atlas/countries-10m.json');

const W = 860, H = 500;
const [[x0, y0], [x1, y1]] = data.extent;
const frame = { type: 'MultiPoint', coordinates: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]] };
const projection = geoMercator().fitSize([W, H], frame).clipExtent([[0, 0], [W, H]]);
const path = geoPath(projection).digits(1);
const P = (lon, lat) => projection([lon, lat]).map(v => Math.round(v * 10) / 10);

const countries = feature(world, world.objects.countries).features;
const shown = { Netherlands: 'nl', Germany: 'de', Belgium: 'be', Luxembourg: 'lu', France: 'fr', Denmark: 'dk' };
const land = countries
  .filter(c => shown[c.properties.name])
  .map(c => `<path class="jm-land jm-${shown[c.properties.name]}" d="${path(c)}"/>`)
  .join('');
const countryLabels = [['NETHERLANDS', 5.55, 52.62], ['GERMANY', 9.0, 52.1], ['BELGIUM', 4.3, 50.75]]
  .map(([t, lon, lat]) => { const [x, y] = P(lon, lat); return `<text class="jm-country" x="${x}" y="${y}">${t}</text>`; })
  .join('');

const places = Object.fromEntries(Object.entries(data.places).map(([id, p]) => [id, { ...p, xy: P(p.lon, p.lat) }]));
const steps = data.steps.map(s => ({ ...s, xy: places[s.place].xy }));

// One leg per step after the first, from the previous step's place to this one's.
const legs = steps.map((s, i) => {
  if (i === 0) return '';
  const [ax, ay] = steps[i - 1].xy, [bx, by] = s.xy;
  if (ax === bx && ay === by) return `<path class="jm-leg" data-i="${i}" d=""/>`;
  // A gentle curve, so legs that retrace a road (Buchenwald and back) do not sit on top of each other.
  const mx = (ax + bx) / 2, my = (ay + by) / 2, dx = bx - ax, dy = by - ay, k = 0.12;
  const cx = Math.round(mx - dy * k), cy = Math.round(my + dx * k);
  return `<path class="jm-leg jm-${s.kind}" data-i="${i}" d="M${ax},${ay} Q${cx},${cy} ${bx},${by}"/>`;
}).join('');

// The last step leaves the map westward, toward Canada.
const [rx, ry] = places.rotterdam.xy;
const canada = `<g class="jm-canada" data-i="${steps.length - 1}"><path d="M${rx - 6},${ry} C${rx - 40},${ry - 10} ${rx - 70},${ry - 40} 8,${ry - 70}" />` +
  `<text x="12" y="${ry - 80}">To Canada, 1947 →</text></g>`;

const offsets = { left: [-9, 4, 'end'], right: [9, 4, 'start'], above: [0, -10, 'middle'], below: [0, 17, 'middle'] };
const dots = Object.entries(places).map(([id, p]) => {
  const [x, y] = p.xy, [dx, dy, anchor] = offsets[p.label];
  return `<g class="jm-place" data-place="${id}"><circle cx="${x}" cy="${y}" r="4.5"/>` +
    `<text x="${x + dx}" y="${y + dy}" text-anchor="${anchor}">${p.short || p.name}</text></g>`;
}).join('');
const context = data.context.map(c => {
  const [x, y] = P(c.lon, c.lat);
  return `<g class="jm-context"><circle cx="${x}" cy="${y}" r="2.5"/><text x="${x + 6}" y="${y + 4}">${c.name}${c.note ? ` (${c.note})` : ''}</text></g>`;
}).join('');

const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const list = steps.map((s, i) =>
  `<li data-i="${i}" class="jm-${s.kind}"><button type="button"><span class="jm-date">${esc(s.date)}</span>` +
  `<span class="jm-where">${esc(places[s.place].name)}</span></button><p>${esc(s.text)} <a href="#${s.anchor}">More</a></p></li>`).join('');

const stepData = JSON.stringify(steps.map(s => ({ p: s.place, xy: s.xy })));

const html = `<h2 id="geerts-journey-on-a-map">Geert’s journey on a map</h2>
<p>From the day he went into hiding to the day he left for Canada.<span class="jm-howto"> Press play, or pick any step to jump to it.</span></p>
<figure class="journey" aria-label="Map of Geert's journey">
<div class="jm-map">
<svg viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="jm-title"><title id="jm-title">${esc(data.title)}</title>
<rect class="jm-sea" width="${W}" height="${H}"/>${land}${countryLabels}${context}<g class="jm-legs">${legs}</g>${canada}${dots}
<g class="jm-marker"><circle r="11" class="jm-halo"/><circle r="6.5"/></g>
</svg>
<div class="jm-caption" aria-live="polite"><span class="jm-cap-date"></span> <span class="jm-cap-text"></span></div>
<div class="jm-controls">
<button type="button" class="jm-btn jm-prev" aria-label="Previous step">‹</button>
<button type="button" class="jm-btn jm-play" aria-label="Play">▶ Play</button>
<button type="button" class="jm-btn jm-next" aria-label="Next step">›</button>
<input class="jm-slider" type="range" min="0" max="${steps.length - 1}" value="0" aria-label="Step">
</div>
</div>
<ol class="jm-steps">${list}</ol>
<figcaption class="jm-note">${esc(data.note)} Borders are today’s, from Natural Earth.</figcaption>
</figure>
<style>
.journey{margin:24px 0 32px;display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:20px;font-family:var(--sans)}
.jm-map{position:sticky;top:12px;align-self:start;background:var(--card);border:1px solid var(--rule);border-radius:8px;overflow:hidden}
.jm-map svg{display:block;width:100%;height:auto}
.jm-sea{fill:var(--jm-sea)}
.jm-land{fill:var(--jm-land);stroke:var(--jm-border);stroke-width:.8}
.jm-nl{fill:var(--jm-nl)}
.jm-country{font:600 11px var(--sans);letter-spacing:.18em;fill:var(--muted);opacity:.7;text-anchor:middle}
.jm-context circle{fill:var(--muted);opacity:.6}.jm-context text{font:11px var(--sans);fill:var(--muted)}
.jm-leg{fill:none;stroke:var(--accent);stroke-width:2.5;stroke-linecap:round;opacity:0}
.jm-leg.jm-march{stroke-dasharray:2 5}
.jm-leg.on{opacity:1}
.jm-place circle{fill:var(--card);stroke:var(--muted);stroke-width:1.5}
.jm-place text{font:12px var(--sans);fill:var(--muted);paint-order:stroke;stroke:var(--jm-land);stroke-width:3px;stroke-linejoin:round}
.jm-place.seen circle{stroke:var(--accent);fill:var(--accent-soft)}
.jm-place.now circle{fill:var(--accent);stroke:var(--accent)}
.jm-place.now text{fill:var(--ink);font-weight:700}
.jm-marker{pointer-events:none;transition:transform .9s ease-in-out}
.jm-marker circle{fill:var(--accent)}.jm-marker .jm-halo{fill:var(--accent);opacity:.25}
.jm-canada{opacity:0;transition:opacity .6s}.jm-canada.on{opacity:1}
.jm-canada path{fill:none;stroke:var(--accent);stroke-width:2.5;stroke-dasharray:6 5}
.jm-canada text{font:700 13px var(--sans);fill:var(--accent)}
.jm-caption{padding:10px 14px;border-top:1px solid var(--rule);font-size:15px;line-height:1.45;min-height:3.4em}
.jm-cap-date{font-weight:700;color:var(--accent)}
.jm-controls{display:flex;align-items:center;gap:8px;padding:0 14px 12px}
.jm-btn{font:600 14px var(--sans);border:1px solid var(--accent);background:transparent;color:var(--accent);border-radius:6px;padding:6px 12px;cursor:pointer}
.jm-play{background:var(--accent);color:var(--paper);min-width:6.5em}
.jm-slider{flex:1;accent-color:var(--accent);min-width:0}
.jm-steps{list-style:none;margin:0;padding:0;max-height:640px;overflow:auto}
.jm-steps li{margin:0;border-left:3px solid var(--rule);padding:2px 0 10px 12px}
.jm-steps button{all:unset;cursor:pointer;display:block}
.jm-steps button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.jm-date{display:block;font:700 13px var(--sans);color:var(--muted)}
.jm-where{display:block;font:600 15px var(--sans);color:var(--ink)}
.jm-steps p{display:none;margin:4px 0 0;font-size:14px;line-height:1.45;color:var(--ink)}
.jm-steps li.now{border-left-color:var(--accent)}
.jm-steps li.now .jm-date{color:var(--accent)}
.jm-steps li.now p{display:block}
.jm-note{grid-column:1/-1;font-size:13px;color:var(--muted)}
:root{--jm-sea:#dfe8ec;--jm-land:#f4efe4;--jm-nl:#ece3d0;--jm-border:#c9bfae}
@media (prefers-color-scheme:dark){:root{--jm-sea:#1c2428;--jm-land:#2b2723;--jm-nl:#35302a;--jm-border:#4a433b}}
@media (max-width:900px){.journey{display:block}.jm-map{position:static}.jm-steps{max-height:none;margin-top:16px}}
@media (prefers-reduced-motion:reduce){.jm-marker,.jm-canada{transition:none}}
@media print{.jm-controls,.jm-caption,.jm-howto,.jm-marker{display:none}.jm-map{position:static}.jm-steps{max-height:none}.jm-steps p{display:block}.jm-leg{opacity:1;stroke-dashoffset:0!important}.jm-canada{opacity:1}.journey{display:block}}
</style>
<script>
(function(){
var root=document.querySelector('.journey');if(!root)return;
var steps=${stepData};
var legs=[].slice.call(root.querySelectorAll('.jm-leg')),items=[].slice.call(root.querySelectorAll('.jm-steps li'));
var marker=root.querySelector('.jm-marker'),slider=root.querySelector('.jm-slider'),play=root.querySelector('.jm-play');
var capDate=root.querySelector('.jm-cap-date'),capText=root.querySelector('.jm-cap-text'),canada=root.querySelector('.jm-canada');
var reduce=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
legs.forEach(function(l){var n=l.getTotalLength?l.getTotalLength():0;l._n=n;if(!l.classList.contains('jm-march')&&n){l.style.strokeDasharray=n;l.style.strokeDashoffset=n;}});
var cur=-1,timer=null;
function show(i,animate){
  i=Math.max(0,Math.min(steps.length-1,i));
  legs.forEach(function(l){var k=+l.getAttribute('data-i');var on=k<=i;l.classList.toggle('on',on);
    if(l._n&&!l.classList.contains('jm-march')){l.style.transition=(animate&&k===i&&!reduce)?'stroke-dashoffset .9s ease-in-out':'none';l.style.strokeDashoffset=on?0:l._n;}});
  canada.classList.toggle('on',i===steps.length-1);
  var seen={};for(var k=0;k<=i;k++)seen[steps[k].p]=1;
  [].forEach.call(root.querySelectorAll('.jm-place'),function(g){var p=g.getAttribute('data-place');g.classList.toggle('seen',!!seen[p]);g.classList.toggle('now',p===steps[i].p);});
  marker.style.transition=(animate&&!reduce)?'':'none';
  marker.setAttribute('transform','translate('+steps[i].xy[0]+','+steps[i].xy[1]+')');marker.style.transform='translate('+steps[i].xy[0]+'px,'+steps[i].xy[1]+'px)';
  items.forEach(function(li,k){li.classList.toggle('now',k===i)});
  var li=items[i];capDate.textContent=li.querySelector('.jm-date').textContent;capText.textContent=li.querySelector('p').firstChild.textContent;
  slider.value=i;cur=i;
}
function stop(){if(timer){clearInterval(timer);timer=null;}play.textContent='▶ Play';play.setAttribute('aria-label','Play');}
function start(){if(cur>=steps.length-1)show(0,false);play.textContent='❚❚ Pause';play.setAttribute('aria-label','Pause');
  timer=setInterval(function(){if(cur>=steps.length-1){stop();return;}show(cur+1,true);},2600);}
play.addEventListener('click',function(){timer?stop():start();});
root.querySelector('.jm-prev').addEventListener('click',function(){stop();show(cur-1,true);});
root.querySelector('.jm-next').addEventListener('click',function(){stop();show(cur+1,true);});
slider.addEventListener('input',function(){stop();show(+slider.value,true);});
items.forEach(function(li,k){li.querySelector('button').addEventListener('click',function(){stop();show(k,true);});});
show(0,false);
})();
</script>`;

writeFileSync(new URL('../sections/journey.html', here), html + '\n');
console.log('wrote tools/sections/journey.html', html.length, 'bytes');
