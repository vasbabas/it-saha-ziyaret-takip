import http.server
import socketserver
import threading
import json
import database as db

class SyncAPIHandler(http.server.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/api/sync_data'):
            try:
                data_json = db.export_data_json()
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data_json.encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith('/api/sync_upload'):
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                
                success, msg = db.import_data_json(body, mode="merge")
                
                self.send_response(200 if success else 400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                res_payload = {"success": success, "message": msg}
                self.wfile.write(json.dumps(res_payload, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "message": str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return

_server_instance = None

def start_sync_server_once(port=8502):
    global _server_instance
    if _server_instance is not None:
        return _server_instance
        
    try:
        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True

        _server_instance = ReusableTCPServer(('0.0.0.0', port), SyncAPIHandler)
        t = threading.Thread(target=_server_instance.serve_forever, daemon=True)
        t.start()
        print(f"Sync API Server running on port {port}")
        return _server_instance
    except Exception as e:
        print(f"Sync Server Status: {e}")
        return None
