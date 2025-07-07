#!/usr/bin/env python3
"""
🌐 Domain Configuration Agent - External API Troubleshooter
===========================================================

Specialized agent for diagnosing and fixing external domain connectivity.
Investigates DNS, SSL, routing, and server configuration issues.
"""

import os
import subprocess
import requests
import json
import time
import socket
from datetime import datetime
from pathlib import Path
import logging

class DomainConfigAgent:
    """
    Expert agent for external domain configuration and troubleshooting
    
    Mission: Restore api.ashortstayinhell.com connectivity that was working before
    """
    
    def __init__(self):
        self.domain = "api.ashortstayinhell.com"
        self.port = 443
        self.expected_ip = "73.161.54.75"  # From ping results
        self.ssl_cert_path = "/Users/weixiangzhang/Local Dev/LibraryOfBabel/ssl/production_certs/"
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("DomainConfigAgent")
        
        print("🌐 Domain Configuration Agent initialized")
        print(f"🎯 Target: {self.domain}:{self.port}")
        
    def investigate_domain_history(self):
        """Investigate what was working before"""
        print("\n🔍 PHASE 1: Domain History Investigation")
        print("="*50)
        
        # Check git history for domain configuration
        git_results = self._check_git_history()
        
        # Analyze SSL certificates
        ssl_status = self._analyze_ssl_certificates()
        
        # Check for server configuration files
        server_configs = self._find_server_configs()
        
        return {
            "git_history": git_results,
            "ssl_status": ssl_status,
            "server_configs": server_configs
        }
    
    def _check_git_history(self):
        """Check git commits for domain configuration"""
        try:
            # Search for commits mentioning the domain
            result = subprocess.run([
                'git', 'log', '--oneline', '--grep=ashortstayinhell', 
                '--grep=external', '--grep=domain', '--grep=SSL'
            ], capture_output=True, text=True, cwd="/Users/weixiangzhang/Local Dev/LibraryOfBabel")
            
            commits = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            print(f"📜 Found {len(commits)} relevant commits:")
            for commit in commits[:5]:  # Show last 5
                print(f"   • {commit}")
                
            return commits
            
        except Exception as e:
            print(f"❌ Git history check failed: {e}")
            return []
    
    def _analyze_ssl_certificates(self):
        """Analyze SSL certificate status"""
        cert_path = Path(self.ssl_cert_path)
        
        if not cert_path.exists():
            return {"status": "missing", "path": str(cert_path)}
        
        certs = list(cert_path.glob("*.pem"))
        cert_info = {}
        
        for cert in certs:
            try:
                # Get certificate info
                result = subprocess.run([
                    'openssl', 'x509', '-in', str(cert), '-text', '-noout'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Extract domain names
                    lines = result.stdout.split('\n')
                    domains = []
                    for line in lines:
                        if 'DNS:' in line:
                            domains.extend([d.strip() for d in line.split('DNS:')[1:]])
                    
                    cert_info[cert.name] = {
                        "domains": domains,
                        "file_size": cert.stat().st_size,
                        "modified": datetime.fromtimestamp(cert.stat().st_mtime).isoformat()
                    }
                    
            except Exception as e:
                cert_info[cert.name] = {"error": str(e)}
        
        print(f"🔐 SSL Certificate Analysis:")
        for cert_name, info in cert_info.items():
            print(f"   • {cert_name}: {info}")
            
        return cert_info
    
    def _find_server_configs(self):
        """Find server configuration files"""
        config_files = []
        search_paths = [
            "/Users/weixiangzhang/Local Dev/LibraryOfBabel/src/api/",
            "/Users/weixiangzhang/Local Dev/LibraryOfBabel/ssl/",
            "/Users/weixiangzhang/Local Dev/LibraryOfBabel/scripts/"
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if any(keyword in file.lower() for keyword in 
                              ['server', 'domain', 'nginx', 'apache', 'config', 'hell']):
                            config_files.append(os.path.join(root, file))
        
        print(f"⚙️ Found {len(config_files)} potential config files:")
        for config in config_files[:10]:  # Show first 10
            print(f"   • {config}")
            
        return config_files
    
    def diagnose_current_connectivity(self):
        """Diagnose current connectivity issues"""
        print("\n🔧 PHASE 2: Current Connectivity Diagnosis")
        print("="*50)
        
        # DNS resolution
        dns_result = self._test_dns_resolution()
        
        # Port connectivity
        port_result = self._test_port_connectivity()
        
        # SSL handshake
        ssl_result = self._test_ssl_handshake()
        
        # HTTP response
        http_result = self._test_http_response()
        
        return {
            "dns": dns_result,
            "port": port_result,
            "ssl": ssl_result,
            "http": http_result
        }
    
    def _test_dns_resolution(self):
        """Test DNS resolution"""
        try:
            resolved_ip = socket.gethostbyname(self.domain)
            matches_expected = resolved_ip == self.expected_ip
            
            result = {
                "resolved_ip": resolved_ip,
                "expected_ip": self.expected_ip,
                "matches": matches_expected,
                "status": "✅" if matches_expected else "⚠️"
            }
            
            print(f"🌐 DNS Resolution: {result['status']} {resolved_ip}")
            return result
            
        except Exception as e:
            result = {"error": str(e), "status": "❌"}
            print(f"🌐 DNS Resolution: ❌ {e}")
            return result
    
    def _test_port_connectivity(self):
        """Test port connectivity"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((self.domain, self.port))
            sock.close()
            
            connected = result == 0
            status = "✅" if connected else "❌"
            
            print(f"🔌 Port {self.port}: {status} {'Connected' if connected else 'Connection failed'}")
            
            return {
                "connected": connected,
                "port": self.port,
                "status": status
            }
            
        except Exception as e:
            print(f"🔌 Port {self.port}: ❌ {e}")
            return {"error": str(e), "status": "❌"}
    
    def _test_ssl_handshake(self):
        """Test SSL handshake"""
        try:
            result = subprocess.run([
                'openssl', 's_client', '-connect', f'{self.domain}:{self.port}',
                '-servername', self.domain, '-verify_return_error'
            ], input='', text=True, capture_output=True, timeout=30)
            
            success = result.returncode == 0
            status = "✅" if success else "❌"
            
            print(f"🔐 SSL Handshake: {status}")
            
            return {
                "success": success,
                "status": status,
                "output": result.stdout[:200] if result.stdout else "",
                "error": result.stderr[:200] if result.stderr else ""
            }
            
        except Exception as e:
            print(f"🔐 SSL Handshake: ❌ {e}")
            return {"error": str(e), "status": "❌"}
    
    def _test_http_response(self):
        """Test HTTP response"""
        try:
            response = requests.get(
                f'https://{self.domain}/api/v3/info',
                timeout=30,
                verify=False  # Skip cert verification for now
            )
            
            status = "✅" if response.status_code == 200 else "⚠️"
            
            print(f"🌐 HTTP Response: {status} Status {response.status_code}")
            
            return {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "status": status,
                "response_size": len(response.content)
            }
            
        except Exception as e:
            print(f"🌐 HTTP Response: ❌ {e}")
            return {"error": str(e), "status": "❌"}
    
    def generate_fix_recommendations(self, investigation_results, connectivity_results):
        """Generate specific fix recommendations"""
        print("\n🎯 PHASE 3: Fix Recommendations")
        print("="*50)
        
        recommendations = []
        
        # Analyze results and generate recommendations
        if connectivity_results["dns"]["status"] == "❌":
            recommendations.append({
                "priority": "HIGH",
                "action": "Fix DNS resolution",
                "details": "Domain not resolving correctly"
            })
        
        if connectivity_results["port"]["status"] == "❌":
            recommendations.append({
                "priority": "HIGH", 
                "action": "Configure port forwarding or proxy",
                "details": f"Port {self.port} not accessible from external network"
            })
        
        if connectivity_results["ssl"]["status"] == "❌":
            recommendations.append({
                "priority": "MEDIUM",
                "action": "Fix SSL certificate configuration",
                "details": "SSL handshake failing"
            })
        
        # Check if this is a local development vs production issue
        recommendations.append({
            "priority": "HIGH",
            "action": "Configure reverse proxy or tunnel",
            "details": "Local API server needs external routing (ngrok, nginx, cloudflare tunnel)"
        })
        
        print("💡 Recommended Actions:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. [{rec['priority']}] {rec['action']}")
            print(f"      → {rec['details']}")
        
        return recommendations
    
    def run_complete_diagnosis(self):
        """Run complete domain configuration diagnosis"""
        print("🌐 DOMAIN CONFIGURATION AGENT - COMPLETE DIAGNOSIS")
        print("="*60)
        print(f"🎯 Mission: Restore {self.domain} API connectivity")
        print()
        
        # Phase 1: Historical investigation
        investigation = self.investigate_domain_history()
        
        # Phase 2: Current connectivity
        connectivity = self.diagnose_current_connectivity()
        
        # Phase 3: Recommendations
        recommendations = self.generate_fix_recommendations(investigation, connectivity)
        
        # Generate report
        report = {
            "timestamp": datetime.now().isoformat(),
            "domain": self.domain,
            "investigation": investigation,
            "connectivity": connectivity,
            "recommendations": recommendations,
            "agent": "DomainConfigAgent"
        }
        
        # Save report
        report_path = "reports/domain_config_diagnosis.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Full diagnosis saved to: {report_path}")
        
        return report

def main():
    """Main function"""
    agent = DomainConfigAgent()
    report = agent.run_complete_diagnosis()
    
    print("\n🎉 DOMAIN CONFIGURATION AGENT - MISSION SUMMARY")
    print("="*60)
    print("✅ Historical analysis complete")
    print("✅ Connectivity diagnosis complete") 
    print("✅ Fix recommendations generated")
    print()
    print("👨‍💻 Ready to restore external API connectivity!")
    
    return report

if __name__ == "__main__":
    main()