import requests
import time
import socket
from base64 import b64decode, b64encode

print("=" * 50)
print("Starting dual subscription filter...")
print("=" * 50)

# Настройки для двух подписок
SUBSCRIPTIONS = [
    {
        "url": "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt",
        "output": "BLACK_VLESS_RUS_FILTERED.txt",
        "name": "BLACK (mobile)",
        "top_n": 5,
        "filter_countries": True  # Фильтровать по странам
    },
    {
        "url": "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt",
        "output": "WHITE_LIST_FILTERED.txt",
        "name": "WHITE (bypass)",
        "top_n": 15,
        "filter_countries": False  # Без фильтра по странам
    }
]

TIMEOUT = 3

# Список разрешенных стран (только для BLACK подписки)
ALLOWED_COUNTRIES = [
    "Austria",
    "Germany", 
    "Netherlands",
    "Finland",
    "Poland",
    "Armenia",
    "Hungary",
    "Turkey"
]

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

def process_subscription(sub_config):
    url = sub_config["url"]
    output_file = sub_config["output"]
    name = sub_config["name"]
    top_n = sub_config["top_n"]
    filter_countries = sub_config["filter_countries"]
    
    print("\n" + "=" * 50)
    print(f"Processing: {name}")
    print("=" * 50)
    
    print("Step 1: Downloading subscription...")
    try:
        response = requests.get(url, timeout=30)
        print("  Status:", response.status_code)
        
        if response.status_code != 200:
            print("  ERROR: Failed to download")
            return
        
        try:
            decoded = b64decode(response.text.strip()).decode('utf-8', errors='ignore')
            proxy_lines = decoded.strip().split('\n')
            print("  Decoded from base64")
        except:
            proxy_lines = response.text.strip().split('\n')
            print("  Using raw text")
        
        print("  Total lines:", len(proxy_lines))
        
    except Exception as e:
        print("  ERROR:", str(e))
        return

    print("Step 2: Filtering...")
    filtered_lines = []
    
    for line in proxy_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        if filter_countries:
            # Фильтруем по странам
            country_found = False
            for country in ALLOWED_COUNTRIES:
                if country in line:
                    filtered_lines.append(line)
                    country_found = True
                    break
            if not country_found:
                continue
        else:
            # Берём все сервера
            filtered_lines.append(line)
    
    print("  Filtered proxies:", len(filtered_lines))

    if not filtered_lines:
        print("  ERROR: No proxies after filtering")
        return

    print("Step 3: Testing latency...")
    results = []
    
    for i, line in enumerate(filtered_lines, 1):
        name_proxy = line.split("://")[0] if "://" in line else "proxy"
        if "#" in line:
            name_proxy = line.split("#")[-1]
        
        if "://" in line:
            parts = line.split("://")
            if len(parts) > 1:
                auth_host = parts[1]
                if "@" in auth_host:
                    host_port = auth_host.split("@")[-1]
                else:
                    host_port = auth_host
                
                host_port = host_port.split("/")[0].split("?")[0]
                
                if ":" in host_port:
                    host, port = host_port.rsplit(":", 1)
                    try:
                        port = int(port)
                    except:
                        port = 443
                    
                    latency = get_latency(host, port)
                    
                    if latency is not None:
                        results.append((line, latency, name_proxy))
                        print("  ", i, name_proxy, latency, "ms")
                    else:
                        print("  ", i, "FAIL:", name_proxy)
        
        time.sleep(0.05)

    if not results:
        print("  ERROR: No working proxies found")
        return

    print("Step 4: Sorting...")
    results.sort(key=lambda x: x[1])

    top_proxies = results[:top_n]

    print("Step 5: Top", top_n, "proxies for", name + ":")
    for i, (proxy, latency, proxy_name) in enumerate(top_proxies, 1):
        print("  ", i, proxy_name, "-", latency, "ms")

    print("Step 6: Saving to", output_file + "...")
    try:
        output_lines = [proxy for proxy, _, _ in top_proxies]
        output_text = '\n'.join(output_lines)
        encoded = b64encode(output_text.encode('utf-8')).decode('ascii')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(encoded)
        
        print("  Saved to", output_file)
        print("  Total proxies:", len(top_proxies))
    except Exception as e:
        print("  ERROR saving:", str(e))
        return

def main():
    for sub in SUBSCRIPTIONS:
        process_subscription(sub)
    
    print("\n" + "=" * 50)
    print("All subscriptions processed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
