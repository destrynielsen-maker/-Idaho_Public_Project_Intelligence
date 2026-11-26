from __future__ import annotations

from pathlib import Path


HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Idaho Public Project Intelligence</title>
<style>
:root{font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#172033;background:#f5f7fb;--ink:#172033;--muted:#667085;--line:#e1e6ef;--blue:#175cd3;--green:#067647;--red:#b42318}
*{box-sizing:border-box}body{margin:0;background:#f5f7fb;color:var(--ink)}
header{background:#172033;color:#fff;padding:28px max(20px,calc((100vw - 1580px)/2))}header h1{margin:0 0 6px;font-size:28px}header p{margin:0;opacity:.82}
main{max-width:1580px;margin:0 auto;padding:22px}.cards{display:grid;grid-template-columns:repeat(5,minmax(150px,1fr));gap:12px;margin-bottom:18px}.card,.panel{background:#fff;border:1px solid var(--line);border-radius:12px;box-shadow:0 1px 2px rgba(0,0,0,.03)}.card{padding:16px}.label{color:var(--muted);font-size:13px}.value{font-size:25px;font-weight:700;margin-top:6px}
.panel{padding:16px;margin-bottom:16px}.panel-title{display:flex;justify-content:space-between;gap:12px;align-items:end;flex-wrap:wrap;margin-bottom:10px}.muted{color:var(--muted)}
.filters{display:grid;grid-template-columns:2fr repeat(5,minmax(120px,.8fr));gap:10px}.date-filters{display:grid;grid-template-columns:1fr 1fr 1fr 1fr auto;gap:10px;margin-top:10px}input,select,button{width:100%;padding:9px 10px;border:1px solid #cfd6e2;border-radius:8px;background:#fff;color:var(--ink);font:inherit}button{cursor:pointer;width:auto;white-space:nowrap}button:hover{background:#f8fafc}
.source-health{display:flex;flex-wrap:wrap;gap:8px;margin:.6rem 0 0;padding:0;list-style:none}.source-health li{border:1px solid var(--line);border-radius:8px;padding:7px 10px}.row-evidence{white-space:normal;max-width:200px;font-size:12px;margin-top:3px}.pagination{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;margin:12px 0 0}.pagination button,.pagination select,.report-actions button{min-height:44px;touch-action:manipulation}.pagination select{width:auto}.pagination-summary{min-width:8rem}.feeds{display:flex;flex-wrap:wrap;gap:8px}.feeds a{text-decoration:none;border:1px solid #cfd6e2;border-radius:999px;padding:7px 11px;color:var(--ink);background:#fff}.feeds a:hover{border-color:#98a2b3}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:10px}table{width:100%;border-collapse:collapse;font-size:13px;min-width:1550px}th{position:sticky;top:0;background:#f8fafc;text-align:left;color:var(--muted);border-bottom:1px solid #dfe5ee;padding:10px 8px;white-space:nowrap;z-index:1}th.sortable{cursor:pointer;user-select:none}th.sortable:hover{color:var(--ink);background:#eef2f7}th.sortable.active{color:var(--ink)}.sort-arrow{display:inline-block;width:14px;margin-left:4px;color:#98a2b3}th.sortable.active .sort-arrow{color:var(--blue)}td{padding:10px 8px;border-bottom:1px solid #edf0f5;vertical-align:top}td.score,td.money,td.date,td.num{white-space:nowrap}.score strong{font-size:15px}.badge{display:inline-block;padding:3px 7px;border-radius:999px;background:#eef2f7;font-size:11px;font-weight:600;white-space:nowrap}.project{min-width:330px}.project a{font-weight:700}.desc{max-width:470px;margin-top:3px;color:var(--muted)}a{color:var(--blue)}.result-count{font-weight:600}.empty{padding:28px;text-align:center;color:var(--muted)}
@media(max-width:1050px){.cards{grid-template-columns:repeat(2,1fr)}.filters{grid-template-columns:1fr 1fr 1fr}.date-filters{grid-template-columns:1fr 1fr}}
@media(max-width:620px){main{padding:12px}.cards,.filters,.date-filters{grid-template-columns:1fr}.date-filters button{width:100%}}
</style>
</head>
<body>
<header>
<h1>Idaho Public Project Intelligence</h1>
<p>State, city and Treasure Valley public construction, procurement and bid-result intelligence</p>
</header>
<main>
<section class="cards">
<div class="card"><div class="label">Tracked records</div><div class="value" id="total">—</div></div>
<div class="card"><div class="label" title="Existing open-view stages include planned work and retained records; verify the source before treating a row as an active bid.">Open opportunities</div><div class="value" id="openCount">—</div></div>
<div class="card"><div class="label">Treasure Valley open</div><div class="value" id="tvCount">—</div></div>
<div class="card"><div class="label">Building / facility open</div><div class="value" id="buildingCount">—</div></div>
<div class="card"><div class="label">Bid results / awards</div><div class="value" id="resultsCount">—</div></div>
</section>

<section class="panel" aria-labelledby="source-health-title">
<div class="panel-title"><div><strong id="source-health-title">Source checks</strong><div class="muted" id="source-health-asof" aria-live="polite">Checking source health…</div><div class="muted">Current collection counts are not the number of open bids or all retained records.</div></div></div>
<ul id="source-health-list" class="source-health"></ul>
<div id="shared-reporting-status"></div>
</section>

<section class="panel">
<div class="panel-title"><div><strong>RSS feeds</strong><div class="muted">Subscribe to the slices you actually want to monitor.</div></div></div>
<div class="feeds">
<a href="feeds/all-public-projects.xml">All opportunities</a><a href="feeds/treasure-valley.xml">Treasure Valley</a><a href="feeds/construction.xml">Construction</a><a href="feeds/building-projects.xml">Building projects</a><a href="feeds/materials-equipment.xml">Materials & equipment</a><a href="feeds/design-rfq.xml">Design / RFQ</a><a href="feeds/closing-14-days.xml">Closing 14 days</a><a href="feeds/new-this-week.xml">New this week</a><a href="feeds/awards.xml">Awards / bid results</a><a href="feeds/early-opportunities.xml">Early opportunities</a>
</div>
</section>

<section class="panel">
<div class="panel-title"><div><strong>Find projects</strong><div class="muted">Search across project name, description, agency, location, solicitation number, contact and bidders.</div></div><div class="report-actions"><button id="export-csv" type="button" disabled>Download filtered CSV</button> <button id="reset">Reset filters</button></div></div>
<div class="filters">
<input id="search" placeholder="Search any project, agency, bidder, number…">
<select id="view"><option value="">All records</option><option value="open">Open opportunities</option><option value="results">Bid results / awards</option></select>
<select id="source"><option value="">All sources</option></select>
<select id="stage"><option value="">All stages</option></select>
<select id="category"><option value="">All categories</option></select>
<select id="type"><option value="">All solicitation types</option></select>
</div>
<div class="date-filters">
<select id="dateField"><option value="due_date">Filter by due / bid date</option><option value="posted_date">Filter by posted date</option><option value="first_seen">Filter by first seen</option></select>
<select id="datePreset"><option value="">All dates</option><option value="next7">Next 7 days</option><option value="next14">Next 14 days</option><option value="next30">Next 30 days</option><option value="last7">Last 7 days</option><option value="last30">Last 30 days</option><option value="last90">Last 90 days</option></select>
<input id="dateFrom" type="date" aria-label="From date">
<input id="dateTo" type="date" aria-label="To date">
<select id="minScore"><option value="0">Any score</option><option value="40">Score 40+</option><option value="60">Score 60+</option><option value="80">Score 80+</option></select>
</div>
</section>

<section class="panel">
<div class="panel-title"><div><strong>Public project opportunities</strong><div class="muted" id="updated">Loading…</div></div><div><span class="result-count" id="count"></span><div class="muted">Click any column header to order; click again to reverse. CSV includes every matching row in that order.</div></div></div>
<div class="table-wrap"><table>
<thead><tr>
<th class="sortable active" data-sort="score">Score<span class="sort-arrow">▼</span></th>
<th class="sortable" data-sort="due_date">Recorded date<span class="sort-arrow"></span></th>
<th class="sortable" data-sort="posted_date">Posted<span class="sort-arrow"></span></th>
<th class="sortable" data-sort="agency">Agency<span class="sort-arrow"></span></th>
<th class="sortable" data-sort="title">Project / Location<span class="sort-arrow"></span></th>
<th class="sortable" data-sort="stage">Stage<span class="sort-arrow"></span></th>
<th class="sortable" data-sort="solicitation_type">Type<span class="sort-arrow"></span></th>
<th class="sortable" data-sort="solicitation_number">Number<span class="sort-arrow"></span></th>
<th class="sortable" data-sort="category">Category<span class="sort-arrow"></span></th>
<th class="sortable" data-sort="estimated_value">Reported value<span class="sort-arrow"></span></th>
<th class="sortable" data-sort="bidders">Bidder evidence<span class="sort-arrow"></span></th>
<th class="sortable" data-sort="first_seen">First seen<span class="sort-arrow"></span></th>
</tr></thead><tbody id="rows"></tbody>
</table></div>
<nav class="pagination" aria-label="Project result pages"><button id="prev-page" type="button" disabled>Previous</button><button id="next-page" type="button" disabled>Next</button><span id="page-summary" class="pagination-summary" aria-live="polite"></span><label for="page-size">Rows per page</label><select id="page-size"><option>25</option><option selected>50</option><option>100</option></select></nav>
</section>
</main>
<script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money=n=>n==null||Number.isNaN(Number(n))?'—':new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(Number(n));
let data=[],sortKey='score',sortDirection='desc',generatedAt='';

function dateValue(value){if(!value)return 0;const s=String(value).slice(0,10);const t=Date.parse(/^\d{4}-\d{2}-\d{2}$/.test(s)?s+'T00:00:00':value);return Number.isNaN(t)?0:t}
function dayStart(d=new Date()){return new Date(d.getFullYear(),d.getMonth(),d.getDate()).getTime()}
function isOpen(r){return !['BID_RESULTS','AWARDED','CLOSED'].includes(String(r.stage||'').toUpperCase()) && !['RESULTS','CLOSED','AWARDED'].includes(String(r.status||'').toUpperCase())}
function isResult(r){return ['BID_RESULTS','AWARDED'].includes(String(r.stage||'').toUpperCase()) || ['RESULTS','AWARDED'].includes(String(r.status||'').toUpperCase())}
function treasureValley(r){return /boise|meridian|nampa|caldwell|eagle|kuna|star|garden city|middleton|ada county|canyon county/i.test([r.location,r.title,r.description].join(' '))}
function bidderText(r){return (r.bidders||[]).map(b=>`${b.contractor||''} ${b.base_bid??''}`).join(' ')}
function searchText(r){return [r.title,r.description,r.agency,r.source,r.location,r.stage,r.status,r.solicitation_type,r.solicitation_number,r.category,r.contact,bidderText(r)].join(' ').toLowerCase()}
function uniq(key){return [...new Set(data.map(r=>r[key]).filter(Boolean))].sort((a,b)=>String(a).localeCompare(String(b),undefined,{numeric:true,sensitivity:'base'}))}
function fill(id,key){const el=document.getElementById(id);uniq(key).forEach(v=>el.insertAdjacentHTML('beforeend',`<option value="${esc(v)}">${esc(v)}</option>`))}

function dateWindow(){
 const preset=document.getElementById('datePreset').value,from=document.getElementById('dateFrom').value,to=document.getElementById('dateTo').value,today=dayStart();
 let lo=from?dateValue(from):null,hi=to?dateValue(to)+86399999:null;
 if(preset){const day=86400000;if(preset==='next7'){lo=today;hi=today+7*day-1}else if(preset==='next14'){lo=today;hi=today+14*day-1}else if(preset==='next30'){lo=today;hi=today+30*day-1}else if(preset==='last7'){lo=today-6*day;hi=today+day-1}else if(preset==='last30'){lo=today-29*day;hi=today+day-1}else if(preset==='last90'){lo=today-89*day;hi=today+day-1}}
 return {lo,hi};
}
function passesDate(r){const field=document.getElementById('dateField').value,{lo,hi}=dateWindow();if(lo==null&&hi==null)return true;const v=dateValue(r[field]);if(!v)return false;return (lo==null||v>=lo)&&(hi==null||v<=hi)}

function sortValue(r,key){
 if(key==='score'||key==='estimated_value')return Number(r[key]??-1);
 if(key==='bidders')return (r.bidders||[]).length;
 if(['due_date','posted_date','first_seen'].includes(key))return dateValue(r[key]);
 return String(r[key]??'').trim().toLowerCase();
}
function compareRows(a,b){const av=sortValue(a,sortKey),bv=sortValue(b,sortKey);let cmp;if(typeof av==='number'&&typeof bv==='number')cmp=av-bv;else cmp=String(av).localeCompare(String(bv),undefined,{numeric:true,sensitivity:'base'});if(cmp===0&&sortKey!=='score')cmp=Number(a.score||0)-Number(b.score||0);return sortDirection==='asc'?cmp:-cmp}
function updateSortHeaders(){document.querySelectorAll('th.sortable').forEach(th=>{const active=th.dataset.sort===sortKey;th.classList.toggle('active',active);th.querySelector('.sort-arrow').textContent=active?(sortDirection==='asc'?'▲':'▼'):'';th.setAttribute('aria-sort',active?(sortDirection==='asc'?'ascending':'descending'):'none')})}
function bidderSummary(r){const bids=r.bidders||[];if(!bids.length)return '—';const priced=bids.filter(b=>b.base_bid!=null).sort((a,b)=>Number(a.base_bid)-Number(b.base_bid));const lead=priced[0];return `<strong>${bids.length}</strong>${lead?`<div class="muted">Low submitted: ${esc(lead.contractor||'')} ${money(lead.base_bid)}</div>`:''}`}

function mountainTimestamp(raw){
 if(!raw)return 'Not recorded';
 const d=new Date(raw);if(!Number.isFinite(d.getTime()))return 'Not recorded';
 return new Intl.DateTimeFormat('en-US',{timeZone:'America/Boise',dateStyle:'medium',timeStyle:'short'}).format(d)+' Mountain';
}
function deadlineKind(r){
 if(!r.due_date)return 'Date not recorded';
 if(r.source==='Idaho Purchasing')return 'Planning target (not a bid deadline)';
 if(r.stage==='BID_RESULTS')return 'Bid date on result';
 if(r.source==='Idaho DPW')return 'Recorded bid date';
 if(['City of Boise','Ada County','ACHD'].includes(r.source))return 'Recorded bid cutoff';
 return 'Recorded source date';
}
function dueEvidence(r,asOf){
 const kind=deadlineKind(r);
 if(!r.due_date||!asOf||!Number.isFinite(new Date(asOf).getTime()))return kind;
 const localDay=new Intl.DateTimeFormat('en-CA',{timeZone:'America/Boise',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date(asOf));
 const iso=['year','month','day'].map(k=>localDay.find(p=>p.type===k)?.value||'').join('-');
 return r.due_date<iso && ['Recorded bid date','Recorded bid cutoff'].includes(kind) ? kind+' · past at snapshot; verify with source' : kind;
}
function postedEvidence(r){
 if(!r.posted_date)return 'No posted date recorded';
 if(r.source==='Idaho Purchasing')return 'Planning record created';
 if(r.source==='City of Boise')return 'Reported event opening';
 if(r.source==='ACHD')return 'Reported release date';
 return 'Source-reported date';
}
function seenEvidence(r,asOf){
 if(!r.last_seen)return 'Observation not recorded';
 if(r.last_seen===asOf)return 'Seen in this snapshot';
 return 'Retained; last observed '+mountainTimestamp(r.last_seen);
}
function stageEvidence(r){
 if(r.source==='Idaho Purchasing' && /^(PADD|PA)\b/i.test(r.title||''))return 'Informational agreement; not a call for bids';
 if(r.stage==='BID_RESULTS')return 'Bid result; not award evidence';
 if(r.stage==='AWARDED')return 'Award reported; no awardee verified here';
 return '';
}
function amountEvidence(r){
 if(r.estimated_value==null||r.estimated_value==='')return '';
 return r.source==='Idaho DPW'&&r.stage==='BID_RESULTS'?'Lowest parsed submitted bid; not an award':'Source-reported value';
}
async function bootSourceHealth(){
 const line=document.getElementById('source-health-asof'),list=document.getElementById('source-health-list');
 try{
  const res=await fetch('data/sources.json?'+Date.now());if(!res.ok)throw new Error('Source check unavailable');
  const data=await res.json();
  if(!Array.isArray(data.collector_status)||!data.generated_at)throw new Error('Invalid source check');
  const stamp=mountainTimestamp(data.generated_at);
  line.textContent='Source check: '+stamp+(generatedAt&&data.generated_at!==generatedAt?' · different from project snapshot; do not use these counts as that snapshot’s coverage.':'');
  list.innerHTML=data.collector_status.map(c=>`<li><strong>${esc(c.source||'Unknown source')}</strong> · ${esc(c.status||'Unknown')} · ${esc(c.records_seen??'—')} observed${c.note?`<div class="muted row-evidence">${esc(c.note)}</div>`:''}</li>`).join('');
 }catch{line.textContent='Source health is unavailable; this does not mean zero source activity.';list.innerHTML='';}
}

function filteredRows(){
 const q=document.getElementById('search').value.trim().toLowerCase(),view=document.getElementById('view').value,source=document.getElementById('source').value,stage=document.getElementById('stage').value,category=document.getElementById('category').value,type=document.getElementById('type').value,minScore=Number(document.getElementById('minScore').value);
 return data.filter(r=>(!q||searchText(r).includes(q))&&(!view||(view==='open'?isOpen(r):isResult(r)))&&(!source||r.source===source)&&(!stage||r.stage===stage)&&(!category||r.category===category)&&(!type||r.solicitation_type===type)&&Number(r.score||0)>=minScore&&passesDate(r)).sort(compareRows);
}
function csvCell(value){
 let text=value==null?'':String(value);
 // Neutralize spreadsheet formula triggers, including after whitespace or controls.
 if(typeof value!=='number' && (/^[\s\p{Cc}\p{Cf}]*[=+\-@＝＋－＠]/u.test(text) || /^[\t\r\n]/.test(text)))text="'"+text;
 return '"'+text.replace(/"/g,'""')+'"';
}
function exportRowsCsv(rows,asOf){
 const headers=['Stable ID','Source','Agency','Title','Location','Solicitation number','Stored stage','Stored status','Category','Heuristic score','Recorded date','Recorded date type','Source posted date','Posted date type','First observed UTC','Last observed UTC','Snapshot UTC','Official project URL','Bidder count','Reported value','Reported value meaning','Stage evidence'];
 const values=rows.map(r=>[r.id,r.source,r.agency,r.title,r.location,r.solicitation_number,r.stage,r.status,r.category,r.score,r.due_date,deadlineKind(r),r.posted_date,postedEvidence(r),r.first_seen,r.last_seen,asOf,r.url,(r.bidders||[]).length,r.estimated_value,amountEvidence(r),stageEvidence(r)]);
 return [headers,...values].map(row=>row.map(csvCell).join(',')).join('\r\n')+'\r\n';
}
function downloadFilteredCsv(){
 const rows=filteredRows();if(!rows.length)return;
 const url=URL.createObjectURL(new Blob(['\uFEFF',exportRowsCsv(rows,generatedAt)],{type:'text/csv;charset=utf-8'}));
 const a=document.createElement('a');
 a.href=url;a.download='idaho-public-projects-'+(generatedAt||'snapshot').slice(0,10)+'.csv';
 document.body.appendChild(a);
 try{a.click();}finally{a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)}
}
let pageNumber=1;
function resetPageAndRender(){pageNumber=1;render()}
function render(){
 const rows=filteredRows();
 const size=Number(document.getElementById('page-size').value)||50;
 const pageCount=Math.max(1,Math.ceil(rows.length/size));
 pageNumber=Math.min(pageCount,Math.max(pageNumber,1));
 const start=(pageNumber-1)*size, visible=rows.slice(start,start+size);
 document.getElementById('prev-page').disabled=pageNumber<=1;
 document.getElementById('next-page').disabled=pageNumber>=pageCount;
 document.getElementById('page-summary').textContent=rows.length?`Rows ${start+1}–${start+visible.length} of ${rows.length} · page ${pageNumber} of ${pageCount}`:'No results';

 document.getElementById('export-csv').disabled=!rows.length;
 updateSortHeaders();document.getElementById('count').textContent=`${rows.length.toLocaleString()} matching records`;
 if(!rows.length){document.getElementById('rows').innerHTML='<tr><td colspan="12" class="empty">No projects match the current filters.</td></tr>';return}
 document.getElementById('rows').innerHTML=visible.map(r=>`<tr>
 <td class="score"><strong>${Number(r.score||0)}</strong></td>
 <td class="date">${esc(r.due_date||'—')}<div class="muted row-evidence">${esc(dueEvidence(r,generatedAt))}</div></td>
 <td class="date">${esc(r.posted_date||'—')}<div class="muted row-evidence">${esc(postedEvidence(r))}</div></td>
 <td>${esc(r.agency||'—')}<div class="muted">${esc(r.source||'')}</div></td>
 <td class="project"><a href="${esc(r.url||'#')}" target="_blank" rel="noopener">${esc(r.title||'Untitled project')}</a><div>${esc(r.location||'')}</div><div class="desc">${esc((r.description||'').slice(0,220))}</div>${r.source==='City of Boise'&&r.contact?`<div class="muted row-evidence">Procurement contact: ${esc(r.contact)}</div>`:''}</td>
 <td><span class="badge">${esc(r.stage||'—')}</span><div class="muted row-evidence">${esc(stageEvidence(r))}</div></td>
 <td>${esc(r.solicitation_type||'—')}</td>
 <td>${esc(r.solicitation_number||'—')}</td>
 <td>${esc(r.category||'—')}</td>
 <td class="money">${money(r.estimated_value)}<div class="muted row-evidence">${esc(amountEvidence(r))}</div></td>
 <td class="num">${bidderSummary(r)}</td>
 <td class="date">${esc((r.first_seen||'').slice(0,10)||'—')}<div class="muted row-evidence">${esc(seenEvidence(r,generatedAt))}</div></td>
 </tr>`).join('');
}

function resetFilters(){['search','view','source','stage','category','type','datePreset','dateFrom','dateTo'].forEach(id=>document.getElementById(id).value='');document.getElementById('dateField').value='due_date';document.getElementById('minScore').value='0';render()}
async function boot(){const payload=await fetch('data/opportunities.json?'+Date.now()).then(r=>r.json());data=payload.opportunities||[];generatedAt=payload.generated_at||'';fill('source','source');fill('stage','stage');fill('category','category');fill('type','solicitation_type');const open=data.filter(isOpen),tv=open.filter(treasureValley),building=open.filter(r=>r.category==='BUILDING'),results=data.filter(isResult);document.getElementById('total').textContent=data.length.toLocaleString();document.getElementById('openCount').textContent=open.length.toLocaleString();document.getElementById('tvCount').textContent=tv.length.toLocaleString();document.getElementById('buildingCount').textContent=building.length.toLocaleString();document.getElementById('resultsCount').textContent=results.length.toLocaleString();document.getElementById('updated').textContent=generatedAt?`Project snapshot: ${mountainTimestamp(generatedAt)}`:'';render();void bootSourceHealth()}
['search'].forEach(id=>document.getElementById(id).addEventListener('input',resetPageAndRender));['view','source','stage','category','type','dateField','datePreset','dateFrom','dateTo','minScore'].forEach(id=>document.getElementById(id).addEventListener('change',resetPageAndRender));document.getElementById('reset').addEventListener('click',resetFilters);document.getElementById('export-csv').addEventListener('click',downloadFilteredCsv);document.querySelectorAll('th.sortable').forEach(th=>th.addEventListener('click',()=>{const next=th.dataset.sort;if(sortKey===next)sortDirection=sortDirection==='asc'?'desc':'asc';else{sortKey=next;sortDirection=['score','due_date','posted_date','estimated_value','bidders','first_seen'].includes(next)?'desc':'asc'}resetPageAndRender()}));
document.getElementById('prev-page').addEventListener('click',()=>{pageNumber--;render()});document.getElementById('next-page').addEventListener('click',()=>{pageNumber++;render()});document.getElementById('page-size').addEventListener('change',resetPageAndRender);
boot().catch(err=>{void bootSourceHealth();document.getElementById('updated').textContent='Unable to load project data';document.getElementById('rows').innerHTML=`<tr><td colspan="12" class="empty">${esc(err.message||err)}</td></tr>`});
</script>
<script>
/* Source reporting extension. No writes or lead/default/filter changes. */
(() => {
  'use strict';
  const mount=document.getElementById('shared-reporting-status');
  if(!mount)return;
  const make=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e};
  const val=x=>(x===null||x===undefined||x==='')?'Unknown':String(x);
  const title=(x)=>val(x).replaceAll('_',' ');
  const count=x=>Number.isInteger(x)&&x>=0?x.toLocaleString('en-US'):'Unknown';
  const mtime=x=>{
    if(!x)return 'Unknown';
    const d=new Date(x);return Number.isFinite(d.getTime())?
      d.toLocaleString('en-US',{timeZone:'America/Boise'})+' MT':'Unknown';
  };
  const validDate=/^\d{4}-\d{2}-\d{2}$/;
  function show(payload){
    if(payload?.schema_version!==1||!Array.isArray(payload.sources)||payload.sources.length===0)throw Error('No comparable evidence manifest');
    mount.replaceChildren();
    mount.append(make('h2','Collection evidence by source'));
    mount.append(make('p','An attempt, a successful collection and the latest source date are different. Stored history is not an active opportunity count. Unknown does not mean zero.'));
    const style=make('style',`#shared-reporting-status .source-evidence-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(18rem,100%),1fr));gap:.7rem}#shared-reporting-status .source-evidence-card{padding:.8rem;border:1px solid #bccbd2;border-radius:.55rem;min-width:0;overflow-wrap:anywhere}#shared-reporting-status .source-evidence-card h3{line-height:1.25;margin:.12em 0 .4em;font-size:1.03rem}#shared-reporting-status .source-evidence-card dl{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:.35rem .5rem;margin:.5rem 0 0;font-size:.88rem}#shared-reporting-status .source-evidence-card dd{margin:0}#shared-reporting-status .source-evidence-card dt{font-weight:600}#shared-reporting-status .source-evidence-card p{margin:.3rem 0;font-size:.9rem}`);
    mount.append(style);
    const cards=make('div',undefined,'source-evidence-grid');
    for(const row of payload.sources){
      const card=make('article',undefined,'source-evidence-card');
      const head=make('h3',val(row.label));const coverage=make('p',title(row.mode)+' · '+val(row.coverage));
      const pairs=make('dl');
      const date=typeof row.latest_authoritative_date==='string'&&validDate.test(row.latest_authoritative_date)?row.latest_authoritative_date:'Unknown';
      const label=date==='Unknown'?'Unknown':date+' · '+title(row.latest_date_kind);
      const stats=[
        ['Last attempt',mtime(row.last_attempt_at)],['Last success',mtime(row.last_success_at)],
        ['Latest source evidence',label],['Age at snapshot',row.source_age_days==null?'Unknown':count(row.source_age_days)+' days'],
        ['New since prior success',count(row.new_since_previous_success)],['Stored history',count(row.retained_records)],
        ['Observed this attempt',count(row.observed_records)],['Availability',title(row.availability)],
        ['Collection outcome',title(row.collection_outcome)],
      ];
      if(row.date_provenance)stats.push(['Date provenance',title(row.date_provenance)]);
      if(row.freshness_status)stats.push(['Freshness',title(row.freshness_status)]);
      for(const [key,value] of stats)pairs.append(make('dt',key),make('dd',value));
      card.append(head,coverage,pairs);cards.append(card);
    }
    mount.append(cards);
  }
  mount.hidden=false;
  fetch('data/sources.json?reporting_v1='+Date.now(),{cache:'no-store'})
    .then(r=>{if(!r.ok)throw Error('Source metadata unavailable');return r.json()})
    .then(p=>show(p.reporting_v1))
    .catch(()=>{mount.replaceChildren(make('h2','Collection evidence by source'),make('p','Comparable collection evidence is unavailable for this snapshot. Do not treat missing evidence as zero permits.'))});
})();

</script>
</body></html>'''


def write(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(HTML, encoding="utf-8")
