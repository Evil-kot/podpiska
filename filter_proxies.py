import requests
import time
import socket
from base64 import b64decode, b64encode
import yaml

print("=" * 50)
print("Starting proxy filter...")
print("=" * 50)

SUBSCRIPTION_URL = "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt"
OUTPUT_FILE = "BLACK_VLESS_RUS_FILTERED.txt"
TOP_N = 15
TIMEOUT = 5

def test_proxy_via_http(proxy_line):
    """Test proxy by making HTTP request through it"""
    try:
        # Parse proxy URL
        if "://" not in proxy_line:
            return None
        
        protocol = proxy_line.split("://")[0]
        
        # For vless, vmess, trojan - use requests with proxy
        if protocol in ['vless', 'vmess', 'trojan', 'ss', 'ssr']:
            # Create proxy dict for requests
            proxy_url = proxy_line  # Use full URL
            
            # Test by making request to a known working site
            test_url = "https://httpbin.org/ip"
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            start = time.time()
            response = requests.get(test_url, proxies=proxies, timeout=TIMEOUT)
            latency = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                return latency
        else:
            # For other protocols, try TCP connect
            return test_tcp_connect(proxy_line)
            
    except Exception as e:
        return None

def test_tcp_connect(proxy_line):
    """Fallback: test TCP connection"""
    try:
        if "://" in proxy_line:
            parts = proxy_line.split("://")
            if len(parts) > 1:
                auth_host = parts[1]
                if "@" in auth_host:
                    host_port = auth_host.split("@")[-1]
                else:
                    host_port = auth_host
                
                host_port = host_port.split("/")[0].split("?")[0]
                
                if ":" in host_port:
                    host, port = host_port.rsplit(":", 1)
                    port = int(port)
                    
                    start = time.time()
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(TIMEOUT)
                    sock.connect((host, port))
                    sock.close()
                    return int((time.time() - start) * 1000)
    except Exception:
        pass
    
    return None

def main():
    print("Step 1: Downloading subscription...")
    try:
        response = requests.get(SUBSCRIPTION_URL, timeout=30
