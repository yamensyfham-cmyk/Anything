"""
مراقب الشبكة المتقدم
بدون أي مكاتب خارجية — stdlib فقط (/proc/net)
"""
import os
import re
import socket
import struct
import time
import subprocess
import json

def _hex_to_ip(hex_str: str) -> str:
    try:
        ip = struct.pack("<I", int(hex_str, 16))
        return socket.inet_ntoa(ip)
    except Exception:
        return hex_str

def _hex_to_port(hex_str: str) -> int:
    try:
        return int(hex_str, 16)
    except Exception:
        return 0

TCP_STATES = {
    "01": "ESTABLISHED", "02": "SYN_SENT", "03": "SYN_RECV",
    "04": "FIN_WAIT1",   "05": "FIN_WAIT2","06": "TIME_WAIT",
    "07": "CLOSE",       "08": "CLOSE_WAIT","09": "LAST_ACK",
    "0A": "LISTEN",      "0B": "CLOSING",
}

def _parse_proc_net(proto="tcp") -> list:
    path = f"/proc/net/{proto}"
    conns = []
    if not os.path.exists(path):
        return conns
    try:
        with open(path, 'r') as f:
            lines = f.readlines()[1:]
        for line in lines:
            parts = line.split()
            if len(parts) < 10: continue
            local_ip,  local_port  = parts[1].split(":")
            remote_ip, remote_port = parts[2].split(":")
            state_hex = parts[3].upper()
            conns.append({
                "proto":        proto.upper(),
                "local":        f"{_hex_to_ip(local_ip)}:{_hex_to_port(local_port)}",
                "remote":       f"{_hex_to_ip(remote_ip)}:{_hex_to_port(remote_port)}",
                "state":        TCP_STATES.get(state_hex, state_hex),
                "inode":        parts[9],
            })
    except Exception:
        pass
    return conns

class NetworkMonitor:

    @staticmethod
    def active_connections(proto="both"):
        """الاتصالات النشطة"""
        conns = []
        if proto in ("tcp", "both"):
            conns += _parse_proc_net("tcp")
        if proto in ("udp", "both"):
            conns += _parse_proc_net("udp")

        return conns

    @staticmethod
    def listening_ports():
        """المنافذ المفتوحة على الجهاز"""
        all_conn = NetworkMonitor.active_connections()
        return [c for c in all_conn if c["state"] == "LISTEN"]

    @staticmethod
    def established_connections():
        return [c for c in NetworkMonitor.active_connections() if c["state"] == "ESTABLISHED"]

    @staticmethod
    def data_usage(interface="wlan0"):
        """استهلاك البيانات للواجهة المحددة"""
        rx_path = f"/sys/class/net/{interface}/statistics/rx_bytes"
        tx_path = f"/sys/class/net/{interface}/statistics/tx_bytes"
        try:
            rx = int(open(rx_path).read().strip())
            tx = int(open(tx_path).read().strip())
            def fmt(b):
                for u in ['B','KB','MB','GB']:
                    if b < 1024: return f"{b:.1f} {u}"
                    b /= 1024
                return f"{b:.1f} TB"
            return {"interface": interface, "downloaded": fmt(rx), "uploaded": fmt(tx)}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def all_interfaces():
        """قائمة كل الواجهات مع IP وبيانات"""
        ifaces = {}
        try:
            for iface in os.listdir("/sys/class/net"):
                info = {"ip": "N/A", "mac": "N/A", "rx": "N/A", "tx": "N/A"}
                try:
                    mac_path = f"/sys/class/net/{iface}/address"
                    info["mac"] = open(mac_path).read().strip()
                except Exception:
                    pass
                try:
                    rx = int(open(f"/sys/class/net/{iface}/statistics/rx_bytes").read())
                    tx = int(open(f"/sys/class/net/{iface}/statistics/tx_bytes").read())
                    def fmt(b):
                        for u in ['B','KB','MB','GB']:
                            if b < 1024: return f"{b:.1f} {u}"
                            b /= 1024
                        return f"{b:.1f} TB"
                    info["rx"] = fmt(rx)
                    info["tx"] = fmt(tx)
                except Exception:
                    pass
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    import fcntl
                    result = fcntl.ioctl(s.fileno(), 0x8915,
                                         struct.pack('256s', iface[:15].encode()))
                    info["ip"] = socket.inet_ntoa(result[20:24])
                except Exception:
                    pass
                ifaces[iface] = info
        except Exception:
            pass
        return ifaces

    @staticmethod
    def live_bandwidth(interface="wlan0", interval=2, rounds=5):
        """قياس السرعة الفعلية للشبكة لحظياً"""
        rx_path = f"/sys/class/net/{interface}/statistics/rx_bytes"
        tx_path = f"/sys/class/net/{interface}/statistics/tx_bytes"
        results = []
        try:
            for _ in range(rounds):
                rx1 = int(open(rx_path).read())
                tx1 = int(open(tx_path).read())
                time.sleep(interval)
                rx2 = int(open(rx_path).read())
                tx2 = int(open(tx_path).read())
                dl = (rx2 - rx1) / interval / 1024
                ul = (tx2 - tx1) / interval / 1024
                line = f"⬇ {dl:7.1f} KB/s  ⬆ {ul:7.1f} KB/s"
                print(line)
                results.append({"dl_kbs": round(dl, 1), "ul_kbs": round(ul, 1)})
        except FileNotFoundError:
            print(f"واجهة {interface} غير موجودة.")
        except KeyboardInterrupt:
            pass
        return results

    @staticmethod
    def port_scan(host: str, ports=None, timeout=0.4) -> list:
        """فحص المنافذ"""
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443,
                     3306, 5432, 6379, 8080, 8443, 27017]
        open_ports = []
        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(timeout)
                if s.connect_ex((host, port)) == 0:
                    try:
                        service = socket.getservbyport(port)
                    except Exception:
                        service = "unknown"
                    open_ports.append({"port": port, "service": service})
                s.close()
            except Exception:
                pass
        return open_ports

    @staticmethod
    def resolve_domains(domains: list) -> dict:
        result = {}
        for d in domains:
            try:
                result[d] = socket.gethostbyname(d)
            except Exception as e:
                result[d] = f"فشل: {e}"
        return result

    @staticmethod
    def public_ip():
        """IP العام عبر DNS بدون HTTP"""
        try:

            import struct
            host = "myip.opendns.com"
            dns_server = ("resolver1.opendns.com", 53)

            query = b"\xaa\xbb\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
            for part in host.split("."):
                query += bytes([len(part)]) + part.encode()
            query += b"\x00\x00\x01\x00\x01"
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(5)
            s.sendto(query, dns_server)
            data, _ = s.recvfrom(512)
            s.close()

            ip_bytes = data[-4:]
            return socket.inet_ntoa(ip_bytes)
        except Exception:
            try:

                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return f"{ip} (local)"
            except Exception as e:
                return f"فشل: {e}"

if __name__ == "__main__":
    menu = {
        "1": ("الاتصالات النشطة",    lambda: [print(f"  {c['proto']:<5} {c['local']:<22} → {c['remote']:<22} [{c['state']}]") for c in NetworkMonitor.established_connections()]),
        "2": ("المنافذ المفتوحة",    lambda: [print(f"  {c['proto']:<5} {c['local']}") for c in NetworkMonitor.listening_ports()]),
        "3": ("استهلاك البيانات",    lambda: print(json.dumps(NetworkMonitor.data_usage(input("الواجهة (wlan0) => ").strip() or "wlan0"), indent=2))),
        "4": ("جميع الواجهات",       lambda: print(json.dumps(NetworkMonitor.all_interfaces(), indent=2, ensure_ascii=False))),
        "5": ("قياس السرعة",         lambda: NetworkMonitor.live_bandwidth(input("الواجهة (wlan0) => ").strip() or "wlan0", rounds=int(input("عدد القراءات (5) => ").strip() or 5))),
        "6": ("فحص منافذ",          lambda: [print(f"  ✅ {r['port']}/{r['service']}") for r in NetworkMonitor.port_scan(input("الهدف => ").strip())]),
        "7": ("IP العام",            lambda: print(NetworkMonitor.public_ip())),
        "8": ("حل DNS",              lambda: print(json.dumps(NetworkMonitor.resolve_domains(input("النطاقات (مفصولة بمسافة) => ").split()), indent=2))),
    }
    while True:
        print("\n" + "═"*45)
        print("  🌐  Network Monitor")
        print("═"*45)
        for k, (label, _) in menu.items():
            print(f"  {k}. {label}")
        print("  0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except KeyboardInterrupt: pass
            except Exception as e: print(f"خطأ: {e}")
