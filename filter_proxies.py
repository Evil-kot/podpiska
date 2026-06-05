import requests
import time
import socket
from base64 import b64decode, b64encode
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- НАСТРОЙКИ ---
# Добавь сюда свои подписки. Для каждой укажи URL, имя выходного файла и название для лога.
SUBSCRIPTIONS = [
    {
        "url": "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt",
        "output": "BLACK_VLESS_RUS_FILTERED.txt",
        "name": "Main Subscription"
    },
    {
        "url": "https://raw.githubusercontent.com/zieng2/wl/main/vless_universal.txt",
        "output": "MOBILE_BYPASS_FILTERED.txt",
        "name": "Second Subscription"
    }
]

TOP_N = 10
TIMEOUT = 3
MAX_WORKERS = 20
# -----------------

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

def test_proxy(line):
    if "://" not in line:
        return None
    name = line.split("://")[0]
    if "#" in line:
        name = line.split("#")[-1]
    parts = line.split("://")[1]
    if "@" in parts:
        host_port = parts.split("@")[-1]
    else:
        host_port = parts
    host_port = host_port.split("/")[0].split("?")[0]
    if ":" not in host_port:
        return None
    host, port = host_port.rsplit(":", 1)
    try:
        port = int(port)
    except:
        port = 443
    latency = get_latency(host, port)
    if latency:
        return (line, latency, name)
    return None

def process_subscription(sub_info):
    url = sub_info["url"]
    output_file = sub_info["output"]
    name = sub_info["name"]
    
    print(f"\n{'='*50}")
    print(f"Processing: {name}")
    print(f"{'='*50}")
    
    print(f"Downloading {name}...")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"ERROR: Failed to download {name}")
            return
        
        try:
            decoded = b64decode(response.text.strip()).decode('utf-8', errors='ignore')
            proxy_lines = decoded.strip().split('\n')
        except:
            proxy_lines = response.text.strip().split('\n')
        
        print(f"Found {len(proxy_lines)} proxies")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return

    print(f"Testing proxies (parallel, {MAX_WORKERS} workers)...")
    results = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_proxy = {executor.submit(test_proxy, line): line for line in proxy_lines if line.strip()}
        
        completed = 0
        for future in as_completed(future_to_proxy):
            completed += 1
            result = future.result()
            if result:
                results.append(result)
                print(f"  [{completed}/{len(proxy_lines)}] OK {result[1]}ms: {result[2]}")
            else:
                print(f"  [{completed}/{len(proxy_lines)}] FAIL")

    if not results:
        print(f"ERROR: No working proxies found for {name}")
        return

    results.sort(key=lambda x: x[1])
    top_proxies = results[:TOP_N]

    print(f"Top {TOP_N} proxies for {name}:")
    for i, (proxy, latency, proxy_name) in enumerate(top_proxies, 1):
        print(f"  {i}. {proxy_name} - {latency}ms")

    print(f"Saving to {output_file}...")
    try:
        output_lines = [proxy for proxy, _, _ in top_proxies]
        output_text = '\n'.join(output_lines)
        encoded = b64encode(output_text.encode('utf-8')).decode('ascii')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(encoded)
        
        print(f"Saved {len(top_proxies)} proxies to {output_file}")
    except Exception as e:
        print(f"ERROR saving: {str(e)}")

def main():
    print("Starting multi-subscription filter...")
    for sub in SUBSCRIPTIONS:
        process_subscription(sub)
    print("\n" + "="*50)
    print("All done!")
    print("="*50)

if __name__ == "__main__":
    main()
