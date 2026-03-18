import os, hashlib, hmac, struct, base64, secrets, time

_S = [
    99,124,119,123,242,107,111,197,48,1,103,43,254,215,171,118,
    202,130,201,125,250,89,71,240,173,212,162,175,156,164,114,192,
    183,253,147,38,54,63,247,204,52,165,229,241,113,216,49,21,
    4,199,35,195,24,150,5,154,7,18,128,226,235,39,178,117,
    9,131,44,26,27,110,90,160,82,59,214,179,41,227,47,132,
    83,209,0,237,32,252,177,91,106,203,190,57,74,76,88,207,
    208,239,170,251,67,77,51,133,69,249,2,127,80,60,159,168,
    81,163,64,143,146,157,56,245,188,182,218,33,16,255,243,210,
    205,12,19,236,95,151,68,23,196,167,126,61,100,93,25,115,
    96,129,79,220,34,42,144,136,70,238,184,20,222,94,11,219,
    224,50,58,10,73,6,36,92,194,211,172,98,145,149,228,121,
    231,200,55,109,141,213,78,169,108,86,244,234,101,122,174,8,
    186,120,37,46,28,166,180,198,232,221,116,31,75,189,139,138,
    112,62,181,102,72,3,246,14,97,53,87,185,134,193,29,158,
    225,248,152,17,105,217,142,148,155,30,135,233,206,85,40,223,
    140,161,137,13,191,230,66,104,65,153,45,15,176,84,187,22,
]
_S_INV = [0]*256
for i,v in enumerate(_S): _S_INV[v] = i

def _xtime(a): return ((a<<1)^0x1B) & 0xFF if a&0x80 else (a<<1)&0xFF

def _gmul(a,b):
    p = 0
    for _ in range(8):
        if b&1: p ^= a
        hi = a&0x80
        a = (a<<1)&0xFF
        if hi: a ^= 0x1B
        b >>= 1
    return p

def _sub_bytes(s):   return [[_S[s[i][j]] for j in range(4)] for i in range(4)]
def _isub_bytes(s):  return [[_S_INV[s[i][j]] for j in range(4)] for i in range(4)]

def _shift_rows(s):
    return [
        s[0],
        [s[1][1],s[1][2],s[1][3],s[1][0]],
        [s[2][2],s[2][3],s[2][0],s[2][1]],
        [s[3][3],s[3][0],s[3][1],s[3][2]],
    ]

def _ishift_rows(s):
    return [
        s[0],
        [s[1][3],s[1][0],s[1][1],s[1][2]],
        [s[2][2],s[2][3],s[2][0],s[2][1]],
        [s[3][1],s[3][2],s[3][3],s[3][0]],
    ]

def _mix_col(col):
    return [
        _gmul(0x02,col[0])^_gmul(0x03,col[1])^col[2]^col[3],
        col[0]^_gmul(0x02,col[1])^_gmul(0x03,col[2])^col[3],
        col[0]^col[1]^_gmul(0x02,col[2])^_gmul(0x03,col[3]),
        _gmul(0x03,col[0])^col[1]^col[2]^_gmul(0x02,col[3]),
    ]

def _imix_col(col):
    return [
        _gmul(0x0e,col[0])^_gmul(0x0b,col[1])^_gmul(0x0d,col[2])^_gmul(0x09,col[3]),
        _gmul(0x09,col[0])^_gmul(0x0e,col[1])^_gmul(0x0b,col[2])^_gmul(0x0d,col[3]),
        _gmul(0x0d,col[0])^_gmul(0x09,col[1])^_gmul(0x0e,col[2])^_gmul(0x0b,col[3]),
        _gmul(0x0b,col[0])^_gmul(0x0d,col[1])^_gmul(0x09,col[2])^_gmul(0x0e,col[3]),
    ]

def _mix_cols(s):
    cols = [[s[i][j] for i in range(4)] for j in range(4)]
    mixed= [_mix_col(c) for c in cols]
    return [[mixed[j][i] for j in range(4)] for i in range(4)]

def _imix_cols(s):
    cols = [[s[i][j] for i in range(4)] for j in range(4)]
    mixed= [_imix_col(c) for c in cols]
    return [[mixed[j][i] for j in range(4)] for i in range(4)]

def _bytes2state(b):
    return [[b[4*j+i] for j in range(4)] for i in range(4)]

def _state2bytes(s):
    return bytes(s[i][j] for j in range(4) for i in range(4))

def _add_rk(s, rk):
    return [[s[i][j]^rk[4*j+i] for j in range(4)] for i in range(4)]

def _key_expand(key):
    n = len(key)//4
    nr= n + 6
    w = list(key)
    RCON = [0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1B,0x36,0x6C,0xD8,0xAB,0x4D,0x9A,0x2F,0x5E,0xBC,0x63,0xC6,0x97,0x35,0x6A,0xD4]
    for i in range(n, 4*(nr+1)):
        t = list(w[(i-1)*4:i*4])
        if i%n == 0:
            rcon_idx = (i//n) - 1
            t = [_S[t[1]]^RCON[rcon_idx%len(RCON)], _S[t[2]], _S[t[3]], _S[t[0]]]
        elif n>6 and i%n==4:
            t = [_S[b] for b in t]
        w += [w[(i-n)*4+k]^t[k] for k in range(4)]
    return [bytes(w[i:i+16]) for i in range(0,len(w),16)]

def _aes_encrypt_block(key, block):
    rk = _key_expand(key)
    nr = len(rk)-1
    s  = _bytes2state(block)
    s  = _add_rk(s, rk[0])
    for r in range(1, nr):
        s = _sub_bytes(s)
        s = _shift_rows(s)
        s = _mix_cols(s)
        s = _add_rk(s, rk[r])
    s = _sub_bytes(s)
    s = _shift_rows(s)
    s = _add_rk(s, rk[nr])
    return _state2bytes(s)

def _aes_decrypt_block(key, block):
    rk = _key_expand(key)
    nr = len(rk)-1
    s  = _bytes2state(block)
    s  = _add_rk(s, rk[nr])
    for r in range(nr-1, 0, -1):
        s = _ishift_rows(s)
        s = _isub_bytes(s)
        s = _add_rk(s, rk[r])
        s = _imix_cols(s)
    s = _ishift_rows(s)
    s = _isub_bytes(s)
    s = _add_rk(s, rk[0])
    return _state2bytes(s)

def _pkcs7_pad(data, bs=16):
    n = bs - len(data)%bs
    return data + bytes([n]*n)

def _pkcs7_unpad(data):
    n = data[-1]
    if n==0 or n>16: raise ValueError("padding invalid")
    if data[-n:] != bytes([n]*n): raise ValueError("padding mismatch")
    return data[:-n]

def aes_encrypt_cbc(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    data   = _pkcs7_pad(plaintext)
    prev   = iv
    result = b''
    for i in range(0, len(data), 16):
        block = bytes(a^b for a,b in zip(data[i:i+16], prev))
        enc   = _aes_encrypt_block(key, block)
        result += enc
        prev   = enc
    return result

def aes_decrypt_cbc(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    result = b''
    prev   = iv
    for i in range(0, len(ciphertext), 16):
        block = ciphertext[i:i+16]
        dec   = _aes_decrypt_block(key, block)
        result += bytes(a^b for a,b in zip(dec, prev))
        prev   = block
    return _pkcs7_unpad(result)

def aes_encrypt_ecb(key: bytes, plaintext: bytes) -> bytes:
    data   = _pkcs7_pad(plaintext)
    return b''.join(_aes_encrypt_block(key, data[i:i+16]) for i in range(0,len(data),16))

def aes_decrypt_ecb(key: bytes, ciphertext: bytes) -> bytes:
    dec = b''.join(_aes_decrypt_block(key, ciphertext[i:i+16]) for i in range(0,len(ciphertext),16))
    return _pkcs7_unpad(dec)

def pbkdf2(password: bytes, salt: bytes, iterations=100000, dklen=32, prf='sha256') -> bytes:
    return hashlib.pbkdf2_hmac(prf, password, salt, iterations, dklen)

class Fernet:
    _VERSION = b'\x80'

    def __init__(self, key):
        if isinstance(key, str): key = key.encode()
        raw = base64.urlsafe_b64decode(key)
        if len(raw) != 32: raise ValueError("Fernet key must be 32 bytes")
        self._signing_key    = raw[:16]
        self._encryption_key = raw[16:]

    @staticmethod
    def generate_key() -> bytes:
        return base64.urlsafe_b64encode(os.urandom(32))

    def encrypt(self, data: bytes) -> bytes:
        if isinstance(data, str): data = data.encode()
        iv        = os.urandom(16)
        ts        = struct.pack('>Q', int(time.time()))
        ciphertext= aes_encrypt_cbc(self._encryption_key, iv, data)
        payload   = self._VERSION + ts + iv + ciphertext
        sig       = hmac.new(self._signing_key, payload, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(payload + sig)

    def decrypt(self, token: bytes, ttl=None) -> bytes:
        if isinstance(token, str): token = token.encode()
        try:
            raw = base64.urlsafe_b64decode(token)
        except Exception:
            raise ValueError("Invalid token")
        if len(raw) < 57: raise ValueError("Token too short")
        if raw[0:1] != self._VERSION: raise ValueError("Bad version")
        ts        = struct.unpack('>Q', raw[1:9])[0]
        payload   = raw[:-32]
        sig       = raw[-32:]
        expected  = hmac.new(self._signing_key, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected): raise ValueError("Signature mismatch")
        if ttl is not None and time.time() - ts > ttl: raise ValueError("Token expired")
        iv         = raw[9:25]
        ciphertext = raw[25:-32]
        return aes_decrypt_cbc(self._encryption_key, iv, ciphertext)

def _mod_exp(base, exp, mod):
    result = 1
    base %= mod
    while exp > 0:
        if exp & 1: result = result * base % mod
        exp >>= 1
        base = base * base % mod
    return result

def _is_prime(n, k=10):
    if n < 2: return False
    if n == 2 or n == 3: return True
    if n % 2 == 0: return False
    r, d = 0, n-1
    while d%2==0: r+=1; d//=2
    for _ in range(k):
        a = secrets.randbelow(n-3) + 2
        x = _mod_exp(a, d, n)
        if x==1 or x==n-1: continue
        for _ in range(r-1):
            x = x*x % n
            if x==n-1: break
        else: return False
    return True

def _gen_prime(bits):
    while True:
        n = int.from_bytes(os.urandom(bits//8), 'big') | (1<<(bits-1)) | 1
        if _is_prime(n): return n

def _gcd(a,b):
    while b: a,b = b,a%b
    return a

def _modinv(a, m):
    g, x, _ = _ext_gcd(a, m)
    if g != 1: raise ValueError("no inverse")
    return x % m

def _ext_gcd(a, b):
    if a==0: return b, 0, 1
    g,x,y = _ext_gcd(b%a, a)
    return g, y-(b//a)*x, x

class RSA:
    def __init__(self, bits=1024):
        self.bits = bits
        self.public_key  = None
        self.private_key = None

    def generate_keys(self):
        p = _gen_prime(self.bits//2)
        q = _gen_prime(self.bits//2)
        n = p*q
        phi = (p-1)*(q-1)
        e = 65537
        while _gcd(e, phi) != 1: e += 2
        d = _modinv(e, phi)
        self.public_key  = (e, n)
        self.private_key = (d, n)
        return self

    def encrypt(self, data: bytes) -> bytes:
        e, n = self.public_key
        num  = int.from_bytes(data, 'big')
        enc  = _mod_exp(num, e, n)
        return enc.to_bytes((n.bit_length()+7)//8, 'big')

    def decrypt(self, data: bytes) -> bytes:
        d, n = self.private_key
        num  = int.from_bytes(data, 'big')
        dec  = _mod_exp(num, d, n)
        return dec.to_bytes((n.bit_length()+7)//8, 'big').lstrip(b'\x00')

    def export_public(self) -> str:
        e, n = self.public_key
        return base64.urlsafe_b64encode(
            struct.pack('>QQ', e, n.bit_length()) +
            n.to_bytes((n.bit_length()+7)//8, 'big')
        ).decode()

    def export_private(self) -> str:
        d, n = self.private_key
        return base64.urlsafe_b64encode(
            struct.pack('>QQ', d, n.bit_length()) +
            n.to_bytes((n.bit_length()+7)//8, 'big')
        ).decode()

class PBKDF2HMAC:
    def __init__(self, algorithm=None, length=32, salt=b'', iterations=100000):
        self._length     = length
        self._salt       = salt
        self._iterations = iterations
        self._alg        = 'sha256'

    def derive(self, key_material: bytes) -> bytes:
        return pbkdf2(key_material, self._salt, self._iterations, self._length, self._alg)

    def verify(self, key_material: bytes, expected_key: bytes):
        derived = self.derive(key_material)
        if not hmac.compare_digest(derived, expected_key):
            raise ValueError("Keys don't match")

def encrypt_file(path: str, password: str) -> str:
    salt = os.urandom(16)
    key  = pbkdf2(password.encode(), salt)
    iv   = os.urandom(16)
    with open(path, 'rb') as f: data = f.read()
    enc  = aes_encrypt_cbc(key, iv, data)
    out  = path + '.enc'
    with open(out, 'wb') as f:
        f.write(b'MCRYPT1')
        f.write(salt)
        f.write(iv)
        f.write(enc)
    return out

def decrypt_file(path: str, password: str) -> str:
    with open(path, 'rb') as f: raw = f.read()
    if not raw.startswith(b'MCRYPT1'): raise ValueError("Not encrypted by mini_crypto")
    salt = raw[7:23]
    iv   = raw[23:39]
    enc  = raw[39:]
    key  = pbkdf2(password.encode(), salt)
    dec  = aes_decrypt_cbc(key, iv, enc)
    out  = path[:-4] if path.endswith('.enc') else path + '.dec'
    with open(out, 'wb') as f: f.write(dec)
    return out

if __name__ == '__main__':
    print("=== AES-256-CBC ===")
    key = os.urandom(32)
    iv  = os.urandom(16)
    msg = b'Hello AES World! This is a test message for encryption.'
    enc = aes_encrypt_cbc(key, iv, msg)
    dec = aes_decrypt_cbc(key, iv, enc)
    assert dec == msg
    print(f"AES: {msg[:20]}... => {enc.hex()[:20]}... => OK")

    print("\n=== Fernet ===")
    k   = Fernet.generate_key()
    f   = Fernet(k)
    tok = f.encrypt(b'Secret message')
    out = f.decrypt(tok)
    assert out == b'Secret message'
    print(f"Fernet: OK, key={k[:20]}...")

    print("\n=== RSA-512 ===")
    rsa = RSA(bits=512)
    rsa.generate_keys()
    msg = b'Hello RSA'
    enc = rsa.encrypt(msg)
    dec = rsa.decrypt(enc)
    assert dec == msg
    print(f"RSA: OK")

    print("\n=== PBKDF2 ===")
    k = pbkdf2(b'password', b'salt', 1000, 32)
    print(f"PBKDF2: {k.hex()[:20]}...")

    print("\n✅ mini_crypto OK")
