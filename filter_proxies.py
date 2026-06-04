import yaml
import requests
import time
import socket
from base64 import b64decode, b64encode

SUBSCRIPTION_URL = "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt"
OUTPUT_FILE = "BLACK_VLESS_RUS_FILTERED.txt"
TOP_N = 15
TIMEOUT = 2

def decode_subscription(url):
    response = requests.get(url, headers={
        'User-Agent': 'ClashMeta/1.19.24; mihomo/1.19.24',
        'x-hwid': '97E4A17D0627'
    })
    
    try:
        decoded = b64decode(response.text).decode('utf-8')
        return yaml.safe_load(decoded)
    except:
        return yaml.safe_load(response.text)

def ping_server(server):
    try:
        host = server.get('server')
        port = server.get('port', 443)
        
        if not host:
            return None
        
        start = time.time()
        sock = socket.create_connection((host, port), timeout=TIMEOUT)
        sock.close()
        latency = (time.time() - start) * 1000
        
        return latency
    except Exception:
        return None

def filter_proxies():
    print("Downloading subscription: " + SUBSCRIPTION_URL)
    config = decode_subscription(SUBSCRIPTION_URL)
    
    if not config or 'proxies' not in config:
        print("Error: failed to get proxy list")
        return
    
    proxies = config['proxies']
    print("Total proxies: " + str(len(proxies)))
    
    print("Pinging proxies...")
    results = []
    
    for i, proxy in enumerate(proxies, 1):
        name = proxy.get('name', 'Unknown')
        latency = ping_server(proxy)
        
        if latency is not None:
            results.append((proxy, latency))
            print("  [" + str(i) + "/" + str(len(proxies)) + "] OK " + name + ": " + str(int(latency)) + "ms")
        else:
            print("  [" + str(i) + "/" + str(len(proxies)) + "] FAIL " + name + ": timeout")
        
        time.sleep(0.1)
    
    results.sort(key=lambda x: x[1])
    
    top_proxies = [proxy for proxy, _ in results[:TOP_N]]
    
    print("")
    print("Top " + str(TOP_N) + " proxies:")
    for i, (proxy, latency) in enumerate(results[:TOP_N], 1):
        print("  " + str(i) + ". " + proxy.get('name') + ": " + str(int(latency)) + "ms")
    
    filtered_config = {
        'proxies': top_proxies
    }
    
    yaml_str = yaml.dump(filtered_config, allow_unicode=True, default_flow_style=False)
    encoded = b64encode(yaml_str.encode('utf-8')).decode('ascii')
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(encoded)
    
    print("")
    print("Saved to " + OUTPUT_FILE)

if __name__ == "__main__":
    filter_proxies()
