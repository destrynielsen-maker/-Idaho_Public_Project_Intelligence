from __future__ import annotations

from pathlib import Path


HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Idaho Public Project Intelligence</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#111b2e;--line:#26344d;--text:#e7edf7;--muted:#9fb0c8;--accent:#7dd3fc}
*{box-sizing:border-box} body{margin:0;font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;background:var(--bg);color:var(--text)}
main{max-width:1600px;margin:auto;padding:24px} h1{font-size:28px;margin:0 0 4px}.sub{color:var(--muted);margin-bottom:18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:14px 0}.card{background:var(--panel);border:1px solid var(--line);padding:14px;border-radius:10px}.num{font-size:24px;font-weight:700}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}.filters input,.filters select{background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:8px;padding:9px}
.feeds{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0 18px}.feeds a{color:var(--accent);text-decoration:none;border:1px solid var(--line);padding:6px 9px;border-radius:999px}
.wrap{overflow:auto;border:1px solid var(--line);border-radius:10px}table{width:100%;border-collapse:collapse;min-width:1250px;background:var(--panel)}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}th{position:sticky;top:0;background:#17243a;text-align:left;cursor:pointer;white-space:nowrap}
td.score{font-weight:800;font-size:16px}a{color:var(--accent)}.muted{color:var(--muted)}.pill{display:inline-block;padding:2px 7px;border:1px solid var(--line);border-radius:999px;font-size:12px}
footer{color:var(--muted);padding:18px 0}
</style>
</head>
<body><main>
<h1>Idaho Public Project Intelligence</h1>
<div class="sub">State, city and Treasure Valley construction/procurement opportunities. Click a header to sort.</div>
<div class="cards" id="cards"></div>
<div class="filters">
<input id="q" placeholder="Search project, agency, location…" size="34">
<select id="source"><option value="">All sources</option></select>
<select id="stage"><option value="">All stages</option></select>
<select id="category"><option value="">All categories</option></select>
<select id="score"><option value="0">Any score</option><option>40</option><option>60</option><option>80</option></select>
</div>
<div class="feeds">
<a href="feeds/all-public-projects.xml">All opportunities RSS</a>
<a href="feeds/treasure-valley.xml">Treasure Valley</a>
<a href="feeds/construction.xml">Construction</a>
<a href="feeds/building-projects.xml">Building projects</a>
<a href="feeds/materials-equipment.xml">Materials & equipment</a>
<a href="feeds/design-rfq.xml">Design / RFQ</a>
<a href="feeds/closing-14-days.xml">Closing 14 days</a>
<a href="feeds/new-this-week.xml">New this week</a>
<a href="feeds/awards.xml">Awards / bid results</a>
<a href="feeds/early-opportunities.xml">Early opportunities</a>
</div>
<div class="wrap"><table><thead><tr>
<th data-k="score">Score</th><th data-k="due_date">Due</th><th data-k="agency">Agency</th><th data-k="location">Location</th>
<th data-k="stage">Stage</th><th data-k="solicitation_type">Type</th><th data-k="solicitation_number">Number</th>
<th data-k="title">Project</th><th data-k="category">Category</th><th data-k="first_seen">First seen</th>
</tr></thead><tbody id="rows"></tbody></table></div>
<footer id="generated"></footer>
<script>
let data=[], sortKey='score', sortDir=-1;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const uniq=k=>[...new Set(data.map(x=>x[k]).filter(Boolean))].sort();
function options(id,k){const el=document.getElementById(id); uniq(k).forEach(v=>el.insertAdjacentHTML('beforeend',`<option>${esc(v)}</option>`))}
function active(r){return !['CLOSED','BID_RESULTS','AWARDED'].includes(r.stage)}
function render(){
 const q=document.getElementById('q').value.toLowerCase(), src=document.getElementById('source').value, st=document.getElementById('stage').value, cat=document.getElementById('category').value, min=+document.getElementById('score').value;
 let rows=data.filter(r=>(!src||r.source===src)&&(!st||r.stage===st)&&(!cat||r.category===cat)&&(r.score||0)>=min&&(!q||JSON.stringify(r).toLowerCase().includes(q)));
 rows.sort((a,b)=>{let x=a[sortKey]??'',y=b[sortKey]??''; if(typeof x==='number')return (x-y)*sortDir; return String(x).localeCompare(String(y))*sortDir});
 document.getElementById('rows').innerHTML=rows.map(r=>`<tr>
 <td class="score">${r.score||0}</td><td>${esc(r.due_date||'TBD')}</td><td>${esc(r.agency)}</td><td>${esc(r.location)}</td>
 <td><span class="pill">${esc(r.stage)}</span></td><td>${esc(r.solicitation_type)}</td><td>${esc(r.solicitation_number)}</td>
 <td><a target="_blank" rel="noopener" href="${esc(r.url||'#')}">${esc(r.title)}</a><div class="muted">${esc((r.description||'').slice(0,220))}</div></td>
 <td>${esc(r.category)}</td><td>${esc((r.first_seen||'').slice(0,10))}</td></tr>`).join('');
}
fetch('data/opportunities.json').then(r=>r.json()).then(p=>{
 data=p.opportunities||[]; options('source','source');options('stage','stage');options('category','category');
 const open=data.filter(active), tv=open.filter(r=>/boise|meridian|nampa|caldwell|eagle|kuna|star|ada county/i.test((r.location||'')+' '+(r.title||'')));
 const build=open.filter(r=>r.category==='BUILDING'), early=open.filter(r=>['FUTURE','UPCOMING','DESIGN_RFQ','DESIGN_RFP'].includes(r.stage));
 document.getElementById('cards').innerHTML=`<div class="card"><div class="num">${open.length}</div>Active opportunities</div><div class="card"><div class="num">${tv.length}</div>Treasure Valley</div><div class="card"><div class="num">${build.length}</div>Building / facility</div><div class="card"><div class="num">${early.length}</div>Early / future</div>`;
 document.getElementById('generated').textContent='Generated '+(p.generated_at||'');
 render();
});
['q','source','stage','category','score'].forEach(id=>document.getElementById(id).addEventListener('input',render));
document.querySelectorAll('th[data-k]').forEach(th=>th.addEventListener('click',()=>{if(sortKey===th.dataset.k)sortDir*=-1;else{sortKey=th.dataset.k;sortDir=sortKey==='score'?-1:1}render()}));
</script></main></body></html>'''


def write(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HTML, encoding="utf-8")
