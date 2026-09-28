import streamlit as st
import ipaddress
import socket
import subprocess
import platform
import re
import csv
import io
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# NetworkScope - Local Network Discovery
# ============================================================

st.set_page_config(
    page_title="NetworkScope",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container { max-width: 1400px; padding-top: 2rem; }
        .main-title { font-size: 2.5rem; font-weight: 800; margin-bottom: .2rem; }
        .subtitle { color: #777; margin-bottom: 2rem; }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(128,128,128,.2);
            padding: 15px;
            border-radius: 14px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "results" not in st.session_state:
    st.session_state.results = []

if "last_network" not in st.session_state:
    st.session_state.last_network = ""

# ------------------------------------------------------------
# Local network detection
# ------------------------------------------------------------

def get_local_ip():
    """Return the IPv4 address used by this machine for local networking."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("192.0.2.1", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return ""


def prefix_from_mask(mask):
    try:
        return ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
    except Exception:
        return None


def get_local_networks():
    """
    Discover IPv4 networks configured on the machine.

    psutil is preferred because it gives the actual interface netmask.
    A small fallback is included for systems without psutil.
    """
    networks = []

    try:
        import psutil

        for iface, addresses in psutil.net_if_addrs().items():
            for addr in addresses:
                if addr.family != socket.AF_INET:
                    continue
                ip = addr.address
                mask = addr.netmask
                if not ip or not mask:
                    continue
                try:
                    network = ipaddress.ip_network(
                        f"{ip}/{mask}", strict=False
                    )
                    if network.version == 4 and network.is_private:
                        networks.append({
                            "interface": iface,
                            "ip": ip,
                            "netmask": mask,
                            "cidr": str(network),
                        })
                except ValueError:
                    pass
    except Exception:
        ip = get_local_ip()
        if ip:
            # Fallback only. A plain IP cannot reveal the true subnet size.
            parts = ip.split(".")
            if len(parts) == 4:
                networks.append({
                    "interface": "Unknown",
                    "ip": ip,
                    "netmask": "255.255.255.0",
                    "cidr": f"{parts[0]}.{parts[1]}.{parts[2]}.0/24",
                })

    # Remove duplicates while preserving order.
    unique = []
    seen = set()
    for item in networks:
        if item["cidr"] not in seen:
            seen.add(item["cidr"])
            unique.append(item)

    return unique


def resolve_scan_target(value):
    """
    Accept:
      192.168.1.0/24
      192.168.1.20

    For a plain IP, use the actual local interface network when possible.
    If the IP is not one of this machine's local addresses, fall back to
    /24 and clearly tell the user that CIDR is more accurate.
    """
    value = value.strip()
    if not value:
        raise ValueError("أدخل IP أو Network CIDR.")

    # CIDR supplied directly.
    if "/" in value:
        network = ipaddress.ip_network(value, strict=False)
        if network.version != 4:
            raise ValueError("الإصدار المدعوم حاليًا هو IPv4 فقط.")
        return network, "تم استخدام الـ CIDR الذي أدخلته."

    # Plain IPv4 address.
    try:
        target_ip = ipaddress.ip_address(value)
    except ValueError:
        raise ValueError("عنوان IP غير صحيح.")

    if target_ip.version != 4:
        raise ValueError("الإصدار المدعوم حاليًا هو IPv4 فقط.")

    local_networks = get_local_networks()

    # If the entered IP belongs to one of this machine's interfaces,
    # use that interface's actual subnet.
    for item in local_networks:
        network = ipaddress.ip_network(item["cidr"], strict=False)
        if target_ip in network:
            return network, (
                f"تم اكتشاف الشبكة تلقائيًا من الواجهة {item['interface']}: "
                f"{network}"
            )

    # Safe convenience fallback. Tell the user that CIDR is preferable.
    parts = str(target_ip).split(".")
    network = ipaddress.ip_network(
        f"{parts[0]}.{parts[1]}.{parts[2]}.0/24",
        strict=False,
    )
    return network, (
        "لم أجد هذا الـ IP على واجهة الجهاز؛ تم افتراض /24. "
        "إذا كانت الشبكة مختلفة، أدخلها بصيغة CIDR مثل 10.10.0.0/16."
    )


# ------------------------------------------------------------
# Discovery
# ------------------------------------------------------------

def ping(ip):
    system = platform.system().lower()
    try:
        if system == "windows":
            command = ["ping", "-n", "1", "-w", "500", ip]
        else:
            command = ["ping", "-c", "1", "-W", "1", ip]
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=1.5,
        )
        return result.returncode == 0
    except Exception:
        return False


@lru_cache(maxsize=1)
def _vendor_lookup():
    try:
        from mac_vendor_lookup import MacLookup
        return MacLookup()
    except Exception:
        return None


def get_mac_vendor(mac):
    """Best-effort OUI lookup. Vendor is evidence, not proof of device type."""
    if not mac:
        return ""
    try:
        lookup = _vendor_lookup()
        if lookup:
            return lookup.lookup(mac)
    except Exception:
        pass
    return ""


def get_netbios_name(ip):
    """Windows NetBIOS lookup; many phones/IoT devices do not advertise it."""
    if platform.system().lower() != "windows":
        return ""
    try:
        result = subprocess.run(
            ["nbtstat", "-A", ip],
            capture_output=True,
            text=True,
            timeout=2.5,
        )
        for line in result.stdout.splitlines():
            match = re.search(r"^\s*([^\s<]{1,40})\s+<00>\s+", line)
            if match and match.group(1) not in {"*", "WORKGROUP"}:
                return match.group(1).strip()
    except Exception:
        pass
    return ""


def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ""


# Common TCP services used only as discovery evidence.
# They do not log in or send application data.
DISCOVERY_PORTS = {
    22: "SSH",
    23: "Telnet",
    53: "DNS",
    80: "HTTP",
    443: "HTTPS",
    445: "SMB",
    515: "LPD Printer",
    554: "RTSP",
    631: "IPP Printer",
    8000: "HTTP-Alt",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
    9100: "JetDirect Printer",
    3389: "RDP",
}


def tcp_probe(ip, port, timeout=0.25):
    """Check whether a TCP service accepts a connection."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((ip, port)) == 0
    except Exception:
        return False


def probe_services(ip, workers=16):
    """Return open common TCP services without authentication or payloads."""
    found = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(tcp_probe, ip, port): (port, name)
            for port, name in DISCOVERY_PORTS.items()
        }
        for future in as_completed(futures):
            port, name = futures[future]
            try:
                if future.result():
                    found.append((port, name))
            except Exception:
                pass
    return sorted(found)


def classify_device(hostname, vendor, services):
    """Conservative classification from hostname/vendor/service evidence."""
    text_value = f"{hostname} {vendor}".lower()
    ports = {p for p, _ in services}

    # Stronger service combinations first.
    if 554 in ports:
        return "كاميرا/جهاز فيديو محتمل", "مرتفعة"
    if ports.intersection({9100, 631, 515}):
        return "طابعة محتملة", "مرتفعة"
    if 445 in ports or 3389 in ports:
        return "حاسب Windows محتمل", "مرتفعة"
    if 22 in ports and ports.intersection({80, 443, 8080, 8443}):
        return "جهاز شبكة/جهاز Linux محتمل", "متوسطة"

    rules = [
        ("كاميرا محتملة", ["camera", "cam", "hikvision", "dahua", "axis", "reolink", "ezviz", "arlo"]),
        ("طابعة محتملة", ["printer", "print", "hp", "hewlett", "epson", "brother", "canon", "lexmark"]),
        ("هاتف/جهاز لوحي محتمل", ["iphone", "ipad", "android", "samsung", "pixel", "oneplus", "xiaomi", "huawei"]),
        ("حاسب محتمل", ["windows", "desktop", "laptop", "macbook", "imac", "pc", "computer", "dell", "lenovo", "asus", "acer", "microsoft", "apple"]),
        ("جهاز شبكة محتمل", ["router", "gateway", "access point", "switch", "ubiquiti", "mikrotik", "cisco", "tp-link", "netgear", "aruba"]),
        ("تلفاز/وسائط محتمل", ["tv", "roku", "chromecast", "firetv", "smarttv", "lg electronics", "sony", "tcl"]),
    ]

    for label, keywords in rules:
        if any(keyword in text_value for keyword in keywords):
            return label, "متوسطة"

    if vendor or services:
        return "جهاز غير محدد", "منخفضة"
    return "غير معروف", "غير متاحة"


def get_arp_table():
    """Read the local ARP/neighbor table."""
    arp = {}
    try:
        system = platform.system().lower()
        if system == "windows":
            output = subprocess.check_output(
                ["arp", "-a"], text=True, stderr=subprocess.DEVNULL
            )
        else:
            try:
                output = subprocess.check_output(
                    ["ip", "neigh"], text=True, stderr=subprocess.DEVNULL
                )
            except Exception:
                output = subprocess.check_output(
                    ["arp", "-a"], text=True, stderr=subprocess.DEVNULL
                )
    except Exception:
        return arp

    ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    mac_pattern = re.compile(r"\b[0-9A-Fa-f]{2}(?:[:-][0-9A-Fa-f]{2}){5}\b")

    for line in output.splitlines():
        ip_match = ip_pattern.search(line)
        mac_match = mac_pattern.search(line)
        if ip_match and mac_match:
            arp[ip_match.group(0)] = mac_match.group(0).replace("-", ":").upper()
    return arp


def scan_network(cidr, workers=32):
    """Multi-signal local discovery: ARP + ICMP + common TCP services."""
    network = ipaddress.ip_network(cidr, strict=False)

    if network.version != 4:
        raise ValueError("هذا الإصدار يدعم IPv4 فقط.")
    if not network.is_private:
        raise ValueError(
            "الفحص المحلي مخصص للشبكات الخاصة. استخدم شبكة تملكها أو لديك تصريح بفحصها."
        )

    hosts = list(network.hosts())
    if len(hosts) > 1024:
        raise ValueError("النطاق كبير جدًا. استخدم نطاقًا أصغر، مثل /24.")

    # Snapshot before the scan: useful when devices already exist in ARP.
    arp_before = get_arp_table()
    candidates = set(ip for ip in arp_before if ipaddress.ip_address(ip) in network)

    progress = st.progress(0, text="اكتشاف الأجهزة: Ping + ARP + الخدمات...")
    completed = 0

    # Phase 1: ICMP. A device does NOT need to answer ICMP to be discovered.
    alive = set()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(ping, str(ip)): str(ip) for ip in hosts}
        for future in as_completed(futures):
            ip = futures[future]
            try:
                if future.result():
                    alive.add(ip)
                    candidates.add(ip)
            except Exception:
                pass
            completed += 1
            progress.progress(
                completed / max(len(hosts), 1),
                text=f"اكتشاف الأجهزة {completed}/{len(hosts)}",
            )

    # Phase 2: TCP discovery for hosts that did not answer ping.
    # This is the key fix for phones/IoT that ignore ICMP.
    tcp_candidates = set()
    with ThreadPoolExecutor(max_workers=min(workers, 32)) as executor:
        futures = {
            executor.submit(probe_services, str(ip)): str(ip)
            for ip in hosts
            if str(ip) not in alive
        }
        for future in as_completed(futures):
            ip = futures[future]
            try:
                services = future.result()
                if services:
                    tcp_candidates.add(ip)
                    candidates.add(ip)
            except Exception:
                pass

    progress.empty()

    # Phase 3: refresh ARP after touching the subnet.
    arp_after = get_arp_table()
    arp = dict(arp_before)
    arp.update(arp_after)

    # Build final records. Probe services only for candidates so the scan
    # does not unnecessarily connect to every port on every address twice.
    records = []
    for ip in sorted(candidates, key=ipaddress.ip_address):
        mac = arp.get(ip, "")
        vendor = get_mac_vendor(mac)
        hostname = get_hostname(ip) or get_netbios_name(ip)
        services = probe_services(ip)
        service_names = ", ".join(name for _, name in services)

        device_type, confidence = classify_device(
            hostname, vendor, services
        )

        evidence = []
        if ip in alive:
            evidence.append("Ping")
        if ip in arp:
            evidence.append("ARP")
        if services:
            evidence.append("TCP: " + service_names)

        # Prefer a real hostname; otherwise give a clearly marked inferred name.
        device_name = hostname or device_type

        records.append({
            "IP": ip,
            "Device Name": device_name,
            "MAC": mac,
            "Vendor": vendor,
            "Hostname": hostname,
            "Device Type": device_type,
            "Confidence": confidence,
            "Services": service_names,
            "Evidence": " + ".join(evidence),
            "Status": "نشط" if ip in alive else "مكتشف عبر الشبكة",
        })

    return records


def export_csv(data):
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["IP", "MAC", "Hostname", "Vendor", "Device Type", "Confidence", "Status"],
    )
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue().encode("utf-8-sig")


# ============================================================
# Sidebar
# ============================================================

st.sidebar.title("🌐 NetworkScope")
st.sidebar.caption("Local Network Discovery Tool")

page = st.sidebar.radio(
    "القائمة",
    [
        "لوحة التحكم",
        "فحص الشبكة",
        "بحث عن IP",
        "حول المشروع",
    ],
)

st.sidebar.divider()

st.sidebar.warning(
    "استخدم الأداة فقط على شبكة تملكها "
    "أو لديك تصريح صريح بفحصها."
)

# ============================================================
# Dashboard
# ============================================================

if page == "لوحة التحكم":

    st.markdown(
        '<div class="main-title">🌐 NetworkScope</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="subtitle">'
        "اكتشاف الأجهزة داخل الشبكة المحلية التي يشغَّل منها التطبيق"
        "</div>",
        unsafe_allow_html=True,
    )

    results = st.session_state.results

    total_devices = len(results)
    active_devices = sum(
        1 for d in results if d["Status"] == "نشط"
    )
    arp_devices = sum(
        1 for d in results if d["Status"] == "ظاهر في ARP"
    )
    mac_devices = sum(
        1 for d in results if d["MAC"]
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("الأجهزة المكتشفة", total_devices)
    col2.metric("أجهزة نشطة", active_devices)
    col3.metric("ظاهر في ARP", arp_devices)
    col4.metric("MAC متوفر", mac_devices)

    if st.session_state.last_network:
        st.info(
            f"آخر شبكة تم فحصها: {st.session_state.last_network}"
        )

    st.divider()

    if results:
        st.subheader("📋 الأجهزة المكتشفة ونوعها المحتمل")
        st.dataframe(
            results,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            label="⬇️ تحميل النتائج CSV",
            data=export_csv(results),
            file_name="network_devices.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info(
            "لا توجد نتائج حتى الآن. "
            "اذهب إلى «فحص الشبكة» وابدأ الفحص."
        )


# ============================================================
# Network Scanner
# ============================================================

elif page == "فحص الشبكة":

    st.title("🔎 فحص الشبكة")

    local_networks = get_local_networks()

    if local_networks:
        st.success("تم اكتشاف الشبكات المحلية على هذا الجهاز.")

        options = [
            f'{x["interface"]} — {x["ip"]} — {x["cidr"]}'
            for x in local_networks
        ]

        selected = st.selectbox(
            "اختر الشبكة المتصلة حاليًا",
            options,
        )

        selected_index = options.index(selected)
        detected_cidr = local_networks[selected_index]["cidr"]

        if st.button(
            "استخدام الشبكة المكتشفة",
            use_container_width=True,
        ):
            st.session_state.scan_target = detected_cidr

    st.write(
        "أدخل IP عاديًا مثل 192.168.1.20، "
        "أو أدخل الشبكة مباشرة مثل 192.168.1.0/24."
    )

    target_value = st.text_input(
        "IP أو Network CIDR",
        value=get_local_ip(),
        placeholder="192.168.1.20 أو 192.168.1.0/24",
    ).strip()

    try:
        network, explanation = resolve_scan_target(target_value)
        st.info(explanation)
        st.code(str(network), language="text")

        host_count = len(list(network.hosts()))

        col1, col2 = st.columns(2)
        col1.metric("الشبكة التي سيتم فحصها", str(network))
        col2.metric("عدد عناوين الأجهزة", host_count)

        workers = st.slider(
            "عدد عمليات الفحص المتوازية",
            min_value=4,
            max_value=64,
            value=32,
        )

        if st.button(
            "🚀 بدء فحص الشبكة",
            type="primary",
            use_container_width=True,
        ):
            try:
                with st.spinner(
                    f"يتم فحص {network} من هذا الجهاز..."
                ):
                    results = scan_network(
                        str(network),
                        workers,
                    )

                st.session_state.results = results
                st.session_state.last_network = str(network)

                st.success(
                    f"انتهى الفحص — تم العثور على "
                    f"{len(results)} جهاز/عنوان."
                )

                if not results:
                    st.warning(
                        "لم يتم اكتشاف أجهزة. إذا كنت متأكدًا أن هناك أجهزة متصلة، "
                        "فقد تكون الشبكة تستخدم Client/AP Isolation أو أن الجهاز الذي "
                        "يشغّل NetworkScope ليس على نفس الـLAN. جرّب أولًا اختيار "
                        "الشبكة المكتشفة من واجهة الجهاز، ثم أعد الفحص."
                    )

            except Exception as error:
                st.error(f"حدث خطأ: {error}")

    except Exception as error:
        st.error(str(error))

    if st.session_state.results:
        st.divider()
        st.subheader("📋 نتائج آخر فحص")
        st.dataframe(
            st.session_state.results,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# IP Search
# ============================================================

elif page == "بحث عن IP":

    st.title("📍 البحث عن جهاز داخل النتائج")

    ip_input = st.text_input(
        "أدخل IP",
        placeholder="192.168.1.10",
    ).strip()

    if ip_input:
        try:
            ipaddress.ip_address(ip_input)

            matches = [
                device
                for device in st.session_state.results
                if device["IP"] == ip_input
            ]

            if matches:
                device = matches[0]

                st.success("تم العثور على الجهاز.")

                col1, col2, col3 = st.columns(3)
                col1.metric("IP", device["IP"])
                col2.metric(
                    "MAC",
                    device["MAC"] or "غير متاح",
                )
                col3.metric("الحالة", device["Status"])

                st.write(
                    "Hostname:",
                    device["Hostname"] or "غير متاح",
                )
            else:
                st.info(
                    "هذا الـ IP غير موجود في نتائج آخر فحص."
                )

        except ValueError:
            st.error("عنوان IP غير صحيح.")


# ============================================================
# About
# ============================================================

elif page == "حول المشروع":

    st.title("ℹ️ حول NetworkScope")

    st.markdown(
        """
## ما هو NetworkScope؟

NetworkScope هو مشروع Streamlit لاكتشاف الأجهزة
داخل شبكة IPv4 محلية من الجهاز الذي يشغّل التطبيق.

### ماذا يفعل؟

- 🔎 يكتشف الأجهزة التي تستجيب لـ Ping.
- 📡 يقرأ جدول ARP المحلي.
- 💻 يعرض IP Address.
- 🆔 يعرض MAC Address عندما يكون متاحًا.
- 🖥️ يحاول معرفة Hostname.
- 🏷️ يحاول تحديد الشركة المصنعة من MAC/OUI.
- 🔎 يصنف نوع الجهاز بشكل محافظ بناءً على الاسم والشركة.
- 📊 يعرض النتائج في Dashboard.
- 🔍 يسمح بالبحث عن IP داخل نتائج الفحص.
- 📥 يصدّر النتائج إلى CSV.
- 🌐 يكتشف الشبكة المحلية تلقائيًا عند توفر معلومات الواجهة.

### نقطة مهمة جدًا

إذا كتبت IP فقط، فإن البرنامج لا يستطيع معرفة قناع الشبكة
من الرقم وحده. لذلك يحاول أولًا معرفة الشبكة من إعدادات
واجهة الشبكة في الجهاز.

مثال:

192.168.1.20 → قد تكون /24 أو /23 أو غير ذلك.

لذلك عند الحاجة للدقة، استخدم CIDR:

192.168.1.0/24

### حدود الأداة

الأداة لا:

- تتجاوز كلمات المرور.
- تسجل الدخول إلى الأجهزة.
- تخترق الأجهزة.
- تتجاوز صلاحيات الشبكة.
- تفحص الإنترنت العام.
- تضمن تحديد أن الجهاز كاميرا بمجرد اكتشاف IP.

### أين يتم الفحص؟

الفحص يتم من الجهاز الذي يشغّل Streamlit.

إذا شغّلت التطبيق على جهازك وهو متصل بشبكة الفندق
أو المنزل المصرح لك بفحصها، فالأداة تفحص الشبكة التي
يستطيع ذلك الجهاز الوصول إليها.

أما إذا رفعت Streamlit على Cloud، فإن السيرفر السحابي
هو الذي سيحاول الفحص، وليس جهاز الزائر.
"""
    )

    st.divider()
    st.caption("NetworkScope • Local Network Discovery • Device Fingerprinting")
