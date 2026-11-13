'use strict';
const headings = {
  overview: ['项目总览', '统一查看项目进度、验证证据与工程状态。'],
  tasks: ['任务管理', '追踪任务状态与验收证据完整性。'],
  tests: ['测试与验收', '按时间查看已保存的测试报告与验证结果。'],
  repairs: ['AI 修复记录', '观察多轮修复过程与最终结果。'],
  changes: ['代码变更', '追踪经过审批的本地修改及恢复状态。'],
  git: ['Git 仓库', '快速查看分支、提交和工作区变更。']
};
const statusNames = {todo: '待办', in_progress: '进行中', blocked: '阻塞', done: '已完成', passed: '通过', failed: '失败', unverified: '未验证', completed: '已完成', exhausted: '次数耗尽', applied: '已应用', restored: '已恢复', aborted: '已中止', awaiting_approval: '待审批', awaiting_test: '待测试', awaiting_repair: '待修复', testing: '测试中', recovery_needed: '需恢复', rollback_blocked: '恢复受阻'};
const colors = {done: '#4ce1c5', in_progress: '#6d9fff', todo: '#8c90dc', blocked: '#eb7d93'};
const $ = (id) => document.getElementById(id);
const asArray = (v) => Array.isArray(v) ? v : [];
let state = {snapshot: null, view: 'overview', refreshing: false};

function node(tag, className, content) {
  const n = document.createElement(tag);
  if (className) n.className = className;
  if (content !== undefined && content !== null) n.textContent = String(content);
  return n;
}
function dateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '—' : new Intl.DateTimeFormat('zh-CN', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}).format(d);
}
function percent(num, denom) { return denom > 0 ? Math.min(100,Math.max(0,Math.round(num / denom * 100))) : 0; }
function pill(value, override) { return node('span', 'pill ' + String(value).replace(/[^a-z_]/g,''), override || statusNames[value] || value || '—'); }
function empty(message) { const box = node('div','empty-state');box.append(node('span','empty-symbol','◇'),node('span','',message));return box; }
function cell(row, text, sub) { const td = node('td','');td.append(node('span','cell-primary',text));if (sub) td.append(node('span','cell-sub',sub));row.append(td);return td; }
function cellNode(row, n) {const td=node('td','');td.append(n);row.append(td);}
function tableBody(id, entries, render, msg) {const tbody=$(id);tbody.replaceChildren();if(!entries.length){const row=node('tr','');const td=node('td','empty-state',msg);td.colSpan=5;row.append(td);tbody.append(row);return;}for(const item of entries)tbody.append(render(item));}

function setView(view) {
  if (!headings[view]) return;
  state.view=view;
  for (const key of Object.keys(headings)) $(key).hidden = key !== view;
  document.querySelectorAll('.nav-item').forEach(btn => {const active=btn.dataset.view===view;btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',String(active));});
  $('pageTitle').textContent=headings[view][0];$('breadcrumb').textContent=headings[view][0];$('pageDesc').textContent=headings[view][1];
  window.scrollTo({top:0,behavior:'smooth'});
}
function renderOverview(d) {
  const total=d.stats.tasks;const statuses=d.stats.by_status;
  $('metricTasks').textContent=total;
  $('metricDone').textContent=statuses.done;
  $('metricDoneSub').textContent=percent(statuses.done,total)+'% 的任务已完成';
  $('metricPassed').textContent=d.stats.successful_reports;
  $('metricPassedSub').textContent='最近 '+d.stats.reports+' 份报告中 '+d.stats.failed_reports+' 项失败';
  $('metricWarnings').textContent=statuses.blocked+d.stats.evidence_alerts;
  $('completionPercent').textContent=percent(statuses.done,total)+'%';
  const ordering=['done','in_progress','todo','blocked'];let from=0;
  const ring=ordering.map(k=>{const to=from+percent(statuses[k],total);const s=`${colors[k]} ${from}% ${to}%`;from=to;return s;}).join(', ');
  $('progressRing').style.background=total ? `conic-gradient(${ring}, #34435f ${Math.min(100,from)}% 100%)` : '#34435f';
  const legend=$('taskLegend');legend.replaceChildren();const strip=$('progressStrip');strip.replaceChildren();
  for (const k of ordering) {
    const row=node('div','legend-row');const dot=node('span','legend-dot');dot.style.background=colors[k];row.append(dot,node('span','',statusNames[k]),node('b','',statuses[k]));legend.append(row);
    if(statuses[k] > 0){const segment=node('span','progress-segment');segment.style.flexGrow=String(statuses[k]);segment.style.background=colors[k];strip.append(segment);}
  }
  const rows=$('qualityRows');rows.replaceChildren();
  const values=[['任务完成率',statuses.done,total,''],['最近报告通过率',d.stats.successful_reports,d.stats.reports,'blue'],['展示任务证据未告警率',d.coverage.evidence_checked_tasks-d.stats.evidence_alerts,d.coverage.evidence_checked_tasks,'warn']];
  for(const [label,good,base,color] of values){const wrap=node('div','quality-row');const line=node('div','quality-label');line.append(node('span','',label),node('strong','',base?percent(good,base)+'%':'暂无数据'));const bar=node('div','quality-bar');const fill=node('div','quality-fill '+color);fill.style.width=(base?percent(good,base):0)+'%';bar.append(fill);wrap.append(line,bar);rows.append(wrap);}
  const recents=$('recentReports');recents.replaceChildren();
  if (!d.reports.length) recents.append(empty('目前还没有测试报告。运行经授权的测试后将在此显示。'));
  for(const report of d.reports.slice(0,4)) {
    const row=node('div','record-item');row.append(node('span','report-icon '+report.status,report.status==='passed'?'✓':report.status==='failed'?'!':'○'));
    const detail=node('div','record-detail');detail.append(node('strong','',report.name),node('small','',`${dateTime(report.timestamp)} · ${report.passed}/${report.checks} 项检查通过`));row.append(detail,pill(report.status));recents.append(row);
  }
  const repo=$('repoOverview');repo.replaceChildren();
  if(d.git.available){const first=node('div','info-strip');first.append(node('span','','当前分支'),node('strong','',d.git.branch));repo.append(first);for(const [label,value] of [['HEAD 提交',d.git.head||'—'],['工作区状态',d.git.dirty?'存在未提交修改':'干净'],['当前可见变更文件',d.git.files.length]]){const r=node('div','repo-pair');r.append(node('span','',label),node('strong','',value));repo.append(r);}}
  else repo.append(empty(d.git.note || '该目录尚未初始化 Git 仓库。'));
}
function renderTables(d) {
  $('navTasks').textContent=d.stats.tasks;
  const term=$('taskSearch').value.toLowerCase().trim();const filter=$('taskFilter').value;
  const tasks=d.tasks.filter(t=>(filter==='all'||t.status===filter)&&(`${t.id} ${t.title} ${t.skill}`).toLowerCase().includes(term));
  tableBody('taskRows',tasks,t=>{const row=node('tr','');cell(row,t.title||'未命名',t.id+(t.skill?' · '+t.skill:''));cellNode(row,pill(t.status));const evidence=t.evidence_integrity;cellNode(row,pill(evidence,evidence==='verified'?'已核验':evidence==='warning'?'证据异常':evidence==='manual'?'人工验收':'无证据'));cell(row,dateTime(t.updated_at));return row;},'没有符合条件的任务。');
  tableBody('reportRows',d.reports,r=>{const row=node('tr','');cell(row,r.name);cellNode(row,pill(r.status));cell(row,`${r.passed} 通过 · ${r.failed} 失败 · ${r.skipped} 未执行`);cell(row,dateTime(r.timestamp));return row;},'还没有测试报告。');
  tableBody('repairRows',asArray(d.loops.items),r=>{const row=node('tr','');cell(row,r.run_id);cellNode(row,pill(r.stage));cell(row,r.attempts);cell(row,r.passed_attempts+' / '+r.failed_attempts);return row;},'尚未创建修复会话。');
  tableBody('changeRows',d.changes,c=>{const row=node('tr','');cell(row,c.id);cell(row,c.task_id||'—');cellNode(row,pill(c.status));cell(row,c.file_count);return row;},'尚未记录本地代码修改。');
  tableBody('gitRows',d.git.available?d.git.files:[],f=>{const row=node('tr','');cell(row,f.path);cellNode(row,pill(f.code==='??'?'unverified':f.code.includes('M')?'in_progress':'todo',f.code));return row;},'仓库工作区干净，或未识别为独立 Git 仓库。');
  $('gitSummary').replaceChildren();
  for(const [label,value] of [['当前分支',d.git.available?d.git.branch:'—'],['当前提交',d.git.available?d.git.head||'—':'—'],['变更文件数',d.git.available?d.git.files.length:'—']]){const r=node('div','info-strip');r.append(node('span','',label),node('strong','',value));$('gitSummary').append(r);}
  $('repairRuns').textContent=d.loops.available ? d.loops.runs : '—';
  $('repairCompleted').textContent=d.loops.available ? d.loops.completed : '—';
  $('repairAttempts').textContent=d.loops.available ? d.loops.total_attempts : '—';
  $('repairExhausted').textContent=d.loops.available ? d.loops.exhausted : '—';
}
function render(d) {
  state.snapshot=d;
  $('projectName').textContent=d.project.name;
  $('projectPath').textContent=d.project.path;
  $('projectPath').title=d.project.path;
  $('lastUpdate').textContent=dateTime(d.generated_at);
  $('syncState').textContent='数据已同步 · 自动刷新每 30 秒';
  const notices=$('notices');notices.replaceChildren();
  if(d.coverage.tasks_total>d.coverage.tasks_displayed)notices.append(node('div','notice',`仅展示最近 ${d.coverage.tasks_displayed} / ${d.coverage.tasks_total} 项任务，搜索与筛选限于当前展示范围。`));
  for(const message of asArray(d.warnings).slice(0,3))notices.append(node('div','notice',message));
  renderOverview(d);renderTables(d);
}
async function refresh() {
  if (state.refreshing) return;
  state.refreshing=true;$('refresh').disabled=true;$('syncState').textContent='读取中…';
  try {
    const response=await fetch('/api/snapshot',{credentials:'same-origin',cache:'no-store'});
    if(!response.ok)throw Error('HTTP '+response.status);
    render(await response.json());
  } catch (err) {
    $('syncState').textContent='连接失败 · 请刷新或检查终端';
    $('notices').replaceChildren(node('div','notice','无法读取项目状态：'+String(err.message)));
  } finally {state.refreshing=false;$('refresh').disabled=false;}
}
document.querySelectorAll('.nav-item').forEach(btn=>btn.addEventListener('click',()=>setView(btn.dataset.view)));
document.querySelectorAll('[data-goto]').forEach(btn=>btn.addEventListener('click',()=>setView(btn.dataset.goto)));
$('taskSearch').addEventListener('input',()=>{if(state.snapshot)renderTables(state.snapshot)});
$('taskFilter').addEventListener('change',()=>{if(state.snapshot)renderTables(state.snapshot)});
$('refresh').addEventListener('click',refresh);
refresh();setInterval(refresh,30000);
