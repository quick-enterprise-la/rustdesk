#!/usr/bin/env python3
"""Turn a RustDesk source tree into "Quick Remote Support" (WINDOWS build).

Run from the root of the RustDesk source (the folder with Cargo.toml):
    python quick-remote/brand.py --server 119.59.124.56 --key "<key from the server>"

What it changes:
  * app name, server address and server key   (libs/hbb_common/src/config.rs)  -- REQUIRED
  * Windows: product name / company in the .exe details (Cargo.toml, Runner.rc) -- cosmetic, tolerant
  * Windows icons (res/, flutter/windows/runner/resources/) and the logo shown above the ID/password

This Windows-only version skips the Android and macOS branding. Any icon/logo source
file that is missing is simply skipped, so the Windows build never fails on a missing asset.

RustDesk is AGPL-3.0: if you give this program to customers, publish the changed source
(keep your GitHub fork public). Quick Enterprise's own programs do not have to be published.
"""
import argparse
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

APP_NAME = "QuickRemoteSupport"          # internal name: no spaces (folders, service, quickremotesupport:// link)
PRODUCT = "Quick Remote Support"
COMPANY = "Quick Enterprise Software Development Sole Co., Ltd."
COPYRIGHT = "Copyright (C) 2026 Quick Enterprise Software Development Sole Co., Ltd. Based on RustDesk (AGPL-3.0)."


def edit(path, pairs, required=True):
    """Apply regex replacements. required=False -> warn (don't exit) if a pattern isn't found,
    so a cosmetic rename never breaks the build if RustDesk reorganised that file."""
    if not os.path.exists(path):
        if required:
            sys.exit(f"brand.py: {path} not found (run from the RustDesk source root with submodules).")
        print("  skip (no file)", path)
        return
    with open(path, encoding="utf-8") as f:
        text = f.read()
    for pattern, repl in pairs:
        new, n = re.subn(pattern, repl, text, flags=re.M)
        if n == 0:
            if required:
                sys.exit(f"brand.py: could not find {pattern!r} in {path}. RustDesk changed this file; update brand.py.")
            print(f"  warn: pattern not found in {path} (skipped): {pattern}")
            continue
        text = new
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    print("  changed", path)


def put(src, dst):
    s = os.path.join(HERE, src)
    if not os.path.exists(s):
        print("  skip (no source)", src)
        return
    d = os.path.dirname(dst)
    if d:
        os.makedirs(d, exist_ok=True)
    shutil.copyfile(s, dst)
    print("  copied ", dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True, help="IP or domain of your hbbs server, e.g. 119.59.124.56")
    ap.add_argument("--key", required=True, help="contents of id_ed25519.pub on the server")
    a = ap.parse_args()
    server, key = a.server.strip(), a.key.strip()
    if not re.fullmatch(r"[A-Za-z0-9.\-:]+", server):
        sys.exit("brand.py: --server must be an IP or domain name, e.g. 119.59.124.56")
    if not re.fullmatch(r"[A-Za-z0-9+/]{43}=", key):
        sys.exit("brand.py: --key must be the 44-character text from id_ed25519.pub on the server")
    if not os.path.exists("Cargo.toml") or not os.path.exists("libs/hbb_common/src/config.rs"):
        sys.exit("brand.py: run this from the RustDesk source folder (with submodules checked out)")

    # REQUIRED: app name + server + key (used by every platform, Windows included)
    edit("libs/hbb_common/src/config.rs", [
        (r'(pub static ref APP_NAME: RwLock<String> = RwLock::new\(")RustDesk("\.to_owned\(\)\);)', r"\g<1>" + APP_NAME + r"\g<2>"),
        (r'^pub const RENDEZVOUS_SERVERS: &\[&str\] = &\[[^\]]*\];', f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{server}"];'),
        (r'^pub const RS_PUB_KEY: &str = "[^"]*";', f'pub const RS_PUB_KEY: &str = "{key}";'),
    ], required=True)

    # Cosmetic: Windows .exe details (tolerant - never fails the build)
    edit("Cargo.toml", [
        (r'^LegalCopyright = ".*"$', f'LegalCopyright = "{COPYRIGHT}"'),
        (r'^ProductName = ".*"$', f'ProductName = "{PRODUCT}"'),
        (r'^FileDescription = ".*"$', f'FileDescription = "{PRODUCT}"'),
    ], required=False)
    edit("flutter/windows/runner/Runner.rc", [
        (r'(VALUE "CompanyName", )".*?"', r'\g<1>"' + COMPANY + '"'),
        (r'(VALUE "FileDescription", )".*?"', r'\g<1>"' + PRODUCT + '"'),
        (r'(VALUE "LegalCopyright", )".*?"', r'\g<1>"' + COPYRIGHT + '"'),
        (r'(VALUE "ProductName", )".*?"', r'\g<1>"' + PRODUCT + '"'),
    ], required=False)

    # Windows icons + the logo above the ID/password (missing sources are skipped)
    for dst in ("res/icon.ico", "res/tray-icon.ico", "flutter/windows/runner/resources/app_icon.ico"):
        put("icon.ico", dst)
    for dst in ("res/icon.png", "res/mac-icon.png"):
        put("icon.png", dst)
    put("icon.svg", "flutter/assets/icon.svg")
    put("icon.png", "flutter/assets/icon.png")
    for name in ("logo.png", "logo_light.png", "logo_dark.png"):
        put(name, "flutter/assets/" + name)

    print(f"Done: {PRODUCT} -> server {server}  (Windows branding applied)")


if __name__ == "__main__":
    main()
