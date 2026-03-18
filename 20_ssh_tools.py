"""
أدوات SSH/SFTP المتقدمة — 20 ميزة
pip install paramiko
"""
import os, sys, json, time, threading
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
import rtl_fix

try:
    import mini_ssh as paramiko
    _SSH = True
except ImportError:
    _SSH = False

class SSHTools:
    def __init__(self):
        self._client  = None
        self._sftp    = None
        self._host    = ""
        self._sessions = {}

    def connect(self, host, port=22, user="root", password=None, key_path=None) -> str:
        if not _SSH: return "❌ pip install paramiko"
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if key_path:
                self._client.connect(host, port=port, username=user,
                                     key_filename=os.path.expanduser(key_path), timeout=10)
            else:
                self._client.connect(host, port=port, username=user,
                                     password=password, timeout=10)
            self._host = host
            return f"✅ متصل بـ {user}@{host}:{port}"
        except Exception as e:
            return f"❌ {e}"

    def disconnect(self) -> str:
        if self._sftp:  self._sftp.close();  self._sftp  = None
        if self._client: self._client.close(); self._client = None
        return "✅ قُطع الاتصال."

    def _sftp_session(self):
        if not self._sftp:
            self._sftp = self._client.open_sftp()
        return self._sftp

    def run(self, cmd: str, timeout=30) -> dict:
        if not self._client: return {"error": "غير متصل."}
        try:
            stdin, stdout, stderr = self._client.exec_command(cmd, timeout=timeout)
            out = stdout.read().decode('utf-8', errors='replace').strip()
            err = stderr.read().decode('utf-8', errors='replace').strip()
            code = stdout.channel.recv_exit_status()
            return {"stdout": out, "stderr": err, "exit_code": code}
        except Exception as e:
            return {"error": str(e)}

    def run_many(self, commands: list) -> list:
        """تنفيذ قائمة أوامر بالتسلسل"""
        return [{"cmd": c, **self.run(c)} for c in commands]

    def run_sudo(self, cmd: str, password: str) -> dict:
        """تنفيذ أمر بصلاحية sudo"""
        if not self._client: return {"error": "غير متصل."}
        try:
            transport = self._client.get_transport()
            channel   = transport.open_session()
            channel.get_pty()
            channel.exec_command(f"sudo -S {cmd}")
            channel.sendall(password.encode() + b'\n')
            time.sleep(1)
            out = channel.recv(65536).decode('utf-8', errors='replace')
            channel.close()
            return {"stdout": out}
        except Exception as e:
            return {"error": str(e)}

    def interactive_shell(self):
        """شل تفاعلية"""
        if not self._client: print("❌ غير متصل."); return
        print(f"🖥 شل تفاعلية على {self._host} — اكتب 'exit' للخروج")
        while True:
            try:
                cmd = input(f"[{self._host}]$ ").strip()
                if cmd.lower() in ("exit","quit"): break
                if not cmd: continue
                r = self.run(cmd)
                if r.get("stdout"): print(r["stdout"])
                if r.get("stderr"): print(f"⚠ {r['stderr']}")
            except KeyboardInterrupt:
                break

    def upload(self, local: str, remote: str) -> str:
        if not self._client: return "❌ غير متصل."
        try:
            sftp = self._sftp_session()
            sftp.put(local, remote)
            return f"✅ رُفع: {local} → {remote}"
        except Exception as e: return f"❌ {e}"

    def download(self, remote: str, local: str) -> str:
        if not self._client: return "❌ غير متصل."
        try:
            sftp = self._sftp_session()
            sftp.get(remote, local)
            return f"✅ نُزِّل: {remote} → {local}"
        except Exception as e: return f"❌ {e}"

    def upload_folder(self, local_folder: str, remote_folder: str) -> str:
        if not self._client: return "❌ غير متصل."
        count = 0
        sftp  = self._sftp_session()
        for root, dirs, files in os.walk(local_folder):
            for fname in files:
                local_path  = os.path.join(root, fname)
                remote_path = remote_folder + "/" + os.path.relpath(local_path, local_folder).replace("\\","/")
                try:
                    sftp.put(local_path, remote_path)
                    count += 1
                except Exception:
                    try:
                        sftp.mkdir(os.path.dirname(remote_path))
                        sftp.put(local_path, remote_path)
                        count += 1
                    except Exception:
                        pass
        return f"✅ رُفع {count} ملف"

    def list_dir(self, remote_path="/") -> list:
        if not self._client: return []
        try:
            sftp  = self._sftp_session()
            items = sftp.listdir_attr(remote_path)
            return [{"name":i.filename,"size":i.st_size,"type":"d" if i.st_mode&0o40000 else "f"} for i in items]
        except Exception as e: return [{"error":str(e)}]

    def delete_remote(self, remote_path: str) -> str:
        if not self._client: return "❌ غير متصل."
        try:
            self._sftp_session().remove(remote_path)
            return f"✅ حُذف: {remote_path}"
        except Exception as e: return f"❌ {e}"

    def mkdir_remote(self, path: str) -> str:
        try:
            self._sftp_session().mkdir(path)
            return f"✅ تم إنشاء: {path}"
        except Exception as e: return f"❌ {e}"

    def read_remote_file(self, remote_path: str, max_kb=100) -> str:
        if not self._client: return "❌ غير متصل."
        try:
            with self._sftp_session().open(remote_path,'r') as f:
                return f.read(max_kb*1024).decode('utf-8', errors='replace')
        except Exception as e: return f"❌ {e}"

    def write_remote_file(self, remote_path: str, content: str) -> str:
        if not self._client: return "❌ غير متصل."
        try:
            with self._sftp_session().open(remote_path,'w') as f:
                f.write(content)
            return f"✅ كُتب: {remote_path}"
        except Exception as e: return f"❌ {e}"

    def server_info(self) -> dict:
        cmds = {
            "OS":      "uname -a",
            "CPU":     "nproc",
            "RAM":     "free -h | grep Mem",
            "Disk":    "df -h /",
            "Uptime":  "uptime -p",
            "Users":   "who",
            "IP":      "hostname -I",
            "Python":  "python3 --version 2>&1 || python --version 2>&1",
        }
        result = {}
        for key, cmd in cmds.items():
            r = self.run(cmd)
            result[key] = r.get("stdout","N/A")[:80]
        return result

    def top_processes(self, count=10) -> str:
        r = self.run(f"ps aux --sort=-%cpu | head -{count+1}")
        return r.get("stdout","")

    def tail_log(self, log_path="/var/log/syslog", lines=50) -> str:
        r = self.run(f"tail -{lines} {log_path}")
        return r.get("stdout","❌ لا يمكن قراءة السجل.")

    def port_check(self) -> str:
        r = self.run("ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null")
        return r.get("stdout","")

    def install_pkg(self, pkg: str, mgr="apt") -> str:
        cmds = {
            "apt":    f"apt-get install -y {pkg}",
            "yum":    f"yum install -y {pkg}",
            "pacman": f"pacman -S --noconfirm {pkg}",
            "apk":    f"apk add {pkg}",
        }
        r = self.run(cmds.get(mgr, cmds["apt"]))
        return r.get("stdout","") or r.get("stderr","")

    def backup_remote_dir(self, remote_dir: str, local_out: str) -> str:
        """ضغط مجلد على السيرفر وتنزيله"""
        if not self._client: return "❌ غير متصل."
        tmp = f"/tmp/uas_backup_{int(time.time())}.tar.gz"
        self.run(f"tar -czf {tmp} {remote_dir}")
        r = self.download(tmp, local_out)
        self.run(f"rm -f {tmp}")
        return r

    def tunnel(self, local_port: int, remote_host: str, remote_port: int):
        """SSH Tunnel — إعادة توجيه منفذ"""
        if not self._client: return "❌ غير متصل."
        import socketserver

        class Handler(socketserver.BaseRequestHandler):
            def handle(self):
                try:
                    chan = self.server.ssh_client.get_transport().open_channel(
                        "direct-tcpip", (remote_host, remote_port),
                        self.request.getpeername())
                    while True:
                        r = select.select([self.request, chan],[],[])
                        if self.request in r[0]:
                            data = self.request.recv(1024)
                            if not data: break
                            chan.send(data)
                        if chan in r[0]:
                            data = chan.recv(1024)
                            if not data: break
                            self.request.send(data)
                except Exception:
                    pass

        server = socketserver.ThreadingTCPServer(("127.0.0.1", local_port), Handler)
        server.ssh_client = self._client
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        return f"✅ Tunnel: localhost:{local_port} → {remote_host}:{remote_port}"

if __name__ == "__main__":
    ssh = SSHTools()
    menu = {
        "1":  ("اتصال بـ SSH",           lambda: print(ssh.connect(input("Host => "), int(input("Port (22) => ") or 22), input("User => "), input("Password => ")))),
        "2":  ("قطع الاتصال",            lambda: print(ssh.disconnect())),
        "3":  ("تنفيذ أمر",              lambda: print(json.dumps(ssh.run(input("الأمر => ")), indent=2, ensure_ascii=False))),
        "4":  ("شل تفاعلية",            lambda: ssh.interactive_shell()),
        "5":  ("معلومات السيرفر",        lambda: print(json.dumps(ssh.server_info(), indent=2, ensure_ascii=False))),
        "6":  ("رفع ملف",               lambda: print(ssh.upload(input("المحلي => "), input("البعيد => ")))),
        "7":  ("تنزيل ملف",             lambda: print(ssh.download(input("البعيد => "), input("المحلي => ")))),
        "8":  ("قراءة ملف بعيد",        lambda: print(ssh.read_remote_file(input("المسار => ")))),
        "9":  ("عرض مجلد بعيد",         lambda: print(json.dumps(ssh.list_dir(input("المسار (/) => ") or "/"), indent=2))),
        "10": ("أكثر العمليات CPU",     lambda: print(ssh.top_processes())),
        "11": ("عرض المنافذ المفتوحة",  lambda: print(ssh.port_check())),
        "12": ("قراءة سجل",             lambda: print(ssh.tail_log(input("مسار السجل => ") or "/var/log/syslog"))),
        "13": ("تثبيت حزمة",            lambda: print(ssh.install_pkg(input("اسم الحزمة => "), input("المدير (apt/yum/apk) => ") or "apt"))),
        "14": ("نسخ احتياطي مجلد بعيد", lambda: print(ssh.backup_remote_dir(input("المجلد البعيد => "), input("الحفظ محلياً => ")))),
        "15": ("SSH Tunnel",            lambda: print(ssh.tunnel(int(input("المنفذ المحلي => ")), input("Host البعيد => "), int(input("المنفذ البعيد => "))))),
    }
    while True:
        print("\n═"*45)
        print("  🔌  SSH Tools — 15 ميزة")
        print("═"*45)
        for k,(l,_) in menu.items(): print(f"  {k:>2}. {l}")
        print("   0. رجوع")
        ch = input("\nاختر => ").strip()
        if ch == "0": break
        if ch in menu:
            try: menu[ch][1]()
            except Exception as e: print(f"❌ {e}")
