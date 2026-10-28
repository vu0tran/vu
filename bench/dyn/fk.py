# fannkuch-redux: a straight port of bench/fk.c
import sys

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    perm1 = list(range(n))
    count = [0] * n
    max_flips = checksum = perm_count = 0
    r = n
    while True:
        while r != 1:
            count[r - 1] = r
            r -= 1
        perm = perm1[:]
        flips = 0
        k = perm[0]
        while k != 0:
            lo, hi = 0, k
            while lo < hi:
                perm[lo], perm[hi] = perm[hi], perm[lo]
                lo += 1
                hi -= 1
            flips += 1
            k = perm[0]
        if flips > max_flips:
            max_flips = flips
        checksum += flips if perm_count % 2 == 0 else -flips
        while True:
            if r == n:
                print(f"{checksum}\nPfannkuchen({n}) = {max_flips}")
                return
            first = perm1[0]
            for i in range(r):
                perm1[i] = perm1[i + 1]
            perm1[r] = first
            count[r] -= 1
            if count[r] > 0:
                break
            r += 1
        perm_count += 1

main()
