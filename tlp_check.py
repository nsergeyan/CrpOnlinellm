import os, re, sys

def load(path):
    name = os.path.basename(path)
    tiers = int(re.match(r"data(\d+)-(\d+)-(\d+)\.dat", name).group(1))
    with open(path) as f:
        lines = [l.split() for l in f if l.strip()]
    S, N = int(lines[0][0]), int(lines[0][1])
    stacks = [[int(x) for x in row[1:]] for row in lines[1:1 + S]]  # bottom -> top
    return stacks, N, tiers + 2

def tlp(stacks, N, H):
    st = [s[:] for s in stacks]
    moves = 0
    for target in range(1, N + 1):
        src = next(i for i, s in enumerate(st) if target in s)
        while st[src][-1] != target:
            best = None
            for i, s in enumerate(st):  # leftmost lowest stack wins
                if i != src and (best is None or len(s) < len(st[best])):
                    best = i
            assert len(st[best]) < H
            st[best].append(st[src].pop())
            moves += 1
        st[src].pop()
    return moves

d = sys.argv[1] if len(sys.argv) > 1 else "data/caserta_840"
files = [f for f in os.listdir(d) if re.match(r"data\d+-\d+-\d+\.dat$", f)]
total = sum(tlp(*load(os.path.join(d, f))) for f in files)
print(len(files), "instances, TLP total relocations =", total)