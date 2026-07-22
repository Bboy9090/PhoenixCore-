import hashlib
import sys
from pathlib import Path

# RFC 8032 parameters
p = 2**255 - 19
l = 2**252 + 27742317777372353535851937790883648493
d = -121665 * pow(121666, -1, p) % p
I = pow(2, (p - 1) // 4, p)

# Direct coordinates of standard Base Point G (B)
y_base = 4 * pow(5, -1, p) % p


def _xrecover(y):
    xx = (y * y - 1) * pow(d * y * y + 1, -1, p) % p
    x = pow(xx, (p + 3) // 8, p)
    if (x * x - xx) % p != 0:
        x = (x * I) % p
    if x % 2 != 0:
        x = p - x
    return x


x_base = _xrecover(y_base)
B = (x_base, y_base)


def point_compress(P):
    x_val, y_val = P
    return ((y_val & ((1 << 255) - 1)) | ((x_val & 1) << 255)).to_bytes(32, "little")


def point_add(P, Q):
    x1, y1 = P
    x2, y2 = Q
    num_x = (x1 * y2 + y1 * x2) % p
    den_x = (1 + d * x1 * x2 * y1 * y2) % p
    num_y = (y1 * y2 + x1 * x2) % p
    den_y = (1 - d * x1 * x2 * y1 * y2) % p
    x3 = num_x * pow(den_x, -1, p) % p
    y3 = num_y * pow(den_y, -1, p) % p
    return (x3, y3)


def point_mul(s, P):
    Q = (0, 1)
    base = P
    while s > 0:
        if s & 1:
            Q = point_add(Q, base)
        base = point_add(base, base)
        s >>= 1
    return Q


def ed25519_sign(secret_key, msg):
    h = hashlib.sha512(secret_key).digest()
    a = int.from_bytes(h[:32], "little")
    a &= (1 << 254) - 8
    a |= 1 << 254
    prefix = h[32:]

    A = point_mul(a, B)
    pubkey = point_compress(A)

    r = int.from_bytes(hashlib.sha512(prefix + msg).digest(), "little")
    R = point_mul(r % l, B)
    sig_R = point_compress(R)

    k = int.from_bytes(hashlib.sha512(sig_R + pubkey + msg).digest(), "little") % l
    s = (r + k * a) % l

    sig = sig_R + s.to_bytes(32, "little")
    return pubkey, sig


def main():
    manifest_path = Path("manifests/tool_registry.json")
    if not manifest_path.exists():
        manifest_path = (
            Path(__file__).parent.parent / "manifests" / "tool_registry.json"
        )

    if not manifest_path.exists():
        print("[-] tool_registry.json not found!")
        sys.exit(1)

    msg = manifest_path.read_bytes()

    # We use a deterministic test seed key:
    # "BootForgeSecureTrustAnchorSeedKe" (32 bytes)
    seed = b"BootForgeSecureTrustAnchorSeedKe"

    pubkey, sig = ed25519_sign(seed, msg)

    # Write the detached signature file in hex
    sig_path = manifest_path.parent / "tool_registry.sig"
    sig_path.write_text(sig.hex(), encoding="utf-8")

    print("[+] Cryptographic signing completed successfully!")
    print(f"[+] Public Key Trust Anchor Hex: {pubkey.hex()}")
    print(f"[+] Detached Signature Hex:      {sig.hex()}")
    print(f"[+] Signature file {sig_path} written.")


if __name__ == "__main__":
    main()
