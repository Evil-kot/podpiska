import requests
import time
import socket
import ssl
from base64 import b64decode, b64encode
from concurrent.futures import ThreadPoolExecutor, as_completed

print("=" * 50)
print("Starting proxy filter with SNI + HTTP test...")
print("=" * 50)

SUBSCRIPTION_URL = "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt"
OUTPUT_FILE = "BLACK_VLESS_RUS_FILTERED.txt"
TOP_N = 5
TIMEOUT = 3
MAX_WORKERS = 20

# SNI для тестирования
TEST_SNI = "ya.ru"

def test_with_sni(host, port):
    """Test TCP connection with specific SNI"""
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        
        ssock = context.wrap_socket(sock, server_hostname=TEST_SNI)
        
        start = time.time()
        ssock.connect((host, port))
        ssock.close()
        latency = int((time.time() - start) * 1000)
        
        return latency
    except:
        return None

def test_proxy(line):
    """Test single proxy"""
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
    
    latency = test_with_sni(host, port)
    
    if latency:
        return (line, latency, name)
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

    print(f"Step 2: Testing with SNI={TEST_SNI} (parallel, {MAX_WORKERS} workers)...")
    start_time = time.time()
    
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
    for i, (proxy, latency, name) in enumerate(top_proxies, 1):
        print(f"  {i}. {name} - {latency}ms")

    print("Step 5: Saving...")
    try:
        output_lines = [proxy for proxy, _, _ in top_proxies]
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
