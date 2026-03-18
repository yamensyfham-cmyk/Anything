import os, sys, subprocess, socket, time, threading, json

_SSH  = 'ssh'
_SCP  = 'scp'
_SFTP = 'sftp'

def _run(cmd, input_data=None, timeout=30):
    try:
        r = subprocess.run(
            cmd, input=input_data,
            capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except FileNotFoundError:
        return '', 'ssh not found. Run: pkg install openssh', 1
    except subprocess.TimeoutExpired:
        return '', 'timeout', 1
    except Exception as e:
        return '', str(e), 1

def _ssh_cmd(host, user, port, password, args, timeout=30):
    cmd = [_SSH,
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=10',
        '-o', 'BatchMode=no',
        '-p', str(port),
        f'{user}@{host}'
    ] + args
    if password:
        cmd = ['sshpass', '-p', password] + cmd
    return _run(cmd, timeout=timeout)

class AutoAddPolicy: pass
class RejectPolicy: pass

class SSHException(Exception): pass
class AuthenticationException(SSHException): pass
class NoValidConnectionsError(SSHException): pass

class Channel:
    def __init__(self, proc):
        self._proc = proc

    def recv(self, nbytes=65536):
        try:
            return self._proc.stdout.read(nbytes).encode('utf-8', 'replace')
        except Exception:
            return b''

    def sendall(self, data):
        try:
            self._proc.stdin.write(data.decode('utf-8', 'replace') if isinstance(data, bytes) else data)
            self._proc.stdin.flush()
        except Exception:
            pass

    def close(self): self._proc.terminate()

class Transport:
    def __init__(self, host, port, user, password, key_path):
        self.host     = host
        self.port     = port
        self.user     = user
        self.password = password
        self.key_path = key_path

    def open_session(self):
        cmd = [_SSH,
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'ConnectTimeout=10',
            '-p', str(self.port),
            f'{self.user}@{self.host}',
        ]
        if self.password:
            cmd = ['sshpass', '-p', self.password] + cmd
        if self.key_path:
            cmd += ['-i', self.key_path]
        cmd += ['-tt']
        try:
            proc = subprocess.Popen(
                cmd, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True
            )
            return Channel(proc)
        except Exception as e:
            raise SSHException(str(e))

    def open_channel(self, kind, dest_addr=None, src_addr=None):
        return self.open_session()

class SFTPClient:
    def __init__(self, host, port, user, password, key_path):
        self.host     = host
        self.port     = port
        self.user     = user
        self.password = password
        self.key_path = key_path

    def _scp_cmd(self, src, dst, upload=True):
        base = ['scp', '-o', 'StrictHostKeyChecking=no', '-P', str(self.port)]
        if self.password:
            base = ['sshpass', '-p', self.password] + base
        if self.key_path:
            base += ['-i', self.key_path]
        remote = f'{self.user}@{self.host}:{dst if upload else src}'
        if upload:
            return base + [src, remote]
        else:
            return base + [remote, dst]

    def put(self, local, remote):
        out, err, code = _run(self._scp_cmd(local, remote, upload=True), timeout=120)
        if code != 0: raise SSHException(err or 'put failed')

    def get(self, remote, local):
        out, err, code = _run(self._scp_cmd(remote, local, upload=False), timeout=120)
        if code != 0: raise SSHException(err or 'get failed')

    def listdir_attr(self, path='/'):
        out, err, code = _ssh_exec(self.host, self.port, self.user,
                                   self.password, self.key_path,
                                   f'ls -la {path}', 15)
        if code != 0: raise SSHException(err)
        results = []
        for line in out.split('\n')[1:]:
            parts = line.split()
            if len(parts) < 9: continue
            perm = parts[0]
            size = int(parts[4]) if parts[4].isdigit() else 0
            name = parts[8]
            class Attr:
                pass
            a = Attr()
            a.filename = name
            a.st_size  = size
            a.st_mode  = 0o40755 if perm.startswith('d') else 0o100644
            results.append(a)
        return results

    def remove(self, path):
        out, err, code = _ssh_exec(self.host, self.port, self.user,
                                   self.password, self.key_path,
                                   f'rm -f {path}', 15)
        if code != 0: raise SSHException(err)

    def mkdir(self, path):
        _ssh_exec(self.host, self.port, self.user, self.password,
                  self.key_path, f'mkdir -p {path}', 15)

    def open(self, path, mode='r'):
        if 'w' in mode or 'a' in mode:
            import tempfile
            return _RemoteWriteFile(self, path, mode)
        out, err, code = _ssh_exec(self.host, self.port, self.user,
                                   self.password, self.key_path,
                                   f'cat {path}', 30)
        import io
        return io.StringIO(out)

    def close(self): pass

class _RemoteWriteFile:
    def __init__(self, sftp, path, mode):
        self._sftp = sftp
        self._path = path
        import tempfile
        self._tmp = tempfile.NamedTemporaryFile(delete=False, mode='w' if 'b' not in mode else 'wb')

    def write(self, data): self._tmp.write(data)
    def __enter__(self): return self
    def __exit__(self, *a):
        self._tmp.close()
        self._sftp.put(self._tmp.name, self._path)
        os.unlink(self._tmp.name)
    def close(self):
        self._tmp.close()
        self._sftp.put(self._tmp.name, self._path)
        os.unlink(self._tmp.name)

def _ssh_exec(host, port, user, password, key_path, cmd, timeout=30):
    args = [_SSH,
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ConnectTimeout=10',
        '-p', str(port),
        f'{user}@{host}',
        cmd
    ]
    if password:
        args = ['sshpass', '-p', password] + args
    if key_path:
        idx = args.index(f'{user}@{host}')
        args = args[:idx-1] + ['-i', key_path] + args[idx-1:]
    return _run(args, timeout=timeout)

class SSHClient:
    def __init__(self):
        self._host     = ''
        self._port     = 22
        self._user     = ''
        self._password = ''
        self._key_path = ''
        self._connected= False
        self._policy   = None

    def set_missing_host_key_policy(self, policy): self._policy = policy

    def connect(self, hostname, port=22, username='root',
                password=None, key_filename=None, timeout=10):
        self._host     = hostname
        self._port     = port
        self._user     = username
        self._password = password or ''
        self._key_path = key_filename or ''
        out, err, code = _ssh_exec(
            hostname, port, username, self._password, self._key_path,
            'echo connected', timeout
        )
        if code != 0:
            raise AuthenticationException(err or 'Connection failed')
        self._connected = True

    def exec_command(self, command, timeout=30):
        out, err, code = _ssh_exec(
            self._host, self._port, self._user,
            self._password, self._key_path, command, timeout
        )
        import io
        class _FakeStream:
            def __init__(self, text):
                self._buf = io.BytesIO(text.encode('utf-8','replace'))
                self.channel = type('Ch',(),{'recv_exit_status':lambda s: code})()
            def read(self): return self._buf.read()
        stdin  = io.BytesIO(b'')
        stdout = _FakeStream(out)
        stderr = _FakeStream(err)
        return stdin, stdout, stderr

    def open_sftp(self):
        if not self._connected: raise SSHException('Not connected')
        return SFTPClient(self._host, self._port, self._user,
                          self._password, self._key_path)

    def get_transport(self):
        return Transport(self._host, self._port, self._user,
                         self._password, self._key_path)

    def close(self): self._connected = False

    def __enter__(self): return self
    def __exit__(self, *a): self.close()

if __name__ == '__main__':
    print("mini_ssh — بديل paramiko")
    print("يستخدم: ssh/scp من النظام (pkg install openssh)")
    print("✅ mini_ssh OK")
