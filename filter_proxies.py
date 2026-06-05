import requests
import time
from base64 import b64decode, b64encode

print("=" * 50)
print("Starting proxy filter (HTTP test)...")
print("=" * 50)

SUBSCRIPTION_URL = "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt"
OUTPUT_FILE = "BLACK_VLESS_RUS_FILTERED.txt"
TOP_N = 15
TIMEOUT = 8
TEST_URL = "http://google.com"

# Разрешённые страны
ALLOWED_COUNTRIES = [
    "Austria", "Germany", "Netherlands", 
    "Finland", "Poland", "Armenia", 
    "Hungary", "Turkey"
]

def test_proxy_http(proxy_line):
    """Test proxy by making HTTP request through it"""
    try:
        # Create proxy dict
        proxies = {
            'http': proxy_line,
            'https': proxy_line
        }
        
        # Make request through proxy
        start = time.time()
        response = requests.get(
            TEST_URL, 
            proxies=proxies, 
            timeout=TIMEOUT,
            allow_redirects=True
        )
        latency = int((time.time() - start) * 1000)
        
        # Check if we got a response
        if response.status_code in [200, 301, 302]:
            return latency
        else:
            return None
            
    except Exception:
        return None

def main():
    print("Step 1: Downloading subscription...")
    try:
        response = requests.get(SUBSCRIPTION_URL, timeout=30)
        if response.status_code != 200:
            print("ERROR: Failed to download")
            return
        
        try:
            decoded = b64decode(response.text.strip()).decode('utf-8', errors='ignore')
            proxy_lines = decoded.strip().split('\n')
        except:
            proxy_lines = response.text.strip().split('\n')
        
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
        
        for country in ALLOWED_COUNTRIES:
            if country in line:
                filtered_lines.append(line)
                break
    
    print("Filtered proxies:", len(filtered_lines))

    if not filtered_lines:
        print("ERROR: No proxies from allowed countries")
        return

    print("Step 3: Testing proxies via HTTP...")
    results = []
    
    for i, line in enumerate(filtered_lines, 1):
        name = line.split("://")[0] if "://" in line else "proxy"
        if "#" in line:
            name = line.split("#")[-1]
        
        print(i, "Testing:", name, "...", end=" ", flush=True)
        
        # Try 2 times
        latency = test_proxy_http(line)
        if latency is None:
            time.sleep(0.5)
            latency = test_proxy_http(line)
        
        if latency is not None:
            results.append((line, latency, name))
            print("OK", latency, "ms")
        else:
            print("FAIL")
        
        time.sleep(0.1)

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
