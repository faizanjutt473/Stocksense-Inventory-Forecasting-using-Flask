/* ============ StockSense - main.js (Flask API se connected) ============ */

// ---------- Helpers ----------
const $ = id => document.getElementById(id);
const icon = n => `<svg class="ic" width="18" height="18"><use href="#i-${n}"/></svg>`;
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = n => 'Rs ' + Math.round(n).toLocaleString();
const STATUS = {OK: 'b-ok', Low: 'b-low', Out: 'b-out'};
const toast = m => { const t = $('toast'); t.textContent = m; t.style.display = 'block'; setTimeout(() => t.style.display = 'none', 3000); };

async function api(path, {method = 'GET', body} = {}) {
  const res = await fetch('/api' + path, {
    method,
    headers: {'Content-Type': 'application/json'},
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch (e) {}
  if (res.status === 401) { location.href = 'login.html'; throw new Error('Pehle login karein'); }
  if (!res.ok) throw new Error((data && data.message) || 'Server se jawab nahi aaya');
  return data;
}
// Har async function ke errors toast mein dikhane ke liye
const safe = fn => async (...a) => { try { await fn(...a); } catch (e) { toast(e.message); } };

const closeM = id => $(id).classList.remove('open');
const openM = safe(async id => { await fill(); $(id).classList.add('open'); });
document.querySelectorAll('.mo').forEach(m => m.addEventListener('click', e => { if (e.target === m) m.classList.remove('open'); }));

// Dropdowns (products / suppliers) database se bharna
async function fill() {
  const needP = ['mvP', 'fcP', 'oP'].some(i => $(i));
  if (needP) {
    const products = await api('/products');
    const opts = products.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('');
    ['mvP', 'fcP', 'oP'].forEach(i => { const e = $(i); if (!e) return; const v = e.value; e.innerHTML = opts; if (v) e.value = v; });
  }
  if ($('oS')) {
    const sup = await api('/suppliers');
    $('oS').innerHTML = sup.map(s => `<option value="${s.id}">${esc(s.name)}</option>`).join('');
  }
}

// ---------- Common UI ----------
$('mb').onclick = () => $('side').classList.toggle('open');
$('bell').onclick = safe(async () => { const d = await api('/dashboard'); toast(d.summary.low_stock_count + ' low-stock alerts hain'); });
$('gs').addEventListener('keydown', e => { if (e.key === 'Enter') location.href = 'products.html?q=' + encodeURIComponent(e.target.value); });
function theme(t) {
  document.documentElement.dataset.theme = t;
  $('tb').innerHTML = icon(t === 'dark' ? 'sun' : 'moon');
  try { localStorage.setItem('ss-theme', t); } catch (e) {}
}
let saved = null; try { saved = localStorage.getItem('ss-theme'); } catch (e) {}
theme(saved || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
$('tb').onclick = () => { theme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'); location.reload(); };

async function logout() {
  try { await api('/auth/logout', {method: 'POST'}); } catch (e) {}
  location.href = 'login.html';
}
(async () => {
  try {
    const me = await api('/auth/me');
    const box = document.querySelector('.admin');
    if (!box) return;
    box.querySelector('b').textContent = me.username;
    const btn = document.createElement('button');
    btn.title = 'Logout';
    btn.style.cssText = 'margin-left:auto;width:34px;height:34px;border-radius:8px;border:1px solid rgba(255,255,255,.2);background:transparent;color:#fff;cursor:pointer;display:grid;place-items:center';
    btn.innerHTML = '<svg class="ic" width="18" height="18" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>';
    btn.onclick = logout;
    box.appendChild(btn);
  } catch (e) {}
})();

// ---------- Charts ----------
const P = '#6d28d9', Y = '#facc15', PL = '#a78bfa';
const charts = {};
function chart(id, cfg) {
  if (typeof Chart === 'undefined') { $(id).parentElement.innerHTML = '<p>Chart load nahi hua (internet check karein)</p>'; return; }
  if (charts[id]) charts[id].destroy();
  Chart.defaults.color = getComputedStyle(document.documentElement).getPropertyValue('--mu').trim() || '#6b6485';
  cfg.options = Object.assign({responsive: true, maintainAspectRatio: false}, cfg.options || {});
  charts[id] = new Chart($(id), cfg);
}

// ---------- Dashboard ----------
const initDashboard = safe(async () => {
  const d = await api('/dashboard'), s = d.summary;
  $('s1').textContent = s.total_products;
  $('s2').textContent = s.low_stock_count;
  $('s3').textContent = fmt(s.stock_value);
  $('s4').textContent = s.out_of_stock_count;
  $('lowT').innerHTML = d.low_stock.map(p => `<tr><td>${esc(p.name)}</td><td><span class="bd ${STATUS[p.status]}">${p.stock}</span></td><td>${p.reorder_level}</td><td><b>${p.suggested_order}</b> units</td></tr>`).join('') || '<tr><td colspan="4">Sab items theek hain</td></tr>';
  $('act').innerHTML = d.recent_activity.map(m => `<div class="al"><span class="bd ${m.type === 'in' ? 'b-ok' : 'b-in'}">${m.type.toUpperCase()}</span><span>${esc(m.product)}</span><b>${m.quantity}</b></div>`).join('') || '<p>Abhi koi activity nahi</p>';
  chart('c1', {type: 'line', data: {labels: d.weekly_sales.labels, datasets: [
    {label: 'Units sold', data: d.weekly_sales.units, borderColor: P, backgroundColor: 'rgba(109,40,217,.12)', fill: true, tension: .35}]}});
  chart('c2', {type: 'doughnut', data: {labels: d.stock_by_category.map(c => c.category), datasets: [{data: d.stock_by_category.map(c => c.stock), backgroundColor: [P, Y, PL, '#4c1d95', '#eab308', '#c4b5fd'], borderWidth: 0}]}, options: {plugins: {legend: {position: 'bottom'}}}});
});

// ---------- Products ----------
let searchTimer;
const renderProducts = safe(async () => {
  const q = $('pq').value.trim(), c = $('pc').value;
  const rows = await api('/products?q=' + encodeURIComponent(q) + '&category=' + encodeURIComponent(c));
  $('prodT').innerHTML = rows.map(p => `<tr><td>${esc(p.sku)}</td><td><b>${esc(p.name)}</b></td><td>${esc(p.category)}</td><td>${fmt(p.cost_price)}</td><td>${fmt(p.sale_price)}</td><td>${p.stock}</td><td><span class="bd ${STATUS[p.status]}">${p.status}</span></td><td><button class="btn bo sm" onclick="delProd(${p.id})">Delete</button></td></tr>`).join('') || '<tr><td colspan="8">Koi product nahi mila</td></tr>';
});
const loadCategories = safe(async () => {
  const cs = await api('/products/categories'), cur = $('pc').value;
  $('pc').innerHTML = '<option value="">All Categories</option>' + cs.map(x => `<option ${x === cur ? 'selected' : ''}>${esc(x)}</option>`).join('');
});
const initProducts = async () => {
  const q = new URLSearchParams(location.search).get('q'); if (q) $('pq').value = q;
  $('pq').addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(renderProducts, 250); });
  $('pc').addEventListener('change', renderProducts);
  await loadCategories(); await renderProducts();
};
const addProduct = safe(async () => {
  const sku = $('aSku').value.trim(), name = $('aName').value.trim();
  if (!sku || !name) return toast('SKU aur Name zaroori hain');
  await api('/products', {method: 'POST', body: {
    sku, name, category: $('aCat').value.trim() || 'General',
    cost_price: +$('aCost').value || 0, sale_price: +$('aPrice').value || 0,
    stock: +$('aStock').value || 0, reorder_level: +$('aMin').value || 10}});
  closeM('mProd');
  ['aSku', 'aName', 'aCat', 'aCost', 'aPrice'].forEach(i => $(i).value = '');
  await loadCategories(); await renderProducts(); toast('Product add ho gaya');
});
const delProd = safe(async id => {
  if (!confirm('Is product ko delete karna hai?')) return;
  await api('/products/' + id, {method: 'DELETE'});
  await loadCategories(); await renderProducts(); toast('Product delete ho gaya');
});

// ---------- Suppliers ----------
const renderSuppliers = safe(async () => {
  const rows = await api('/suppliers');
  $('supT').innerHTML = rows.map(s => `<tr><td><b>${esc(s.name)}</b></td><td>${esc(s.contact_person)}</td><td>${esc(s.phone)}</td><td>${s.lead_time_days} days</td><td>${s.product_count}</td></tr>`).join('');
});
const addSupplier = safe(async () => {
  const name = $('sName').value.trim(); if (!name) return toast('Name zaroori hai');
  await api('/suppliers', {method: 'POST', body: {name, contact_person: $('sCon').value.trim(), phone: $('sPh').value.trim(), lead_time_days: +$('sLead').value || 5}});
  closeM('mSup'); ['sName', 'sCon', 'sPh'].forEach(i => $(i).value = '');
  await renderSuppliers(); toast('Supplier add ho gaya');
});

// ---------- Purchase Orders ----------
const renderOrders = safe(async () => {
  const rows = await api('/purchase-orders');
  $('poT').innerHTML = rows.map(o => `<tr><td>${esc(o.po_number)}</td><td>${esc(o.supplier)}</td><td>${esc(o.product)}</td><td>${o.quantity}</td><td>${fmt(o.total_amount)}</td><td><span class="bd ${o.status === 'Received' ? 'b-ok' : 'b-low'}">${o.status}</span></td><td>${o.status === 'Pending' ? `<button class="btn by sm" onclick="receive(${o.id})">Mark Received</button>` : ''}</td></tr>`).join('');
});
const addPO = safe(async () => {
  if (!$('oP').value || !$('oS').value) return toast('Supplier aur product select karein');
  await api('/purchase-orders', {method: 'POST', body: {supplier_id: +$('oS').value, product_id: +$('oP').value, quantity: +$('oQ').value || 1}});
  closeM('mPO'); await renderOrders(); toast('Purchase order ban gaya');
});
const receive = safe(async id => {
  await api(`/purchase-orders/${id}/receive`, {method: 'POST'});
  await renderOrders(); toast('Order receive ho gaya, stock update ho gaya');
});

// ---------- Stock In / Out ----------
const renderMoves = safe(async () => {
  const rows = await api('/stock/movements?limit=50');
  $('mvH').innerHTML = rows.map(m => `<tr><td>${m.date}</td><td>${esc(m.product)}</td><td><span class="bd ${m.type === 'in' ? 'b-ok' : 'b-in'}">${m.type === 'in' ? 'Stock In' : 'Stock Out'}</span></td><td>${m.quantity}</td></tr>`).join('') || '<tr><td colspan="4">Abhi koi movement nahi</td></tr>';
});
const movement = safe(async () => {
  const q = +$('mvQ').value;
  if (!$('mvP').value || q < 1) return toast('Product aur sahi quantity likhein');
  const r = await api('/stock/movements', {method: 'POST', body: {product_id: +$('mvP').value, movement_type: $('mvT').value, quantity: q, note: $('mvN').value.trim()}});
  $('mvN').value = '';
  await renderMoves(); toast('Movement save ho gayi (naya stock: ' + r.new_stock + ')');
});

// ---------- Barcode Scanner ----------
const scan = safe(async () => {
  const sku = $('scIn').value.trim(); if (!sku) return toast('SKU likhein');
  try {
    const p = await api('/barcode/lookup/' + encodeURIComponent(sku));
    $('scOut').innerHTML = `<h3>${esc(p.name)}</h3><p style="color:var(--mu)">${esc(p.sku)} · ${esc(p.category)}</p><br><p>Price: <b>${fmt(p.sale_price)}</b></p><p>In stock: <b>${p.stock}</b> <span class="bd ${STATUS[p.status]}">${p.status}</span></p><br><img src="/api/barcode/${encodeURIComponent(p.sku)}.png" alt="barcode" style="max-width:100%;background:#fff;padding:6px;border-radius:8px"><br><br><a href="stock.html" class="btn bp sm">Update Stock</a>`;
  } catch (e) {
    $('scOut').textContent = e.message;
  }
});

// ---------- Demand Forecast (background / Celery) ----------
const sleep = ms => new Promise(r => setTimeout(r, ms));
let forecastBusy = false;

// Task ka status har second poochta hai (zyada se zyada 60 second)
async function waitForTask(taskId) {
  for (let i = 0; i < 60; i++) {
    const r = await api('/forecast/tasks/' + taskId);
    if (r.status === 'done') return r.result;
    if (r.status === 'failed') throw new Error(r.message);
    await sleep(1000);
  }
  throw new Error('Forecast mein zyada waqt lag raha hai, dobara try karein');
}

function drawForecast(f) {
  const hist = f.history.units, last = hist[hist.length - 1];
  chart('c3', {type: 'line', data: {labels: [...f.history.labels, ...f.forecast.labels], datasets: [
    {label: 'Actual', data: hist, borderColor: P, backgroundColor: 'rgba(109,40,217,.12)', fill: true, tension: .35},
    {label: $('fcM').value + ' Forecast', data: [...Array(hist.length - 1).fill(null), last, ...f.forecast.units], borderColor: Y, borderWidth: 3, borderDash: [6, 4], tension: .35}]}});
  $('fcStats').innerHTML = [
    ['Next 4 weeks demand', f.next_4_weeks_demand + ' units', 'si'],
    ['Current stock', f.current_stock + ' units', 'si g'],
    ['Suggested reorder', f.suggested_reorder + ' units', 'si y'],
    ['Model', $('fcM').value, 'si']]
    .map(x => `<div class="card stat"><div class="${x[2]}">${icon('chart')}</div><div><small>${x[0]}</small><b>${x[1]}</b></div></div>`).join('');
}

const forecast = safe(async () => {
  if (forecastBusy) return toast('Forecast pehle se ban raha hai, thora intezar karein');
  const id = $('fcP').value, model = $('fcM').value.toLowerCase();
  if (!id) return toast('Pehle product select karein');

  forecastBusy = true;
  $('fcStats').innerHTML = '<div class="card">Forecast background mein ban raha hai, thora intezar karein...</div>';
  try {
    let f;
    try {
      const {task_id} = await api(`/forecast/${id}/run?model=${model}`, {method: 'POST'});
      f = await waitForTask(task_id);
    } catch (e) {
      // Redis/Celery band ho to seedha forecast bana lete hain
      if (!e.message.includes('Background service')) throw e;
      toast('Background service band hai, seedha forecast bana rahe hain');
      f = await api(`/forecast/${id}?model=${model}`);
    }
    drawForecast(f);
  } catch (e) {
    $('fcStats').innerHTML = '';
    throw e;
  } finally {
    forecastBusy = false;
  }
});

// ---------- Reports ----------
const initReports = safe(async () => {
  const [profit, fast, dead] = await Promise.all([api('/reports/profit-by-category'), api('/reports/fast-moving'), api('/reports/dead-stock')]);
  chart('c4', {type: 'bar', data: {labels: profit.map(r => r.category), datasets: [{label: 'Profit (Rs)', data: profit.map(r => r.profit), backgroundColor: P, borderRadius: 8}]}, options: {plugins: {legend: {display: false}}}});
  chart('c5', {type: 'bar', data: {labels: fast.map(r => r.name), datasets: [{label: 'Units sold', data: fast.map(r => r.units_sold), backgroundColor: Y, borderRadius: 8}]}, options: {indexAxis: 'y', plugins: {legend: {display: false}}}});
  $('deadT').innerHTML = dead.map(r => `<tr><td>${esc(r.name)}</td><td>${r.stock}</td><td>${fmt(r.tied_up_value)}</td><td><span class="bd b-out">${r.days_idle} days</span></td></tr>`).join('') || '<tr><td colspan="4">Koi dead stock nahi</td></tr>';
});

// ---------- Start: sirf current page chalao ----------
const INIT = {
  dashboard: initDashboard,
  products: initProducts,
  suppliers: renderSuppliers,
  orders: renderOrders,
  stock: safe(async () => { await fill(); await renderMoves(); }),
  scanner: () => $('scIn').addEventListener('keydown', e => { if (e.key === 'Enter') scan(); }),
  forecast: safe(async () => { await fill(); await forecast(); }),
  reports: initReports,
};
(INIT[document.body.dataset.page] || (() => {}))();