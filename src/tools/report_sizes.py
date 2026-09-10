import os
import glob

def main():
    src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = []
    for root, _, filenames in os.walk(src_dir):
        if "scratch" in root or "__pycache__" in root:
            continue
        for fn in filenames:
            if fn.endswith('.py'):
                files.append(os.path.relpath(os.path.join(root, fn), src_dir))
    files.sort()
    print("-" * 55)
    print(f"{'Module / File':<32} {'Size':<12} {'Lines':<8}")
    print("-" * 55)
    total_sz = 0
    total_ln = 0
    for f in files:
        full_p = os.path.join(src_dir, f)
        sz = os.path.getsize(full_p) / 1024
        ln = sum(1 for _ in open(full_p, encoding='utf-8', errors='ignore'))
        total_sz += sz
        total_ln += ln
        print(f"{f:<32} {sz:6.1f} KB    {ln:5d}")
    print("-" * 55)
    print(f"{'TOTAL':<32} {total_sz:6.1f} KB    {total_ln:5d}")
    print("-" * 55)

if __name__ == '__main__':
    main()

