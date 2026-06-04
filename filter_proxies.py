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
TIMEOUT = 3

def get_latency_from_proxy(proxy_line):
    """Extract host:port from proxy line and test latency"""
    try:
        # Try to parse vless:// or other proxy formats
        if "://" in proxy_line:
            # Extract from vless://user@host:port or similar
            parts = proxy_line.split("://")
            if len(parts) > 1:
                auth_host = parts[1]
                if "@" in auth_host:
                    host_port = auth_host.split("@")[-1]
                else:
                    host_port = auth_host
                
                # Remove path and query params
                host_port = host_port.split("/")[0].split("?")[0]
                
                if ":" in host_port:
                    host, port = host_port.rsplit(":", 1)
                    port = int(port)
                    
                    # Test connection
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
    print("  URL:", SUBSCRIPTION_URL)
    
    try:
        response = requests.get(SUBSCRIPTION_URL, timeout=30)
        print("  Status code:", response.status_code)
        print("  Response length:", len(response.text), "bytes")
        
        if response.status_code != 200:
            print("  ERROR: Failed to download")
            return
        
        # Try to decode as base64 first
        try:
            decoded = b64decode(response.text.strip()).decode('utf-8', errors='ignore')
            proxy_lines = decoded.strip().split('\n')
            print("  Decoded from base64")
        except Exception:
            # If not base64, use as is
            proxy_lines = response.text.strip().split('\n')
            print("  Using raw text")
        
        print("  Total lines:", len(proxy_lines))
        
    except Exception as e:
        print("  ERROR:", str(e))
        return

    print("Step 2: Testing latency...")
    results = []
    
    for i, line in enumerate(proxy_lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Get a name for display
        name = line.split("://")[0] if "://" in line else "proxy"
        if "#" in line:
            name = line.split("#")[-1]
        
        latency = get_latency_from_proxy(line)
        
        if latency is not None:
            results.append((line, latency, name))
            print("  [", i, "/", len(proxy_lines), "] OK", latency, "ms:", name)
        else:
            print("  [", i, "/", len(proxy_lines), "] FAIL:", name)
        
        time.sleep(0.05)

    if not results:
        print("  ERROR: No working proxies found")
        return

    print("Step 3: Sorting by latency...")
    results.sort(key=lambda x: x[1])

    top_proxies = results[:TOP_N]

    print("Step 4: Top", TOP_N, "proxies:")
    for i, (proxy, latency, name) in enumerate(top_proxies, 1):
        print("  ", i, ".", name, "-", latency, "ms")

    print("Step 5: Saving filtered subscription...")
    
    # Save in base64 encoded format (standard for subscription)
    output_lines = [proxy for proxy, _, _ in top_proxies]
    output_text = '\n'.join(output_lines)
    encoded = b64encode(output_text.encode('utf-8')).decode('ascii')
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(encoded)
    
    print("  Saved to", OUTPUT_FILE)
    print("  Total proxies:", len(top_proxies))
    print("=" * 50)
    print("Done!")
    print("=" * 50)

if __name__ == "__main__":
    main()
