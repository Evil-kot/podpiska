import requests
import time
import socket
import ssl
from base64 import b64decode, b64encode

print("=" * 50)
print("Starting dual subscription filter...")
print("=" * 50)

# === НАСТРОЙКИ ДВУХ ПОДПИСОК ===
SUBSCRIPTIONS = [
    {
        "url": "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS_mobile.txt",
        "output": "BLACK_VLESS_RUS_FILTERED.txt",
        "name": "BLACK (mobile)",
        "top_n": 5,
        "filter_countries": True,
        "use_sni_test": True
    },
    {
        "url": "https://raw.githack.com/igareck/vpn-configs-for-russia/main/BLACK_VLESS_RUS.txt",
        "output": "WHITE_LIST_FILTERED.txt",
        "name": "WHITE (bypass)",
        "top_n": 15,
        "filter_countries": False,
        "use_sni_test": False
    }
]

TIMEOUT = 3

# Разрешённые страны (только для BLACK подписки)
ALLOWED_COUNTRIES = [
    "Austria", "Germany", "Netherlands",
    "Finland", "Poland", "Armenia",
    "Hungary", "Turkey"
]

# SNI для теста BLACK подписки
TEST_SNI = "ya.ru"
# --------------------------------


def get_latency_tcp(host, port):
    """Обычный TCP-пинг (для белой подписки)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        start = time.time()
        sock.connect((host, port))
        sock.close()
        return int((time.time() - start) * 1000)
    except:
        return None


def get_latency_sni(host, port):
    """TLS-пинг с заданным SNI (для чёрной подписки)"""
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
        return int((time.time() - start) * 1000)
    except:
        return None


def parse_proxy(line):
    """Вытаскивает host и port из строки прокси"""
    if "://" not in line:
        return None, None
    parts = line.split("://")[1]
    host_port = parts.split("@")[-1] if "@" in parts else parts
    host_port = host_port.split("/")[0].split("?")[0]
    if ":" not in host_port:
        return None, None
    host, port = host_port.rsplit(":", 1)
    try:
        port = int(port)
    except:
        port = 443
    return host, port


def get_proxy_name(line):
    """Извлекает имя сервера из строки"""
    if "#" in line:
        return line.split("#")[-1]
    if "://" in line:
        return line.split("://")[0]
    return "proxy"


def process_subscription(sub):
    url = sub["url"]
    output_file = sub["output"]
    name = sub["name"]
    top_n = sub["top_n"]
    filter_countries = sub["filter_countries"]
    use_sni_test = sub["use_sni_test"]

    print("\n" + "=" * 50)
    print(f"Processing: {name}")
    print("=" * 50)

    # === Скачивание ===
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

    # === Фильтрация ===
    print("Step 2: Filtering...")
    filtered_lines = []
    for line in proxy_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if filter_countries:
            if any(country in line for country in ALLOWED_COUNTRIES):
                filtered_lines.append(line)
        else:
            filtered_lines.append(line)

    print("  Filtered proxies:", len(filtered_lines))
    if not filtered_lines:
        print("  ERROR: No proxies after filtering")
        return

    # === Тестирование ===
    test_type = "SNI=" + TEST_SNI if use_sni_test else "TCP"
    print(f"Step 3: Testing latency ({test_type})...")
    results = []

    for i, line in enumerate(filtered_lines, 1):
        proxy_name = get_proxy_name(line)
        host, port = parse_proxy(line)

        if not host:
            print("  ", i, "SKIP (invalid):", proxy_name)
            continue

        if use_sni_test:
            latency = get_latency_sni(host, port)
        else:
            latency = get_latency_tcp(host, port)

        if latency is not None:
            results.append((line, latency, proxy_name))
            print("  ", i, proxy_name, latency, "ms")
        else:
            print("  ", i, "FAIL:", proxy_name)

        time.sleep(0.05)

    if not results:
        print("  ERROR: No working proxies found")
        return

    # === Сортировка и выбор топ-N ===
    print("Step 4: Sorting...")
    results.sort(key=lambda x: x[1])
    top_proxies = results[:top_n]

    print(f"Step 5: Top {top_n} proxies for {name}:")
    for i, (proxy, latency, proxy_name) in enumerate(top_proxies, 1):
        print("  ", i, proxy_name, "-", latency, "ms")

    # === Сохранение ===
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
