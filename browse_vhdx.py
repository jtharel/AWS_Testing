from dissect.hypervisor.disk.vhdx import VHDX
from dissect.volume import disk
from dissect.ntfs import NTFS
import sys

fh = open("Profile.vhdx", "rb")
vhdx = VHDX(fh)
d = disk.Disk(vhdx)
part = list(d.partitions)[0]
vol = part.open()
ntfs = NTFS(vol)

def resolve(path):
    """Walk the NTFS tree to find an entry by path."""
    entry = ntfs.mft.root
    if path in ("", "/", "\\"):
        return entry
    parts = path.replace("\\", "/").strip("/").split("/")
    for p in parts:
        found = False
        for child in entry.listdir():
            if str(child).lower() == p.lower():
                entry = entry.get(str(child))
                found = True
                break
        if not found:
            return None
    return entry

def listdir(path):
    entry = resolve(path)
    if entry is None:
        print(f"  Path not found: {path}")
        return
    print(f"\n  Contents of: {path}\n")
    try:
        for child in entry.listdir():
            print(f"    {child}")
    except Exception as e:
        print(f"  Not a directory or error: {e}")

def cat(path):
    entry = resolve(path)
    if entry is None:
        print(f"  File not found: {path}")
        return
    try:
        data = entry.open().read()
        print(data.decode("utf-8", errors="replace"))
    except Exception as e:
        print(f"  Cannot read: {e}")

def save(path, outfile):
    entry = resolve(path)
    if entry is None:
        print(f"  File not found: {path}")
        return
    try:
        data = entry.open().read()
        with open(outfile, "wb") as f:
            f.write(data)
        print(f"  Saved {len(data)} bytes to {outfile}")
    except Exception as e:
        print(f"  Cannot read: {e}")

# If a path was passed as argument, list it
if len(sys.argv) > 1:
    cmd = sys.argv[1]
    path = sys.argv[2] if len(sys.argv) > 2 else "/"
    if cmd == "ls":
        listdir(path)
    elif cmd == "cat":
        cat(path)
    elif cmd == "save" and len(sys.argv) > 3:
        save(path, sys.argv[3])
    else:
        print("Usage:")
        print("  python browse_vhdx.py ls /path")
        print("  python browse_vhdx.py cat /path/to/file")
        print("  python browse_vhdx.py save /path/to/file output.txt")
else:
    print("Usage:")
    print("  python browse_vhdx.py ls /")
    print("  python browse_vhdx.py ls /88888888.jacob.raifo")
    print("  python browse_vhdx.py cat /88888888.jacob.raifo/AppData/Roaming/Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt")
    print("  python browse_vhdx.py save /path/to/file output.txt")
  
