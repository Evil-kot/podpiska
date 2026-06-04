import yaml
import requests
import time
import socket
from base64 import b64decode, b64encode
import sys

print("=" * 50)
print("Starting proxy filter...")
print("=" * 50)

SUBSCRIPTION_URL = "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt"
OUTPUT_FILE = "BLACK_VLESS_RUS_FILTERED.txt"
TOP_N = 15
TIMEOUT = 3

try:
    print("Step 1: Downloading subscription...")
    print("  URL:", SUBSCRIPTION_URL)
    
    headers = {
        'User-Agent': 'ClashMeta/1.19.24'
    }
    response = requests.get(SUBSCRIPTION_URL, headers=headers, timeout=30)
    print("  Status code:", response.status_code)
    print("  Response length:", len(response.text), "bytes")
    
    if response.status_code != 200:
        print("  ERROR: Failed to download, status code:", response.status_code)
        sys.exit(1)
    
    raw_data = response.text.strip()
    print("  Raw data length:", len(raw_data))
    
except Exception as e:
    print("  ERROR: Download failed:", str(e))
    sys.exit(1)

try:
    print("Step 2: Decoding base64...")
    decoded_bytes = b64decode(raw_data)
    print("  Decoded bytes:", len(decoded_bytes))
    
    decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
    print("  Decoded string length:", len(decoded_str))
    
    config = yaml.safe_load(decoded_str)
    print("  YAML loaded successfully")
    
except Exception as e:
    print("  ERROR: Decode failed:", str(e))
    print("  Trying alternative parsing...")
    try:
        config = yaml.safe_load(raw_data)
        print("  Alternative parsing successful")
    except Exception as e2:
        print("  ERROR: Alternative parsing also failed:", str(e2))
        sys.exit(1)

proxies = config.get("proxies", []) if config else []
print("Step 3: Found", len(proxies), "proxies")

if not proxies:
    print("  ERROR: No proxies found in config")
    print("  Config keys:", list(config.keys()) if config else "None")
    sys.exit(1)

print("Step 4: Testing latency...")
results = []

for i, p in enumerate(proxies, 1):
    name = p.get("name", "Unknown")
    host = p.get("server")
    port = p.get("port", 443)
    
    if not host:
        print("  [", i, "/", len(proxies), "] SKIP (no host):", name)
        continue
    
    try:
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((host, port))
        sock.close()
        latency = int((time.time() - start) * 1000)
        
        results.append((p, latency))
        print("  [", i, "/", len(proxies), "] OK", latency, "ms:", name)
        
    except Exception as e:
        print("  [", i, "/", len(proxies), "] FAIL:", name, "-", str(e))
    
    time.sleep(0.05)

if not results:
    print("  ERROR: No working proxies found")
    sys.exit(1)

print("Step 5: Sorting by latency...")
results.sort(key=lambda x: x[1])

top_proxies = [p for p, _ in results[:TOP_N]]

print("Step 6: Top", TOP_N, "proxies:")
for i, (p, latency) in enumerate(results[:TOP_N], 1):
    name = p.get("name", "Unknown")
    print("  ", i, ".", name, "-", latency, "ms")

print("Step 7: Saving filtered subscription...")
output = {"proxies": top_proxies}

try:
    yaml_str = yaml.dump(output, default_flow_style=False, sort_keys=False, allow_unicode=True)
    print("  YAML string length:", len(yaml_str))
    
    yaml_bytes = yaml_str.encode('utf-8')
    print("  YAML bytes:", len(yaml_bytes))
    
    encoded_bytes = b64encode(yaml_bytes)
    print("  Encoded bytes:", len(encoded_bytes))
    
    encoded_str = encoded_bytes.decode('ascii')
    print("  Encoded string:", len(encoded_str))
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(encoded_str)
    
    print("  File saved successfully!")
    print("  Output file:", OUTPUT_FILE)
    
except Exception as e:
    print("  ERROR: Save failed:", str(e))
    sys.exit(1)

print("=" * 50)
print("Done!")
print("=" * 50)
