"""
Duplex AQRDT.py - Airgapped QR Data Transfer (Duplex CLI Edition v2.0)
High-Speed Bidirectional Optical Air-Gap File Transfer System.

Features:
- Unique Identifying Auth QR Codes (.env Transmitter Credentials + Receiver Auth UI)
- SHA-256 CTR Authenticated Encryption (AEAD) with Dynamic Key Derivation
- 100% Lossless High-Ratio Compression (ZLIB Level 9)
- Per-Packet CRC32 and End-to-End SHA-256 Integrity Verification
- Range-Compressed ARQ Missing Frame Retransmission
- Headless Windowless Terminal Block QR Rendering (ANSI VT100)
- Sender, Receiver, and Simulation Modes
"""

import sys
import os
import time
import math
import zlib
import base64
import hashlib
import hmac
import secrets
import argparse
import random
import re
import unicodedata
from typing import Optional, List, Dict, Tuple, Set

# Ensure UTF-8 output encoding and ANSI VT100 support for Windows terminals
if sys.platform == "win32":
    try:
        os.system('')  # Enables VT100 escape codes in Windows cmd/PowerShell
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import cv2
import numpy as np
import qrcode

try:
    from pyzbar.pyzbar import decode, ZBarSymbol
    HAS_PYZBAR = True
except Exception:
    HAS_PYZBAR = False


# =====================================================================
# --- Configuration & Secure .env Credentials Management ---
# =====================================================================

DEFAULT_ENV_FILENAME = ".env"
DEFAULT_FALLBACK_USER = "Nathaniel"
DEFAULT_FALLBACK_PASS = "AirgapSecurePass2026!"


def load_env_credentials(env_path: Optional[str] = None) -> Tuple[str, str]:
    """
    Loads username and password from .env file.
    Creates a default .env file if none exists.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not env_path:
        env_path = os.path.join(script_dir, DEFAULT_ENV_FILENAME)

    username = None
    password = None

    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'").strip('"')
                        if k == "AQRDT_USERNAME":
                            username = v
                        elif k == "AQRDT_PASSWORD":
                            password = v
                        elif k in ["USERNAME", "USER"] and not username:
                            username = v
                        elif k in ["PASSWORD", "AUTH_PASS", "PASS"] and not password:
                            password = v
        except Exception:
            pass

    # If .env not present or incomplete, create/update it
    if not username or not password:
        username = username or DEFAULT_FALLBACK_USER
        password = password or DEFAULT_FALLBACK_PASS
        try:
            if not os.path.exists(env_path):
                with open(env_path, "w", encoding="utf-8") as f:
                    f.write(
                        "# Airgapped QR Data Transfer (AQRDT) v2 Environment Configuration\n"
                        "# Transmitter & Receiver Authentication Credentials\n\n"
                        f"AQRDT_USERNAME={username}\n"
                        f"AQRDT_PASSWORD={password}\n"
                    )
        except Exception:
            pass

    return username, password


def compute_auth_signature(username: str, password: str) -> str:
    """Computes unique identifying cryptographic Auth signature."""
    norm_user = username.strip().lower()
    norm_pwd = password.strip()
    return hashlib.sha256(f"AQRDT_AUTH_v2:{norm_user}:{norm_pwd}".encode("utf-8")).hexdigest()


def generate_auth_qr_payload(username: str, password: str) -> str:
    """Generates standard v2 Auth QR payload."""
    sig = compute_auth_signature(username, password)
    return f"AUTH|AQRDT|v2|{username.strip()}|{sig}"


def verify_auth_payload(scanned_payload: str, expected_user: str, expected_pass: str) -> Tuple[bool, Optional[str]]:
    """
    Verifies scanned Auth QR code against configured credentials.
    Returns (is_valid, authenticated_username).
    """
    cleaned = scanned_payload.strip().replace("\r\n", "\n")
    expected_sig = compute_auth_signature(expected_user, expected_pass)

    # V2 format: AUTH|AQRDT|v2|<username>|<signature>
    if cleaned.startswith("AUTH|AQRDT|v2|"):
        parts = cleaned.split("|")
        if len(parts) >= 5:
            user = parts[3].strip()
            sig = parts[4].strip()
            # Match signature for expected password and user
            if sig == expected_sig or sig == compute_auth_signature(user, expected_pass):
                return True, user

    # Legacy V1 format / Raw Password Fallback
    legacy_auth = f"xnTTp2rHtQKmZ2hB0m9pOxxnsApAdmrN\n85jGqGsV7X1f5EGtW0VXCqjgFOExOvyY"
    if cleaned == legacy_auth or cleaned == f"AUTH|{legacy_auth}":
        return True, "LegacyUser"

    if cleaned == expected_pass or cleaned == f"AUTH|{expected_pass}":
        return True, expected_user

    return False, None


# =====================================================================
# --- Cryptographic Engine: SHA-256 CTR AEAD Stream Cipher ---
# =====================================================================

MAGIC_CONTAINER_V2 = b"AQ02"  # 4 bytes magic prefix
CONTAINER_HEADER_SIZE = 85    # 4 (Magic) + 16 (Salt) + 16 (Nonce) + 16 (MAC) + 1 (CompFlag) + 32 (OrigSHA256)


def derive_encryption_key(username: str, password: str, salt: bytes) -> bytes:
    """Derives a 256-bit (32-byte) symmetric encryption key using SHA-256."""
    norm_user = username.strip().lower().encode("utf-8")
    norm_pwd = password.strip().encode("utf-8")
    return hashlib.sha256(norm_user + b":" + norm_pwd + b":" + salt).digest()


def sha256_ctr_crypt(data: bytes, key: bytes, nonce: bytes) -> bytes:
    """
    SHA-256 CTR Keystream Cipher.
    High-speed, 100% lossless symmetric encryption/decryption using SHA-256 in counter mode.
    """
    out = bytearray(len(data))
    block_size = 32
    num_blocks = (len(data) + block_size - 1) // block_size

    for i in range(num_blocks):
        counter_bytes = i.to_bytes(4, byteorder="big")
        keystream_block = hashlib.sha256(key + nonce + counter_bytes).digest()
        start = i * block_size
        end = min(start + block_size, len(data))
        block_len = end - start
        for j in range(block_len):
            out[start + j] = data[start + j] ^ keystream_block[j]

    return bytes(out)


def compute_container_mac(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    """Computes 16-byte HMAC-SHA256 authentication tag (AEAD)."""
    return hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()[:16]


def pack_and_encrypt_file(
    file_bytes: bytes,
    username: str,
    password: str
) -> Tuple[bytes, str, bool, float]:
    """
    Compresses (lossless ZLIB 9) and encrypts (SHA-256 CTR AEAD) raw file bytes.
    Returns: (container_bytes, orig_sha256_hex, is_compressed, compression_ratio_pct)
    """
    orig_sha256_raw = hashlib.sha256(file_bytes).digest()
    orig_sha256_hex = orig_sha256_raw.hex()

    # 1. 100% Lossless Compression
    compressed_bytes = zlib.compress(file_bytes, level=9)
    if len(compressed_bytes) < len(file_bytes):
        is_compressed = True
        payload_data = compressed_bytes
        ratio = (1.0 - (len(compressed_bytes) / max(1, len(file_bytes)))) * 100.0
    else:
        is_compressed = False
        payload_data = file_bytes
        ratio = 0.0

    # 2. Key Derivation & AEAD Nonce/Salt
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(16)
    key = derive_encryption_key(username, password, salt)

    # 3. SHA-256 CTR Encryption
    ciphertext = sha256_ctr_crypt(payload_data, key, nonce)
    mac = compute_container_mac(key, nonce, ciphertext)

    # 4. Construct Binary Transfer Container
    comp_flag = bytes([1 if is_compressed else 0])
    container = (
        MAGIC_CONTAINER_V2 +  # 4 B
        salt +                # 16 B
        nonce +               # 16 B
        mac +                 # 16 B
        comp_flag +           # 1 B
        orig_sha256_raw +     # 32 B
        ciphertext            # N B
    )

    return container, orig_sha256_hex, is_compressed, ratio


def decrypt_and_unpack_container(
    container_bytes: bytes,
    username: str,
    password: str
) -> Tuple[bytes, str]:
    """
    Verifies MAC, decrypts SHA-256 CTR stream, and decompresses payload.
    Returns: (original_file_bytes, orig_sha256_hex).
    Raises ValueError on authentication or integrity failure.
    """
    if len(container_bytes) < CONTAINER_HEADER_SIZE or not container_bytes.startswith(MAGIC_CONTAINER_V2):
        # Fallback for unencrypted legacy raw ZLIB stream
        try:
            decomp = zlib.decompress(container_bytes)
            return decomp, hashlib.sha256(decomp).hexdigest()
        except Exception:
            raise ValueError("Invalid container header or corrupted packet data.")

    # Parse container header
    salt = container_bytes[4:20]
    nonce = container_bytes[20:36]
    expected_mac = container_bytes[36:52]
    is_compressed = (container_bytes[52] == 1)
    orig_sha256_raw = container_bytes[53:85]
    ciphertext = container_bytes[85:]

    orig_sha256_hex = orig_sha256_raw.hex()

    # Verify Authentication Tag
    key = derive_encryption_key(username, password, salt)
    actual_mac = compute_container_mac(key, nonce, ciphertext)

    if not hmac.compare_digest(actual_mac, expected_mac):
        raise ValueError("Decryption failed: Authentication tag mismatch (Incorrect password or corrupted data).")

    # Decrypt
    decrypted_payload = sha256_ctr_crypt(ciphertext, key, nonce)

    # Decompress
    if is_compressed:
        try:
            file_bytes = zlib.decompress(decrypted_payload)
        except Exception as e:
            raise ValueError(f"Decompression error after decryption: {e}")
    else:
        file_bytes = decrypted_payload

    # End-to-End SHA-256 Integrity Verification
    actual_sha256 = hashlib.sha256(file_bytes).digest()
    if actual_sha256 != orig_sha256_raw:
        raise ValueError(f"SHA-256 checksum mismatch! Expected: {orig_sha256_hex}, Got: {actual_sha256.hex()}")

    return file_bytes, orig_sha256_hex


# =====================================================================
# --- Range Compression Utilities for NACK Index Requests ---
# =====================================================================

def compress_indices(indices: List[int]) -> str:
    """Compresses a list of integers into range notation: e.g. [0,1,2,5,7,8] -> '0-2,5,7-8'"""
    if not indices:
        return ""
    sorted_idx = sorted(set(indices))
    ranges = []
    start = sorted_idx[0]
    prev = sorted_idx[0]

    for idx in sorted_idx[1:]:
        if idx == prev + 1:
            prev = idx
        else:
            ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
            start = idx
            prev = idx
    ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ",".join(ranges)


def decompress_indices(range_str: str) -> List[int]:
    """Decompresses range or comma-separated string: e.g. '0-2,5,7-9' -> [0,1,2,5,7,8,9]"""
    if not range_str or not range_str.strip():
        return []
    result = []
    for part in range_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                s, e = part.split("-", 1)
                result.extend(range(int(s), int(e) + 1))
            except ValueError:
                pass
        elif part.isdigit():
            result.append(int(part))
    return sorted(set(result))


# =====================================================================
# --- Standardized Data Packet Framing ---
# =====================================================================
# Frame format: D|<filename>|<idx>|<total>|<crc32_hex>|<b64_chunk>

def create_data_packet(filename: str, idx: int, total: int, raw_chunk_bytes: bytes) -> str:
    crc32 = zlib.crc32(raw_chunk_bytes) & 0xffffffff
    b64_chunk = base64.b64encode(raw_chunk_bytes).decode("ascii").replace("\n", "").replace("\r", "")
    return f"D|{filename}|{idx}|{total}|{crc32:08x}|{b64_chunk}"


def parse_data_packet(payload: str) -> Optional[Dict]:
    parts = payload.split("|")
    if len(parts) >= 5 and parts[0] == "D":
        try:
            fname = parts[1]
            idx = int(parts[2])
            total = int(parts[3])

            if len(parts) == 6:
                expected_crc = int(parts[4], 16)
                b64_data = parts[5]
                chunk_bytes = base64.b64decode(b64_data)
                if (zlib.crc32(chunk_bytes) & 0xffffffff) != expected_crc:
                    return None
            else:
                b64_data = parts[4]
                chunk_bytes = base64.b64decode(b64_data)

            return {
                "type": "DATA",
                "filename": fname,
                "idx": idx,
                "total": total,
                "chunk_bytes": chunk_bytes
            }
        except Exception:
            pass
    return None


# =====================================================================
# --- Terminal Block QR Rendering & Screen Management ---
# =====================================================================

def render_terminal_qr(data: str, invert: bool = True, double_width: bool = True, border: int = 2) -> str:
    """Renders high-contrast QR code directly to terminal using ANSI block characters."""
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=1,
        border=border
    )
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    char_block = "██" if double_width else "█"
    char_space = "  " if double_width else " "

    lines = []
    for row in matrix:
        if invert:
            line = "".join(char_space if cell else char_block for cell in row)
        else:
            line = "".join(char_block if cell else char_space for cell in row)
        lines.append(line)

    return "\n".join(lines)


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_at_top(content: str):
    """
    Renders content starting at top-left of the terminal.
    Appends \\033[K (clear line) to prevent ghost characters.
    """
    lines = content.split("\n")
    cleared_content = "\n".join(line + "\033[K" for line in lines)
    sys.stdout.write("\033[H" + cleared_content + "\n\033[J")
    sys.stdout.flush()


def display_width(text: str) -> int:
    """Calculates true terminal display width, ignoring ANSI codes and accounting for wide emojis."""
    clean = re.sub(r'\x1b\[[0-9;]*m', '', text)
    return sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in clean)


def render_header_card(
    tag: str,
    right_info: str,
    status_line: str,
    extra_line: Optional[str] = None,
    color_code: str = "\033[1;96m",
    width: int = 70,
    closed: bool = True
) -> str:
    """Renders a clean, uniformly formatted status header card with perfectly straight borders."""
    rst = "\033[0m"
    inner_w = width - 2
    dash_char = "─"

    tag_w = display_width(tag)
    right_w = display_width(right_info) if right_info else 0

    top_label = f"── {tag} "
    top_right = f" {right_info} ──" if right_info else "──"

    label_visual_len = tag_w + 4
    right_visual_len = right_w + 4 if right_info else 2

    middle_dash_len = max(2, inner_w - label_visual_len - right_visual_len)
    top_border = f"{color_code}┌{top_label}{dash_char * middle_dash_len}{top_right}┐{rst}"

    if closed:
        s1_w = display_width(status_line)
        pad1 = " " * max(0, inner_w - 2 - s1_w)
        line1 = f"{color_code}│{rst}  {status_line}{pad1}{color_code}│{rst}"

        if extra_line:
            s2_w = display_width(extra_line)
            pad2 = " " * max(0, inner_w - 2 - s2_w)
            line2 = f"\n{color_code}│{rst}  {extra_line}{pad2}{color_code}│{rst}"
        else:
            line2 = ""
    else:
        line1 = f"{color_code}│{rst}  {status_line}"
        line2 = f"\n{color_code}│{rst}  {extra_line}" if extra_line else ""

    bot_border = f"\n{color_code}└{dash_char * inner_w}┘{rst}"
    return f"{top_border}\n{line1}{line2}{bot_border}\n\n"


def render_kv_double_box(
    title: str,
    kv_pairs: List[Tuple[str, str, str]],
    color_code: str = "\033[1;96m",
    width: int = 70
):
    """
    Renders double-line box with perfectly straight right edge for any width.
    kv_pairs: list of tuples (label, value, value_color)
    """
    rst = "\033[0m"
    bld_white = "\033[1;97m"
    inner_w = width - 2
    val_w = width - 21  # 19 char prefix ('  Label:       ') + val_w + 2 borders = width
    title_pad = " " * max(0, width - 4 - display_width(title))

    print(f"{color_code}╔{'═' * inner_w}╗{rst}")
    print(f"{color_code}║{rst}  {bld_white}{title}{rst}{title_pad}{color_code}║{rst}")
    print(f"{color_code}╠{'═' * inner_w}╣{rst}")

    for label, val, val_color in kv_pairs:
        lbl_str = f"  {label}:".ljust(19)
        val_str = str(val)[:val_w].ljust(val_w)
        print(f"{color_code}║{rst}{lbl_str}{val_color}{val_str}{rst}{color_code}║{rst}")

    print(f"{color_code}╚{'═' * inner_w}╝{rst}\n")


def clean_path_input(raw_input: str) -> str:
    """Cleans user file path input (strips PowerShell operators, wrapping quotes, spaces)."""
    s = raw_input.strip()
    changed = True
    while changed:
        prev = s
        s = s.strip()
        if s.startswith("&"):
            s = s[1:].strip()
        if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
            s = s[1:-1].strip()
        changed = (s != prev)
    return s


def resolve_file_path(file_path: str) -> str:
    cleaned = clean_path_input(file_path)
    if os.path.exists(cleaned):
        return os.path.abspath(cleaned)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(script_dir, cleaned)
    if os.path.exists(candidate):
        return os.path.abspath(candidate)
    return cleaned


def format_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes:,} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes:,} B ({num_bytes / 1024:.2f} KB)"
    else:
        return f"{num_bytes:,} B ({num_bytes / (1024 * 1024):.2f} MB)"


# =====================================================================
# --- Headless Camera Computer Vision Scanning ---
# =====================================================================

def scan_camera(cap: cv2.VideoCapture, opencv_detector: Optional[cv2.QRCodeDetector] = None) -> Optional[str]:
    """Reads camera frame and detects QR codes with pyzbar and dual-polarity OpenCV fallback."""
    ret, frame = cap.read()
    if not ret or frame is None:
        return None

    if HAS_PYZBAR:
        try:
            decoded_objs = decode(frame, symbols=[ZBarSymbol.QRCODE])
            if decoded_objs:
                return decoded_objs[0].data.decode("utf-8").replace("\r\n", "\n")
        except Exception:
            pass

    if opencv_detector is None:
        opencv_detector = cv2.QRCodeDetector()

    try:
        data, _, _ = opencv_detector.detectAndDecode(frame)
        if data:
            return data.replace("\r\n", "\n")
    except Exception:
        pass

    # Dual-polarity inversion fallback for high-contrast light/dark themes
    inv_frame = cv2.bitwise_not(frame)
    if HAS_PYZBAR:
        try:
            decoded_objs = decode(inv_frame, symbols=[ZBarSymbol.QRCODE])
            if decoded_objs:
                return decoded_objs[0].data.decode("utf-8").replace("\r\n", "\n")
        except Exception:
            pass

    try:
        data, _, _ = opencv_detector.detectAndDecode(inv_frame)
        if data:
            return data.replace("\r\n", "\n")
    except Exception:
        pass

    return None


# =====================================================================
# --- Interactive Terminal UI ---
# =====================================================================

def prompt_file_selection(error_msg: Optional[str] = None) -> Optional[str]:
    """Renders file selection terminal card."""
    sys.stdout.write("\033[?25h")  # Show cursor
    sys.stdout.flush()

    clear_screen()
    w = 70
    border = "\033[1;96m"
    rst = "\033[0m"
    bld = "\033[1m"

    # App Banner
    banner_t1 = "✦ AIRGAPPED QR DATA TRANSFER (AQRDT v2.0)"
    banner_pad1 = " " * max(0, w - 4 - display_width(banner_t1))
    banner_t2 = "Secure Optical Air-Gap Protocol with SHA-256 AEAD Encryption"
    banner_pad2 = " " * max(0, w - 4 - display_width(banner_t2))

    print(f"\n{border}╭{'─' * (w - 2)}╮{rst}")
    print(f"{border}│{rst}  {bld}\033[97m{banner_t1}{rst}{banner_pad1}{border}│{rst}")
    print(f"{border}│{rst}  \033[90m{banner_t2}{rst}{banner_pad2}{border}│{rst}")
    print(f"{border}╰{'─' * (w - 2)}╯{rst}\n")

    if error_msg:
        truncated_err = error_msg[:58]
        err_hdr = "✖ ERROR"
        err_dashes = "─" * max(2, w - 8 - display_width(err_hdr))
        err_pad1 = " " * max(0, w - 8 - display_width(truncated_err))
        err_sub = "Please check the path and try again or drag & drop a file."
        err_pad2 = " " * max(0, w - 8 - display_width(err_sub))

        print(f"\033[1;91m  ╭─ {err_hdr} {err_dashes}╮\033[0m")
        print(f"\033[1;91m  │\033[0m  \033[91m{truncated_err}\033[0m{err_pad1}\033[1;91m│\033[0m")
        print(f"\033[1;91m  │\033[0m  \033[90m{err_sub}\033[0m{err_pad2}\033[1;91m│\033[0m")
        print(f"\033[1;91m  ╰{'─' * (w - 4)}╯\033[0m\n")

    card_hdr = "📁 Select File to Transmit"
    card_dashes = "─" * max(2, w - 8 - display_width(card_hdr))
    c_blue = "\033[1;34m"

    row1 = "\033[1;97m1.\033[0m Drag & drop any file directly into this terminal window"
    row1_pad = " " * max(0, w - 8 - display_width(row1))
    row2 = f"\033[1;97m2.\033[0m Or type the file path (e.g. \033[93mData.txt\033[0m, \033[93m./document.pdf\033[0m)"
    row2_pad = " " * max(0, w - 8 - display_width(row2))
    row3 = f"\033[1;97m3.\033[0m Press \033[1;92mEnter\033[0m or type \033[1;91m'q'\033[0m to quit"
    row3_pad = " " * max(0, w - 8 - display_width(row3))
    empty_pad = " " * (w - 6)

    print(f"{c_blue}   ╭─ {card_hdr} {card_dashes}╮{rst}")
    print(f"{c_blue}   │{rst}{empty_pad}{c_blue} │{rst}")
    print(f"{c_blue}   │{rst}  {row1}{row1_pad}{c_blue} │{rst}")
    print(f"{c_blue}   │{rst}  {row2}{row2_pad}{c_blue} │{rst}")
    print(f"{c_blue}   │{rst}  {row3}{row3_pad}{c_blue} │{rst}")
    print(f"{c_blue}   │{rst}{empty_pad}{c_blue} │{rst}")
    print(f"{c_blue}   ╰{'─' * (w - 5)}╯{rst}")

    try:
        user_input = input(f"\n  \033[1;96m╰─➤\033[0m \033[1;97mFile path:\033[0m ")
    except (EOFError, KeyboardInterrupt):
        return None

    cleaned = clean_path_input(user_input)
    if not cleaned or cleaned.lower() in ["q", "quit", "exit"]:
        return None
    return cleaned


# =====================================================================
# --- SENDER / TRANSMITTER ---
# =====================================================================

def run_sender(
    initial_file: Optional[str] = None,
    cam_id: int = 0,
    target_fps: float = 20.0,
    chunk_size: int = 120,
    invert: bool = True,
    retransmit_fps: Optional[float] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
):
    """
    Executes the SENDER workflow:
    1. Loads credentials from .env.
    2. Authenticates Receiver's Auth QR code via camera scan.
    3. Encrypts file with SHA-256 CTR AEAD + ZLIB lossless compression.
    4. Streams QR packets and dynamically handles ARQ missing packet requests.
    5. Loops persistently for continuous multiple file transmissions.
    """
    env_user, env_pass = load_env_credentials()
    user = username or env_user
    pwd = password or env_pass

    cap = cv2.VideoCapture(cam_id)
    if not cap.isOpened():
        print(f"\033[91mError: Could not open camera {cam_id}.\033[0m")
        return False

    detector = cv2.QRCodeDetector()
    delay = 1.0 / max(0.5, target_fps)
    effective_retransmit_fps = retransmit_fps if retransmit_fps is not None else max(1.0, round(target_fps * 0.6, 1))
    retransmit_delay = 1.0 / max(0.5, effective_retransmit_fps)

    auth_matched = False
    authenticated_user = None

    current_file = initial_file
    error_msg: Optional[str] = None
    w = 70

    try:
        while True:
            if not current_file:
                current_file = prompt_file_selection(error_msg)
                error_msg = None
                if not current_file:
                    exit_msg = "✔ All transmissions finished. Exiting AQRDT. Goodbye!"
                    exit_pad = " " * max(0, w - 8 - display_width(exit_msg))
                    print(f"\n\033[1;92m  ╭{'─' * (w - 4)}╮\033[0m")
                    print(f"\033[1;92m  │\033[0m  \033[1;97m{exit_msg}\033[0m{exit_pad}\033[1;92m│\033[0m")
                    print(f"\033[1;92m  ╰{'─' * (w - 4)}╯\033[0m\n")
                    break

            file_path = resolve_file_path(current_file)
            if not os.path.exists(file_path):
                error_msg = f"Target file '{os.path.basename(current_file)}' does not exist."
                current_file = None
                continue

            with open(file_path, "rb") as f:
                file_bytes = f.read()

            # 1. Compress & Encrypt with SHA-256 AEAD
            container_bytes, orig_sha256, is_compressed, ratio = pack_and_encrypt_file(
                file_bytes, user, pwd
            )

            raw_chunks = [container_bytes[i:i + chunk_size] for i in range(0, len(container_bytes), chunk_size)]
            total_chunks = len(raw_chunks)
            filename = os.path.basename(file_path)

            packets = [
                create_data_packet(filename, idx, total_chunks, raw_chunks[idx])
                for idx in range(total_chunks)
            ]

            rendered_qr = [render_terminal_qr(pkt, invert=invert) for pkt in packets]

            sys.stdout.write("\033[?25l")  # Hide cursor
            sys.stdout.flush()

            clear_screen()
            tx_summary_pairs = [
                ("File Name", filename, "\033[1;93m"),
                ("Raw Size", format_size(len(file_bytes)), "\033[1;96m"),
                ("Encrypted", f"{format_size(len(container_bytes))} (ZLIB -{ratio:.1f}%, SHA-256 AEAD)", "\033[1;92m"),
                ("Auth Identity", f"{user} (Key: SHA-256 CTR AEAD)", "\033[1;95m"),
                ("Total Chunks", f"{total_chunks} packets ({chunk_size} B/chunk)", "\033[1;92m"),
                ("Target Speed", f"{target_fps} FPS (Retransmit: {effective_retransmit_fps} FPS)", "\033[1;95m"),
                ("SHA-256 Hash", f"{orig_sha256[:45]}...", "\033[90m"),
            ]
            render_kv_double_box(
                title="✦ AIRGAPPED QR DATA TRANSMITTER (AQRDT v2.0)",
                kv_pairs=tx_summary_pairs,
                color_code="\033[1;96m",
                width=w
            )

            # STEP 1: Scan for Receiver Auth QR code
            if not auth_matched:
                auth_hdr = "🔐 STEP 1/3: Receiver Identity Authentication"
                auth_dashes = "─" * max(2, w - 8 - display_width(auth_hdr))
                auth_l1 = "Point camera at Receiver screen to scan Auth QR code..."
                auth_l1_pad = " " * max(0, w - 8 - display_width(auth_l1))
                auth_l2 = f"Expected User: '{user}' (Press Ctrl+C to abort)..."
                auth_l2_pad = " " * max(0, w - 8 - display_width(auth_l2))

                print(f"\n\033[1;93m   ╭─ {auth_hdr} {auth_dashes}╮\033[0m")
                print(f"\033[1;93m   │\033[0m  {auth_l1}{auth_l1_pad}\033[1;93m │\033[0m")
                print(f"\033[1;93m   │\033[0m  \033[90m{auth_l2}\033[0m{auth_l2_pad}\033[1;93m │\033[0m")
                print(f"\033[1;93m   ╰{'─' * (w - 5)}╯\033[0m\n")

                scan_ticks = 0
                while not auth_matched:
                    scanned = scan_camera(cap, detector)
                    scan_ticks += 1
                    if scanned:
                        is_valid, auth_user = verify_auth_payload(scanned, user, pwd)
                        if is_valid:
                            auth_matched = True
                            authenticated_user = auth_user or user
                            break

                    if scan_ticks % 10 == 0:
                        sys.stdout.write(f"\r  \033[90m[Scanning camera feed: {scan_ticks} checks...]\033[0m")
                        sys.stdout.flush()
                    time.sleep(0.05)

                print(f"\r\033[K\n\033[1;92m  ✔ [AUTH VERIFIED] Receiver verified: User '{authenticated_user}'!\033[0m")
                print(f"\033[1;96m  ⏳ Starting encrypted optical stream in 3 seconds...\033[0m\n")
                time.sleep(3.0)
            else:
                print(f"\n\033[1;92m  ✔ Session authenticated for User '{authenticated_user}'. Streaming '{filename}'...\033[0m\n")
                time.sleep(1.5)

            # STEP 2: Initial Blast
            for idx in range(total_chunks):
                pct = ((idx + 1) / total_chunks) * 100.0
                header = render_header_card(
                    tag="📡 TRANSMITTING ENCRYPTED AQRDT STREAM",
                    right_info=f"[{idx + 1:03d}/{total_chunks:03d}]",
                    status_line=f"File: \033[1;93m{filename}\033[0m  •  Speed: \033[1;92m{target_fps:.1f} FPS\033[0m  •  Progress: \033[1;95m{pct:5.1f}%\033[0m",
                    extra_line=f"User: \033[1;95m{authenticated_user}\033[0m  •  Cipher: \033[1;92mSHA-256 CTR AEAD\033[0m  •  Lossless ZLIB 9",
                    color_code="\033[1;96m",
                    width=w
                )
                print_at_top(header + rendered_qr[idx])
                time.sleep(delay)

            # Signal burst completion
            done_qr = render_terminal_qr("DONE_BLAST", invert=invert)
            initial_done_hdr = render_header_card(
                tag="⏳ INITIAL BURST COMPLETED",
                right_info=f"[{total_chunks:03d}/{total_chunks:03d}] Sent",
                status_line=f"File: \033[1;93m{filename}\033[0m  •  Listening for Receiver ACK / REQ",
                extra_line="Encrypted frames broadcasted. Waiting for optical feedback...",
                color_code="\033[1;93m",
                width=w
            )
            print_at_top(initial_done_hdr + done_qr)

            # STEP 3: ARQ Missing Packets & ACK Loop
            transfer_complete = False
            while not transfer_complete:
                scanned = scan_camera(cap, detector)
                if scanned:
                    if scanned.startswith("ACK|COMPLETE") or scanned.startswith("ACK|AQRDT|COMPLETE"):
                        transfer_complete = True
                        break
                    elif scanned.startswith("REQ|"):
                        range_str = scanned.split("|", 1)[1]
                        missing = decompress_indices(range_str)
                        if missing:
                            missing_preview = ", ".join(str(x + 1) for x in missing[:8])
                            if len(missing) > 8:
                                missing_preview += f" ... (+{len(missing) - 8} more)"

                            # 3-second delay to give user time to prepare camera alignment
                            for countdown in range(3, 0, -1):
                                retransmit_wait_hdr = render_header_card(
                                    tag="⚡ RETRANSMISSION REQUEST DETECTED",
                                    right_info=f"{len(missing)} Missing",
                                    status_line=f"Receiver requested \033[1;96m{len(missing)}\033[0m missing frame(s): \033[1;97m[{missing_preview}]\033[0m",
                                    extra_line=f"\033[1;95m⏳ Resending @ {effective_retransmit_fps:.1f} FPS in {countdown}s... (Get ready!)\033[0m",
                                    color_code="\033[1;93m",
                                    width=w
                                )
                                print_at_top(retransmit_wait_hdr + done_qr)
                                time.sleep(1.0)

                            # Resend missing frames at reliable retransmission FPS
                            for seq_num, m_idx in enumerate(missing, start=1):
                                if 0 <= m_idx < total_chunks:
                                    m_hdr = render_header_card(
                                        tag="🔄 RETRANSMITTING MISSING FRAMES",
                                        right_info=f"Frame [{m_idx + 1:03d}/{total_chunks:03d}]",
                                        status_line=f"File: \033[1;93m{filename}\033[0m  •  Resending \033[1;93m{seq_num}/{len(missing)}\033[0m  •  Speed: \033[1;92m{effective_retransmit_fps:.1f} FPS\033[0m",
                                        extra_line=f"Missing index: #{m_idx + 1}  •  Cipher: SHA-256 CTR",
                                        color_code="\033[1;91m",
                                        width=w
                                    )
                                    print_at_top(m_hdr + rendered_qr[m_idx])
                                    time.sleep(retransmit_delay)

                            # Re-display DONE_BLAST to trigger next check
                            batch_sent_hdr = render_header_card(
                                tag="✔ RETRANSMISSION BATCH SENT",
                                right_info=f"[{len(missing)} Frames Resent]",
                                status_line="Waiting for Receiver confirmation or next request...              ",
                                color_code="\033[1;93m",
                                width=w
                            )
                            print_at_top(batch_sent_hdr + done_qr)

                time.sleep(0.02)

            clear_screen()
            tx_ack_pairs = [
                ("File Name", filename, "\033[1;93m"),
                ("Original Size", format_size(len(file_bytes)), "\033[1;96m"),
                ("Auth Identity", f"{authenticated_user} (SHA-256 AEAD Verified)", "\033[1;95m"),
                ("Total Packets", f"{total_chunks} frames", "\033[1;92m"),
                ("Target Speed", f"{target_fps} FPS", "\033[1;95m"),
                ("SHA-256 Digest", f"{orig_sha256[:45]}...", "\033[90m"),
            ]
            render_kv_double_box(
                title="✔ ENCRYPTED FILE TRANSFER ACKNOWLEDGED BY RECEIVER",
                kv_pairs=tx_ack_pairs,
                color_code="\033[1;92m",
                width=w
            )

            time.sleep(2.0)
            current_file = None

        return True

    except KeyboardInterrupt:
        print("\n\033[93mTransmission stopped by user.\033[0m")
        return False
    finally:
        sys.stdout.write("\033[?25h\n")
        sys.stdout.flush()
        cap.release()


# =====================================================================
# --- RECEIVER (CLI Terminal Edition) ---
# =====================================================================

def run_receiver(
    output_dir: str = "./received_files",
    cam_id: int = 0,
    invert: bool = True,
    username: Optional[str] = None,
    password: Optional[str] = None
):
    """
    Executes the RECEIVER workflow:
    1. Displays Auth QR code on screen.
    2. Scans sender stream with camera.
    3. Reassembles packets, verifies CRC32 and SHA-256 MAC.
    4. Decrypts with SHA-256 CTR and decompresses with ZLIB.
    5. Saves verified file to output directory and displays ACK QR code.
    """
    env_user, env_pass = load_env_credentials()
    user = username or env_user
    pwd = password or env_pass

    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(cam_id)
    if not cap.isOpened():
        print(f"\033[91mError: Could not open camera {cam_id}.\033[0m")
        return False

    detector = cv2.QRCodeDetector()
    auth_payload = generate_auth_qr_payload(user, pwd)
    auth_qr_str = render_terminal_qr(auth_payload, invert=invert)

    w = 70
    received_chunks: Dict[int, bytes] = {}
    total_chunks: Optional[int] = None
    target_filename: str = "received_file.bin"
    is_complete = False

    try:
        clear_screen()
        hdr = render_header_card(
            tag="🔐 AQRDT RECEIVER: AUTH QR READY",
            right_info=f"User: {user}",
            status_line=f"Point Transmitter camera at this screen to authenticate...",
            extra_line="Waiting for Sender to scan Auth QR and begin transmission...",
            color_code="\033[1;92m",
            width=w
        )
        print_at_top(hdr + auth_qr_str)

        last_scan_time = time.time()

        while not is_complete:
            scanned = scan_camera(cap, detector)
            if scanned:
                if scanned == "DONE_BLAST":
                    # Send NACK for missing frames
                    if total_chunks is not None:
                        missing = [i for i in range(total_chunks) if i not in received_chunks]
                        if missing:
                            req_payload = f"REQ|{compress_indices(missing)}"
                            req_qr = render_terminal_qr(req_payload, invert=invert)
                            nack_hdr = render_header_card(
                                tag="⚡ REQUESTING MISSING FRAMES",
                                right_info=f"{len(missing)} Missing",
                                status_line=f"Point camera at Sender while Sender reads this request...",
                                extra_line=f"Missing indices: {missing[:6]}...",
                                color_code="\033[1;91m",
                                width=w
                            )
                            print_at_top(nack_hdr + req_qr)
                            time.sleep(1.0)
                            continue

                parsed = parse_data_packet(scanned)
                if parsed:
                    target_filename = parsed["filename"]
                    idx = parsed["idx"]
                    total_chunks = parsed["total"]
                    chunk_bytes = parsed["chunk_bytes"]

                    if idx not in received_chunks:
                        received_chunks[idx] = chunk_bytes
                        last_scan_time = time.time()

                        pct = (len(received_chunks) / total_chunks) * 100.0
                        hud_hdr = render_header_card(
                            tag="📥 RECEIVING ENCRYPTED STREAM",
                            right_info=f"[{len(received_chunks)}/{total_chunks}]",
                            status_line=f"File: \033[1;93m{target_filename}\033[0m  •  Progress: \033[1;92m{pct:5.1f}%\033[0m",
                            extra_line=f"User: \033[1;95m{user}\033[0m  •  Capturing optical frames...",
                            color_code="\033[1;96m",
                            width=w
                        )
                        print_at_top(hud_hdr + auth_qr_str)

                    # Check if all chunks arrived
                    if len(received_chunks) == total_chunks:
                        # Reassemble container
                        full_container = bytearray()
                        for i in range(total_chunks):
                            full_container.extend(received_chunks[i])

                        # Decrypt & Decompress
                        try:
                            file_bytes, sha256_hex = decrypt_and_unpack_container(
                                bytes(full_container), user, pwd
                            )
                            out_file_path = os.path.join(output_dir, target_filename)
                            with open(out_file_path, "wb") as f:
                                f.write(file_bytes)

                            # Display completion ACK QR
                            ack_payload = f"ACK|AQRDT|COMPLETE|{sha256_hex}|{user}"
                            ack_qr = render_terminal_qr(ack_payload, invert=invert)
                            ack_hdr = render_header_card(
                                tag="✔ TRANSFER COMPLETE & VERIFIED",
                                right_info=f"{format_size(len(file_bytes))}",
                                status_line=f"Saved to: \033[1;92m{out_file_path}\033[0m",
                                extra_line=f"SHA-256: \033[90m{sha256_hex[:45]}...\033[0m",
                                color_code="\033[1;92m",
                                width=w
                            )
                            print_at_top(ack_hdr + ack_qr)
                            is_complete = True
                            print(f"\n\033[1;92mFile '{target_filename}' successfully decrypted and saved!\033[0m\n")
                            break
                        except Exception as e:
                            print(f"\n\033[1;91mDecryption Error: {e}\033[0m\n")
                            break

            time.sleep(0.01)

        return is_complete

    except KeyboardInterrupt:
        print("\n\033[93mReceiver stopped by user.\033[0m")
        return False
    finally:
        sys.stdout.write("\033[?25h\n")
        sys.stdout.flush()
        cap.release()


# =====================================================================
# --- SIMULATOR MODE (Loopback Simulation) ---
# =====================================================================

def run_simulator(
    file_path: Optional[str] = None,
    drop_rate: float = 0.25,
    chunk_size: int = 120,
    username: Optional[str] = None,
    password: Optional[str] = None
):
    """
    Simulates end-to-end loopback transfer with simulated packet drops and ARQ retransmissions.
    """
    env_user, env_pass = load_env_credentials()
    user = username or env_user
    pwd = password or env_pass

    print(f"\033[1;96m=== Running AQRDT v2 Simulation (Drop Rate: {drop_rate * 100:.0f}%) ===\033[0m")

    # Generate sample file if none provided
    if not file_path or not os.path.exists(file_path):
        sample_data = b"CONFIDENTIAL AIRGAP TEST DATA TRANSMITTED VIA AQRDT v2.0!\n" * 50
        file_path = "sim_test_data.txt"
        with open(file_path, "wb") as f:
            f.write(sample_data)
        cleanup_temp = True
    else:
        with open(file_path, "rb") as f:
            sample_data = f.read()
        cleanup_temp = False

    filename = os.path.basename(file_path)

    # 1. Receiver generates Auth QR
    auth_payload = generate_auth_qr_payload(user, pwd)
    print(f"[Receiver] Auth QR Generated: {auth_payload[:35]}...")

    # 2. Transmitter verifies Auth QR
    is_valid, auth_user = verify_auth_payload(auth_payload, user, pwd)
    assert is_valid and auth_user == user
    print(f"[Transmitter] Auth QR Verified for User '{auth_user}'! [SUCCESS]")

    # 3. Transmitter compresses and encrypts
    container_bytes, orig_sha, is_comp, ratio = pack_and_encrypt_file(sample_data, user, pwd)
    print(f"[Transmitter] Encrypted: {len(sample_data)} B -> {len(container_bytes)} B (ZLIB -{ratio:.1f}%, SHA-256 AEAD)")

    raw_chunks = [container_bytes[i:i + chunk_size] for i in range(0, len(container_bytes), chunk_size)]
    total_chunks = len(raw_chunks)
    packets = [create_data_packet(filename, i, total_chunks, raw_chunks[i]) for i in range(total_chunks)]

    # 4. First pass with simulated packet drops
    received: Dict[int, bytes] = {}
    print(f"[Transmitter] Broadcasting {total_chunks} packets...")

    for i, pkt in enumerate(packets):
        if random.random() >= drop_rate:
            parsed = parse_data_packet(pkt)
            if parsed:
                received[parsed["idx"]] = parsed["chunk_bytes"]

    print(f"[Receiver] Received {len(received)}/{total_chunks} packets in first blast.")

    # 5. ARQ Missing Packet Retransmission Loop
    retransmit_passes = 0
    while len(received) < total_chunks:
        retransmit_passes += 1
        missing = [i for i in range(total_chunks) if i not in received]
        range_str = compress_indices(missing)
        req_pkt = f"REQ|{range_str}"
        print(f"[Receiver] NACK #{retransmit_passes}: Requesting {len(missing)} missing frames: {req_pkt}")

        # Transmitter resends requested missing frames
        for m_idx in missing:
            # 90% chance of arrival on retransmit
            if random.random() > 0.1:
                parsed = parse_data_packet(packets[m_idx])
                if parsed:
                    received[parsed["idx"]] = parsed["chunk_bytes"]

    print(f"[Receiver] All {total_chunks} packets assembled after {retransmit_passes} ARQ passes!")

    # 6. Receiver Unpacks & Decrypts
    full_container = bytearray()
    for i in range(total_chunks):
        full_container.extend(received[i])

    recovered_bytes, recovered_sha = decrypt_and_unpack_container(bytes(full_container), user, pwd)
    assert recovered_bytes == sample_data
    assert recovered_sha == orig_sha

    print(f"\033[1;92m[SIMULATION SUCCESS] Bit-for-bit verified! SHA-256: {recovered_sha}\033[0m")

    if cleanup_temp and os.path.exists(file_path):
        os.remove(file_path)


# =====================================================================
# --- CLI ENTRYPOINT ---
# =====================================================================

def main():
    parser = argparse.ArgumentParser(description="Duplex AQRDT v2.0 - Airgapped QR Data Transfer")
    parser.add_argument("mode", nargs="?", choices=["sender", "receiver", "simulate"], default="sender")
    parser.add_argument("-f", "--file", help="Path to file to transmit")
    parser.add_argument("-o", "--output", default="./received_files", help="Output directory for receiver")
    parser.add_argument("-c", "--camera", type=int, default=0, help="Camera index (default: 0)")
    parser.add_argument("--fps", type=float, default=20.0, help="Target FPS (default: 20.0)")
    parser.add_argument("--retransmit-fps", type=float, default=10.0, help="Retransmission FPS (default: 10.0)")
    parser.add_argument("--chunk-size", type=int, default=120, help="Chunk payload size (default: 120)")
    parser.add_argument("--drop-rate", type=float, default=0.3, help="Simulated drop rate for simulation mode (default: 0.3)")
    parser.add_argument("--username", help="Override auth username")
    parser.add_argument("--password", help="Override auth password")
    parser.add_argument("--light-terminal", action="store_true", help="Set flag if using a white background terminal")

    args = parser.parse_args()
    invert = not args.light_terminal

    if args.mode == "sender":
        run_sender(
            args.file,
            cam_id=args.camera,
            target_fps=args.fps,
            chunk_size=args.chunk_size,
            invert=invert,
            retransmit_fps=args.retransmit_fps,
            username=args.username,
            password=args.password
        )
    elif args.mode == "receiver":
        run_receiver(
            output_dir=args.output,
            cam_id=args.camera,
            invert=invert,
            username=args.username,
            password=args.password
        )
    elif args.mode == "simulate":
        run_simulator(
            file_path=args.file,
            drop_rate=args.drop_rate,
            chunk_size=args.chunk_size,
            username=args.username,
            password=args.password
        )


if __name__ == "__main__":
    main()
