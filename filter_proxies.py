import requests
import time
import socket
from base64 import b64decode, b64encode
from concurrent.futures import ThreadPoolExecutor, as_completed

print("=" * 50)
print("Starting proxy filter (PARALLEL MODE)...")
print("=" * 50)

SUBSCRIPTION_URL = "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt"
OUTPUT_FILE = "BLACK_VLESS_RUS_FILTERED.txt"
TOP_N = 10
TIMEOUT = 3
MAX_WORKERS = 20  # Тестируем 20 серверов одновременно!

def test_proxy_latency(proxy_line):
    """Test single proxy latency"""
    try:
        if "://" not in proxy_line:
            return None
        
        # Extract host:port
        parts = proxy_line.split("://")[1]
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
        
        # Test TCP connection
        start = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((host, port))
        sock.close()
        latency = int((time.time() - start) * 1000)
        
        return (proxy_line, latency)
        
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
        
        print(f"  Found {len(proxy_lines)} proxies")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return

    print(f"Step 2: Testing {len(proxy_lines)} proxies (parallel, {MAX_WORKERS} workers)...")
    start_time = time.time()
    
    # Parallel testing with ThreadPoolExecutor
    results = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_proxy = {executor.submit(test_proxy_latency, line): line for line in proxy_lines if line.strip()}
        
        completed = 0
        for future in as_completed(future_to_proxy):
            completed += 1
            result = future.result()
            
            if result:
                results.append(result)
                proxy_line = result[0]
                latency = result[1]
                name = proxy_line.split("#")[-1] if "#" in proxy_line else "proxy"
                print(f"  [{completed}/{len(proxy_lines)}] OK {latency}ms: {name}")
            else:
                print(f"  [{completed}/{len(proxy_lines)}] FAIL")

    elapsed = time.time() - start_time
    print(f"\n  Tested in {elapsed:.1f} seconds")
    print(f"  Working proxies: {len(results)}")

    if not results:
        print("ERROR: No working proxies found")
        return

    print("Step 3: Sorting by latency...")
    results.sort(key=lambda x: x[1])

    top_proxies = results[:TOP_N]

    print(f"Step 4: Top {TOP_N} proxies:")
    for i, (proxy, latency) in enumerate(top_proxies, 1):
        name = proxy.split("#")[-1] if "#" in proxy else "proxy"
        print(f"  {i}. {name} - {latency}ms")

    print("Step 5: Saving...")
    try:
        output_lines = [proxy for proxy, _ in top_proxies]
        output_text = '\n'.join(output_lines)
        encoded = b64encode(output_text.encode('utf-8')).decode('ascii')
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(encoded)
        
        print(f"  Saved to {OUTPUT_FILE}")
        print(f"  Total proxies: {len(top_proxies)}")
    except Exception as e:
        print(f"ERROR saving: {str(e)}")
        return

    print("=" * 50)
    print("Done!")
    print("=" * 50)

if __name__ == "__main__":
    main()
