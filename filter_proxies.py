import requests
import time
import socket
from base64 import b64decode, b64encode

print("=" * 50)
print("Starting proxy filter...")
print("=" * 50)

SUBSCRIPTION_URL = "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt"
OUTPUT_FILE = "BLACK_VLESS_RUS_FILTERED.txt"
TOP_N = 15
TIMEOUT = 3

# Список разрешенных стран (только те, что работают из России)
ALLOWED_COUNTRIES = [
    "Austria",
    "Germany", 
    "Netherlands",
    "Finland",
    "Poland",
    "Armenia",
    "Hungary",
    "Turkey"
]

def get_latency(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        start = time.time()
        sock.connect((host, port))
        sock.close()
        return int((time.time() - start) * 1000)
    except:
        return None

def main():
    print("Step 1: Downloading subscription...")
    try:
        response = requests.get(SUBSCRIPTION_URL, timeout=30)
        print("Status:", response.status_code)
        
        if response.status_code != 200:
            print("ERROR: Failed to download")
            return
        
        try:
            decoded = b64decode(response.text.strip()).decode('utf-8', errors='ignore')
            proxy_lines = decoded.strip().split('\n')
            print("Decoded from base64")
        except:
            proxy_lines = response.text.strip().split('\n')
            print("Using raw text")
        
        print("Total lines:", len(proxy_lines))
        
    except Exception as e:
        print("ERROR:", str(e))
        return

    print("Step 2: Filtering by country...")
    filtered_lines = []
    
    for line in proxy_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Проверяем, есть ли в названии разрешенная страна
        for country in ALLOWED_COUNTRIES:
            if country in line:
                filtered_lines.append(line)
                break
    
    print("Filtered proxies:", len(filtered_lines))

    if not filtered_lines:
        print("ERROR: No proxies from allowed countries")
        return

    print("Step 3: Testing latency...")
    results = []
    
    for i, line in enumerate(filtered_lines, 1):
        name = line.split("://")[0] if "://" in line else "proxy"
        if "#" in line:
            name = line.split("#")[-1]
        
        if "://" in line:
            parts = line.split("://")
            if len(parts) > 1:
                auth_host = parts[1]
                if "@" in auth_host:
                    host_port = auth_host.split("@")[-1]
                else:
                    host_port = auth_host
                
                host_port = host_port.split("/")[0].split("?")[0]
                
                if ":" in host_port:
                    host, port = host_port.rsplit(":", 1)
                    try:
                        port = int(port)
                    except:
                        port = 443
                    
                    latency = get_latency(host, port)
                    
                    if latency is not None:
                        results.append((line, latency, name))
                        print(i, name, latency, "ms")
                    else:
                        print(i, "FAIL:", name)
        
        time.sleep(0.05)

    if not results:
        print("ERROR: No working proxies found")
        return

    print("Step 4: Sorting...")
    results.sort(key=lambda x: x[1])

    top_proxies = results[:TOP_N]

    print("Step 5: Top", TOP_N, "proxies:")
    for i, (proxy, latency, name) in enumerate(top_proxies, 1):
        print(i, name, "-", latency, "ms")

    print("Step 6: Saving...")
    try:
        output_lines = [proxy for proxy, _, _ in top_proxies]
        output_text = '\n'.join(output_lines)
        encoded = b64encode(output_text.encode('utf-8')).decode('ascii')
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(encoded)
        
        print("Saved to", OUTPUT_FILE)
        print("Total proxies:", len(top_proxies))
    except Exception as e:
        print("ERROR saving:", str(e))
        return

    print("=" * 50)
    print("Done!")
    print("=" * 50)

if __name__ == "__main__":
    main()
