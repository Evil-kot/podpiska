import yaml
import requests
import time
import socket
from base64 import b64decode, b64encode
import re

SUBSCRIPTION_URL = "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt"
OUTPUT_FILE = "BLACK_VLESS_RUS_FILTERED.txt"
TOP_N = 15
TIMEOUT = 2

def sanitize_name(name):
    """Remove non-ASCII characters from server name"""
    if not name:
        return "Unknown"
    # Keep only ASCII characters
    return re.sub(r'[^\x00-\x7F]', '', name).strip() or "Unknown"

def get_latency(host, port):
    """Test TCP connection latency"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        start = time.time()
        sock.connect((host, port))
        sock.close()
        return int((time.time() - start) * 1000)
    except Exception:
        return None

def main():
    print("Step 1: Downloading subscription...")
    try:
        resp = requests.get(SUBSCRIPTION_URL, timeout=30)
        resp.raise_for_status()
        raw_data = resp.text.strip()
        print("  Downloaded", len(raw_data), "bytes")
    except Exception as e:
        print("  ERROR: Failed to download:", str(e))
        return

    print("Step 2: Decoding base64...")
    try:
        decoded_bytes = b64decode(raw_data)
        decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
        config = yaml.safe_load(decoded_str)
        print("  Decoded successfully")
    except Exception as e:
        print("  ERROR: Failed to decode:", str(e))
        return

    proxies = config.get("proxies", [])
    print("Step 3: Found", len(proxies), "proxies")

    if not proxies:
        print("  ERROR: No proxies found in subscription")
        return

    print("Step 4: Testing latency...")
    results = []
    for i, p in enumerate(proxies, 1):
        name = p.get("name", "Unknown")
        host = p.get("server")
        port = p.get("port", 443)

        if not host:
            print("  [", i, "/", len(proxies), "] SKIP (no host):", name)
            continue

        latency = get_latency(host, port)
        if latency is not None:
            results.append((p, latency))
            print("  [", i, "/", len(proxies), "] OK", latency, "ms:", name)
        else:
            print("  [", i, "/", len(proxies), "] FAIL:", name)

        time.sleep(0.05)

    if not results:
        print("  ERROR: No working proxies found")
        return

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
        yaml_bytes = yaml_str.encode('utf-8')
        encoded_bytes = b64encode(yaml_bytes)
        encoded_str = encoded_bytes.decode('ascii')

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(encoded_str)

        print("  Saved to", OUTPUT_FILE)
        print("  File size:", len(encoded_str), "bytes")
    except Exception as e:
        print("  ERROR: Failed to save:", str(e))
        return

    print("Step 8: Done!")

if __name__ == "__main__":
    main()
