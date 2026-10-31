#!/usr/bin/env python3
"""
preview_terminal_outputs.py - AQRDT Terminal UI Catalog & Alignment Preview

Renders all terminal screens, cards, headers, prompts, and dialog boxes
at once so you can audit, edit, and ensure consistent widths, borders, and margins.
"""

import sys
import os
import re
import unicodedata
from typing import Optional, List, Tuple

# Enable UTF-8 encoding in Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Set global box width for consistency audit (default is 70)
W = 80

# ANSI color codes
RST = "\033[0m"
BLD = "\033[1m"
DIM = "\033[90m"

C_CYAN    = "\033[1;96m"
C_GREEN   = "\033[1;92m"
C_YELLOW  = "\033[1;93m"
C_BLUE    = "\033[1;34m"
C_MAGENTA = "\033[1;95m"
C_RED     = "\033[1;91m"
C_WHITE   = "\033[1;97m"


def display_width(text: str) -> int:
    """Calculates true terminal display width, ignoring ANSI codes and accounting for wide emojis."""
    clean = re.sub(r'\x1b\[[0-9;]*m', '', text)
    return sum(2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in clean)


def section_divider(title: str, num: int, total: int):
    """Visual section separator for the preview catalog."""
    tag = f" SCREEN {num:02d}/{total:02d}: {title} "
    pad_len = max(2, (W - display_width(tag)) // 2)
    line = "═" * pad_len + tag + "═" * max(0, W - pad_len - display_width(tag))
    print(f"\n\033[38;5;244m{line}{RST}\n")


def render_header_card(
    tag: str,
    right_info: str,
    status_line: str,
    extra_line: str = None,
    color_code: str = C_CYAN,
    width: int = W,
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
    return f"{top_border}\n{line1}{line2}{bot_border}"


def render_kv_double_box(
    title: str,
    kv_pairs: List[Tuple[str, str, str]],
    color_code: str = C_CYAN,
    width: int = W
):
    """
    Renders double-line box with perfectly straight right edge for any width.
    kv_pairs: list of tuples (label, value, value_color)
    """
    inner_w = width - 2
    val_w = width - 21  # 19 char prefix ('  Label:       ') + val_w + 2 borders = width
    title_pad = " " * max(0, width - 4 - display_width(title))

    print(f"{color_code}╔{'═' * inner_w}╗{RST}")
    print(f"{color_code}║{RST}  {C_WHITE}{title}{RST}{title_pad}{color_code}║{RST}")
    print(f"{color_code}╠{'═' * inner_w}╣{RST}")

    for label, val, val_color in kv_pairs:
        lbl_str = f"  {label}:".ljust(19)
        val_str = str(val)[:val_w].ljust(val_w)
        print(f"{color_code}║{RST}{lbl_str}{val_color}{val_str}{RST}{color_code}║{RST}")

    print(f"{color_code}╚{'═' * inner_w}╝{RST}")


def render_rounded_box(
    title: Optional[str],
    body_lines: List[str],
    color_code: str = C_BLUE,
    width: int = W,
    indent: int = 2
):
    """
    Renders rounded single-line box (╭─╮) with straight right edge and consistent padding.
    """
    ind = " " * indent
    box_w = width - indent
    dash_w = box_w - 2

    if title:
        title_w = display_width(title)
        dash_len = max(2, dash_w - title_w - 3)
        dashes = "─" * dash_len
        print(f"{ind}{color_code}╭─ {title} {dashes}╮{RST}")
    else:
        print(f"{ind}{color_code}╭{'─' * dash_w}╮{RST}")

    for line in body_lines:
        if line == "":
            print(f"{ind}{color_code}│{RST}{' ' * dash_w}{color_code}│{RST}")
        else:
            lw = display_width(line)
            pad = " " * max(0, dash_w - 2 - lw)
            print(f"{ind}{color_code}│{RST}  {line}{pad}{color_code}│{RST}")

    print(f"{ind}{color_code}╰{'─' * dash_w}╯{RST}")


def main():
    TOTAL_SCREENS = 14
    screen_idx = 1

    print(f"\n{BLD}{C_WHITE}================================================================================{RST}")
    print(f"{BLD}{C_CYAN}    AQRDT v2.0 TERMINAL OUTPUT & ALIGNMENT PREVIEW (Width = {W})    {RST}")
    print(f"{BLD}{C_WHITE}================================================================================{RST}")

    # -------------------------------------------------------------
    # 1. Main App Banner
    # -------------------------------------------------------------
    section_divider("App Banner / Intro Header", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    render_rounded_box(
        title=None,
        body_lines=[
            f"{BLD}{C_WHITE}✦ AIRGAPPED QR DATA TRANSFER (AQRDT v2.0){RST}",
            f"{DIM}Secure Optical Air-Gap Protocol with SHA-256 AEAD Encryption{RST}"
        ],
        color_code=C_CYAN,
        width=W,
        indent=0
    )

    # -------------------------------------------------------------
    # 2. File Selection & Drag-and-Drop Prompt
    # -------------------------------------------------------------
    section_divider("File Selection Menu", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    render_rounded_box(
        title="📁 Select File to Transmit",
        body_lines=[
            "",
            f"{C_WHITE}1.{RST} Drag & drop any file directly into this terminal window",
            f"{C_WHITE}2.{RST} Or type the file path (e.g. {C_YELLOW}Data.txt{RST}, {C_YELLOW}./document.pdf{RST})",
            f"{C_WHITE}3.{RST} Press {C_GREEN}Enter{RST} or type {C_RED}'q'{RST} to quit",
            ""
        ],
        color_code=C_BLUE,
        width=W,
        indent=2
    )
    print(f"\n  {C_CYAN}╰─➤{RST} {C_WHITE}File path:{RST} document_secret.pdf")

    # -------------------------------------------------------------
    # 3. File Error Box
    # -------------------------------------------------------------
    section_divider("Error Message Card", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    render_rounded_box(
        title="✖ ERROR",
        body_lines=[
            "\033[91mTarget file 'missing_data.zip' does not exist.\033[0m",
            f"{DIM}Please check the path and try again or drag & drop a file.{RST}"
        ],
        color_code=C_RED,
        width=W,
        indent=2
    )

    # -------------------------------------------------------------
    # 4. Transmitter Ready & Encryption Summary Box
    # -------------------------------------------------------------
    section_divider("Transmitter: File Encryption & Transfer Card", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    tx_summary_pairs = [
        ("File Name", "document_secret.pdf", C_YELLOW),
        ("Raw Size", "148,684 B (145.20 KB)", C_CYAN),
        ("Encrypted", "115,080 B (ZLIB -22.6%, SHA-256 AEAD)", C_GREEN),
        ("Auth Identity", "Nathaniel (Key: SHA-256 CTR AEAD)", C_MAGENTA),
        ("Total Chunks", "959 packets (120 B/chunk)", C_GREEN),
        ("Target Speed", "20.0 FPS (Retransmit: 12.0 FPS)", C_MAGENTA),
        ("SHA-256 Hash", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b...", DIM),
    ]
    render_kv_double_box(
        title="✦ AIRGAPPED QR DATA TRANSMITTER (AQRDT v2.0)",
        kv_pairs=tx_summary_pairs,
        color_code=C_CYAN,
        width=W
    )

    # -------------------------------------------------------------
    # 5. Step 1: Scan Receiver Auth QR Card
    # -------------------------------------------------------------
    section_divider("Transmitter: Step 1 Scan Auth QR Card", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    render_rounded_box(
        title="🔐 STEP 1/3: Receiver Identity Authentication",
        body_lines=[
            "Point camera at Receiver screen to scan Auth QR code...",
            f"{DIM}Expected User: 'Nathaniel' (Press Ctrl+C to abort)...{RST}"
        ],
        color_code=C_YELLOW,
        width=W,
        indent=2
    )
    print(f"\n  {C_GREEN}✔ [AUTH VERIFIED] Receiver verified: User 'Nathaniel'!{RST}")
    print(f"  {C_CYAN}⏳ Starting encrypted optical stream in 3 seconds...{RST}")

    # -------------------------------------------------------------
    # 6. Stream Transmission Header
    # -------------------------------------------------------------
    section_divider("Transmitter: Streaming Packets Active Card", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    hdr_transmitting = render_header_card(
        tag="📡 TRANSMITTING ENCRYPTED AQRDT STREAM",
        right_info="[042/959]",
        status_line=f"File: {C_YELLOW}document_secret.pdf{RST}  •  Speed: {C_GREEN}20.0 FPS{RST}  •  Progress: {C_MAGENTA}  4.4%{RST}",
        extra_line=f"User: {C_MAGENTA}Nathaniel{RST}  •  Cipher: {C_GREEN}SHA-256 CTR AEAD{RST}  •  Lossless ZLIB 9",
        color_code=C_CYAN,
        width=W
    )
    print(hdr_transmitting)

    # -------------------------------------------------------------
    # 7. Initial Burst Completed Header
    # -------------------------------------------------------------
    section_divider("Transmitter: Initial Blast Completed Card", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    hdr_burst = render_header_card(
        tag="⏳ INITIAL BURST COMPLETED",
        right_info="[959/959] Sent",
        status_line=f"File: {C_YELLOW}document_secret.pdf{RST}  •  Listening for Receiver ACK / REQ",
        extra_line="Encrypted frames broadcasted. Waiting for optical feedback...",
        color_code=C_YELLOW,
        width=W
    )
    print(hdr_burst)

    # -------------------------------------------------------------
    # 8. Retransmission Request Detected (Sender side)
    # -------------------------------------------------------------
    section_divider("Transmitter: Retransmit Request Detected Card", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    hdr_req_detected = render_header_card(
        tag="⚡ RETRANSMISSION REQUEST DETECTED",
        right_info="5 Missing",
        status_line=f"Receiver requested {C_CYAN}5{RST} missing frame(s): {C_WHITE}[14, 89, 210, 450, 712]{RST}",
        extra_line=f"{C_MAGENTA}⏳ Resending @ 12.0 FPS in 3s... (Get ready!){RST}",
        color_code=C_YELLOW,
        width=W
    )
    print(hdr_req_detected)

    # -------------------------------------------------------------
    # 9. Retransmitting Missing Frames (Sender side)
    # -------------------------------------------------------------
    section_divider("Transmitter: Resending Missing Frames Card", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    hdr_resending = render_header_card(
        tag="🔄 RETRANSMITTING MISSING FRAMES",
        right_info="Frame [014/959]",
        status_line=f"File: {C_YELLOW}document_secret.pdf{RST}  •  Resending {C_YELLOW}1/5{RST}  •  Speed: {C_GREEN}12.0 FPS{RST}",
        extra_line="Missing index: #14  •  Cipher: SHA-256 CTR",
        color_code=C_RED,
        width=W
    )
    print(hdr_resending)

    # -------------------------------------------------------------
    # 10. Transmitter Completion & Acknowledged Box
    # -------------------------------------------------------------
    section_divider("Transmitter: Transfer Complete & Acknowledged Card", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    tx_ack_pairs = [
        ("File Name", "document_secret.pdf", C_YELLOW),
        ("Original Size", "148,684 B (145.20 KB)", C_CYAN),
        ("Auth Identity", "Nathaniel (SHA-256 AEAD Verified)", C_MAGENTA),
        ("Total Packets", "959 frames", C_GREEN),
        ("Target Speed", "20.0 FPS", C_MAGENTA),
        ("SHA-256 Digest", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b...", DIM),
    ]
    render_kv_double_box(
        title="✔ ENCRYPTED FILE TRANSFER ACKNOWLEDGED BY RECEIVER",
        kv_pairs=tx_ack_pairs,
        color_code=C_GREEN,
        width=W
    )

    # -------------------------------------------------------------
    # 11. Receiver: Auth QR Ready Card
    # -------------------------------------------------------------
    section_divider("Receiver: Awaiting Transmitter Auth Scan Card", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    hdr_rx_auth = render_header_card(
        tag="🔐 AQRDT RECEIVER: AUTH QR READY",
        right_info="User: Nathaniel",
        status_line="Point Transmitter camera at this screen to authenticate...",
        extra_line="Waiting for Sender to scan Auth QR and begin transmission...",
        color_code=C_GREEN,
        width=W
    )
    print(hdr_rx_auth)

    # -------------------------------------------------------------
    # 12. Receiver: Actively Receiving Stream Card
    # -------------------------------------------------------------
    section_divider("Receiver: Receiving Optical Stream Active Card", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    hdr_rx_stream = render_header_card(
        tag="📥 RECEIVING ENCRYPTED STREAM",
        right_info="[420/959]",
        status_line=f"File: {C_YELLOW}document_secret.pdf{RST}  •  Progress: {C_GREEN} 43.8%{RST}",
        extra_line=f"User: {C_MAGENTA}Nathaniel{RST}  •  Capturing optical frames...",
        color_code=C_CYAN,
        width=W
    )
    print(hdr_rx_stream)

    # -------------------------------------------------------------
    # 13. Receiver: Requesting Missing Frames NACK Card
    # -------------------------------------------------------------
    section_divider("Receiver: NACK Missing Frames Request Card", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    hdr_rx_nack = render_header_card(
        tag="⚡ REQUESTING MISSING FRAMES",
        right_info="5 Missing",
        status_line="Point camera at Sender while Sender reads this request...",
        extra_line="Missing indices: [14, 89, 210, 450, 712]...",
        color_code=C_RED,
        width=W
    )
    print(hdr_rx_nack)

    # -------------------------------------------------------------
    # 14. Receiver: Verified & Saved Completion Card
    # -------------------------------------------------------------
    section_divider("Receiver: Transfer Complete & Saved Card", screen_idx, TOTAL_SCREENS)
    screen_idx += 1

    hdr_rx_done = render_header_card(
        tag="✔ TRANSFER COMPLETE & VERIFIED",
        right_info="145.20 KB",
        status_line=f"Saved to: {C_GREEN}./received_files/document_secret.pdf{RST}",
        extra_line=f"SHA-256: {DIM}e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b...{RST}",
        color_code=C_GREEN,
        width=W
    )
    print(hdr_rx_done)

    # Exit Box
    render_rounded_box(
        title=None,
        body_lines=[
            f"{C_WHITE}✔ All transmissions finished. Exiting AQRDT. Goodbye!{RST}"
        ],
        color_code=C_GREEN,
        width=W,
        indent=2
    )

    print(f"\n{BLD}{C_WHITE}================================================================================{RST}")
    print(f"{BLD}{C_GREEN}             END OF UI PREVIEW CATALOG ({TOTAL_SCREENS} TOTAL SCREENS)            {RST}")
    print(f"{BLD}{C_WHITE}================================================================================{RST}\n")


if __name__ == "__main__":
    main()
