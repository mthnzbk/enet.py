"""Build script to compile zpl-c/enet into a shared library.

Supports:
- Windows (enet.dll)
- Linux (libenet.so)
- macOS (libenet.dylib)

Compilers tested: zig, gcc, clang, msvc (cl).
"""

import os
import sys
import shutil
import subprocess

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
INCLUDE_DIR = os.path.join(ROOT_DIR, "enet-c", "include")
LIB_DIR = os.path.join(ROOT_DIR, "enet", "lib")

if not os.path.exists(INCLUDE_DIR):
    # Try enet/include if not renamed
    alt = os.path.join(ROOT_DIR, "enet", "include")
    if os.path.exists(alt):
        INCLUDE_DIR = alt

WRAPPER_C = os.path.join(ROOT_DIR, "_enet_amalgamation.c")
DEF_FILE = os.path.join(ROOT_DIR, "_enet.def")


def find_compiler():
    """Detect an available C compiler."""
    # 1. ziglang via python
    try:
        import ziglang
        return "python_zig"
    except ImportError:
        pass

    # 2. System binaries
    for cc in ["zig", "clang", "gcc", "cl"]:
        if shutil.which(cc):
            return cc

    return None


def generate_c_wrapper():
    with open(WRAPPER_C, "w", encoding="utf-8") as f:
        f.write(
            """#define _WINSOCK_DEPRECATED_NO_WARNINGS
#define ENET_IMPLEMENTATION
#define ENET_DLL
#include "enet.h"
"""
        )


def generate_def_file():
    # Export all public enet functions
    import re
    header_path = os.path.join(INCLUDE_DIR, "enet.h")
    with open(header_path, "r", encoding="utf-8", errors="ignore") as f:
        funcs = sorted(set(re.findall(r"(?:ENET_API|extern)\s+[\w\s\*]+\s+(enet_\w+)\s*\(", f.read())))

    with open(DEF_FILE, "w", encoding="utf-8") as f:
        f.write("EXPORTS\n")
        for fn in funcs:
            f.write(f"    {fn}\n")


def build():
    os.makedirs(LIB_DIR, exist_ok=True)
    generate_c_wrapper()
    cc = find_compiler()
    if not cc:
        print("ERROR: No C compiler found (zig, gcc, clang, cl).", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Detected compiler: {cc}")

    if sys.platform == "win32":
        out_name = os.path.join(LIB_DIR, "enet.dll")
        generate_def_file()
        if cc == "python_zig" or cc == "zig":
            cmd = [
                sys.executable, "-m", "ziglang", "cc" if cc == "python_zig" else "cc",
                "-shared", "-O3",
                "-target", "x86_64-windows-gnu",
                f"-I{INCLUDE_DIR}",
                WRAPPER_C,
                DEF_FILE,
                "-lws2_32", "-lwinmm",
                "-o", out_name,
            ]
            if cc == "zig":
                cmd = cmd[3:]  # start with 'zig'
        elif cc in ("gcc", "clang"):
            cmd = [
                cc, "-shared", "-O3",
                f"-I{INCLUDE_DIR}",
                WRAPPER_C,
                DEF_FILE,
                "-lws2_32", "-lwinmm",
                "-o", out_name,
            ]
        elif cc == "cl":
            cmd = [
                "cl", "/O2", "/LD",
                f"/I{INCLUDE_DIR}",
                WRAPPER_C,
                f"/DEF:{DEF_FILE}",
                "ws2_32.lib", "winmm.lib",
                f"/Fe:{out_name}",
            ]
    elif sys.platform == "darwin":
        out_name = os.path.join(LIB_DIR, "libenet.dylib")
        cmd = [
            cc if cc != "python_zig" else sys.executable,
            "-shared", "-O3", "-fPIC",
            f"-I{INCLUDE_DIR}",
            WRAPPER_C,
            "-o", out_name,
        ]
        if cc == "python_zig":
            cmd = [sys.executable, "-m", "ziglang", "cc", "-shared", "-O3", "-fPIC", f"-I{INCLUDE_DIR}", WRAPPER_C, "-o", out_name]
    else:  # Linux / POSIX
        out_name = os.path.join(LIB_DIR, "libenet.so")
        if cc == "python_zig":
            cmd = [sys.executable, "-m", "ziglang", "cc", "-shared", "-O3", "-fPIC", f"-I{INCLUDE_DIR}", WRAPPER_C, "-o", out_name]
        else:
            cmd = [
                cc, "-shared", "-O3", "-fPIC",
                f"-I{INCLUDE_DIR}",
                WRAPPER_C,
                "-o", out_name,
            ]

    print(f"[*] Compiling: {' '.join(cmd)}")
    res = subprocess.run(cmd)
    if res.returncode == 0 and os.path.isfile(out_name):
        print(f"[+] Successfully built: {out_name} ({os.path.getsize(out_name)} bytes)")
    else:
        print("[-] Build failed!", file=sys.stderr)
        sys.exit(1)

    # Clean temporary files
    for f in [WRAPPER_C, DEF_FILE]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass


if __name__ == "__main__":
    build()
