#!/usr/bin/env python3
"""Simple HR API for system integration"""

import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os

class HRAPIHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'knowledge_base'),
            'user': os.getenv('DB_USER', 'weixiangzhang'),
            'port': int(os.getenv('DB_PORT', 5432))
        }
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests for HR data"""
        path = urlparse(self.path).path
        
        if path == '/hr/status':
            self._handle_status()
        elif path == '/hr/agents':
            self._handle_agents()
        elif path == '/hr/alerts':
            self._handle_alerts()
        elif path == '/hr/performance':
            self._handle_performance()
        else:
            self._send_404()
    
    def _handle_status(self):
        """Return HR system status"""
        response = {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "manager": "Linda Zhang (张丽娜)",
            "systems": ["performance", "cross_training", "mentorship"]
        }
        self._send_json_response(response)
    
    def _handle_agents(self):
        """Return agent performance data"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM hr_dashboard_view
                        ORDER BY success_rate DESC
                    """)
                    agents = [dict(row) for row in cur.fetchall()]
            
            self._send_json_response({"agents": agents})
        except Exception as e:
            self._send_error_response(str(e))
    
    def _handle_alerts(self):
        """Return active HR alerts"""
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT alert_id, agent_id, alert_type, alert_data, status, created_at
                        FROM hr_automation.hr_alerts 
                        WHERE status = 'new'
                        ORDER BY created_at DESC
                        LIMIT 20
                    """)
                    alerts = [dict(row) for row in cur.fetchall()]
            
            self._send_json_response({"alerts": alerts})
        except Exception as e:
            self._send_error_response(str(e))
    
    def _send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def _send_error_response(self, error):
        """Send error response"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": error}).encode())
    
    def _send_404(self):
        """Send 404 response"""
        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    port = int(os.getenv('HR_API_PORT', 8081))
    server = HTTPServer(('localhost', port), HRAPIHandler)
    print(f"🌐 HR API server running on port {port}")
    server.serve_forever()
