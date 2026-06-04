import yaml
import requests
import time
import socket
import os
from base64 import b64decode, b64encode

# Settings
SUBSCRIPTION_URL = "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt"
OUTPUT_FILE = "BLACK_VLESS_RUS_FILTERED.txt"
TOP_N = 15
TIMEOUT = 2

def decode_subscription(url):
    """Download and decode subscription"""
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
    """Ping server via TCP connect"""
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
    """Main filtering function"""
    print(f"Downloading subscription: {SUBSCRIPTION_URL}")
    config = decode_subscription(SUBSCRIPTION_URL)
    
    if not config or 'proxies' not in config:
        print("Error: failed to get proxy list")
        return
    
    proxies = config['proxies']
    print(f"Total proxies: {len(proxies)}")
    
    print("Pinging proxies...")
    results = []
    
    for i, proxy in enumerate(proxies, 1):
        name = proxy.get('name', 'Unknown')
        latency = ping_server(proxy)
        
        if latency is not None:
            results.append((proxy, latency))
            print(f"  [{i}/{len(proxies)}] OK {name}: {latency:.0f}ms")
        else:
            print(f"  [{i}/{len(proxies)}] FAIL {name}: timeout")
        
        time.sleep(0.1)
    
    results.sort(key=lambda x: x[1])
    
    top_proxies = [proxy for proxy, _ in results[:TOP_N]]
    
    print(f"\nTop {TOP_N} proxies:")
    for i, (proxy, latency) in enumerate(results[:TOP_N], 1):
        print(f"  {i}. {proxy.get('name')}: {latency:.0f}ms")
    
    filtered_config = {
        'proxies': top_proxies,
        'proxy-groups': config.get('proxy-groups', []),
        'rules': config.get('rules', [])
    }
    
    yaml_str = yaml.dump(filtered_config, allow_unicode=True, default_flow_style=False)
    encoded = b64encode(yaml_str.encode('utf-8')).decode('ascii')
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(encoded)
    
    print(f"\nSaved to {OUTPUT_FILE}")

if __name__ == "__main__":
    filter_proxies()
