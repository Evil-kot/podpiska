import yaml
import requests
import time
import socket
from base64 import b64decode, b64encode

SUBSCRIPTION_URL = "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt"
OUTPUT_FILE = "BLACK_VLESS_RUS_FILTERED.txt"
TOP_N = 15
TIMEOUT = 2

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
    print("Downloading subscription...")
    try:
        resp = requests.get(SUBSCRIPTION_URL, timeout=30)
        config = yaml.safe_load(b64decode(resp.text))
    except Exception as e:
        print("Error:", str(e))
        return

    proxies = config.get("proxies", [])
    print("Total proxies:", len(proxies))

    results = []
    for i, p in enumerate(proxies):
        name = p.get("name", "Unknown")
        host = p.get("server")
        port = p.get("port", 443)
        
        if not host:
            continue
            
        latency = get_latency(host, port)
        if latency:
            results.append((p, latency))
            print(i+1, name, latency, "ms")
        time.sleep(0.05)

    results.sort(key=lambda x: x[1])
    top = [p for p, _ in results[:TOP_N]]

    output = {"proxies": top}
    yaml_str = yaml.dump(output, default_flow_style=False, sort_keys=False)
    encoded = b64encode(yaml_str.encode()).decode()

    with open(OUTPUT_FILE, "w") as f:
        f.write(encoded)
    
    print("Saved", OUTPUT_FILE)

if __name__ == "__main__":
    main()
