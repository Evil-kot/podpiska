import requests
import time
from base64 import b64decode, b64encode

print("=" * 50)
print("Starting proxy filter (Russia check)...")
print("=" * 50)

SUBSCRIPTION_URL = "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt"
OUTPUT_FILE = "BLACK_VLESS_RUS_FILTERED.txt"
TOP_N = 10
TIMEOUT = 10
TEST_URL = "http://yandex.ru"

def test_proxy_via_http(proxy_line):
    """Test proxy by making HTTP request through it to Russian site"""
    try:
        # Create proxy dict for requests
        proxies = {
            'http': proxy_line,
            'https': proxy_line
        }
        
        # Test by making request to Yandex
        start = time.time()
        response = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT, allow_redirects=True)
        latency = int((time.time() - start) * 1000)
        
        if response.status_code == 200:
            return latency
        else:
            return None
            
    except Exception as e:
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

    print("Step 2: Testing proxies via HTTP to Yandex...")
    results = []
    
    for i, line in enumerate(proxy_lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        name = line.split("://")[0] if "://" in line else "proxy"
        if "#" in line:
            name = line.split("#")[-1]
        
        print(i, "Testing:", name, "...", end=" ")
        
        latency = test_proxy_via_http(line)
        
        if latency is not None:
            results.append((line, latency, name))
            print("OK", latency, "ms")
        else:
            print("FAIL")
        
        time.sleep(0.1)

    if not results:
        print("ERROR: No working proxies found")
        return

    print("Step 3: Sorting by latency...")
    results.sort(key=lambda x: x[1])

    top_proxies = results[:TOP_N]

    print("Step 4: Top", TOP_N, "working proxies:")
    for i, (proxy, latency, name) in enumerate(top_proxies, 1):
        print(i, name, "-", latency, "ms")

    print("Step 5: Saving...")
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
