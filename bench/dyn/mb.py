# mandelbrot: a straight port of bench/mbt.c (one thread), printing the bitmap's MD5
import hashlib
import sys

def inside(cr, ci):
    zr = zi = tr = ti = 0.0
    for _ in range(10):
        for _ in range(5):
            zi = (zr + zr) * zi + ci
            zr = tr - ti + cr
            tr = zr * zr
            ti = zi * zi
        if tr + ti > 4.0:
            return False
    return True

def main():
    size = ((int(sys.argv[1]) if len(sys.argv) > 1 else 200) + 7) // 8 * 8
    row = size // 8
    inv = 2.0 / size
    print(f"P4\n{size} {size}")
    px = bytearray(size * row)
    for y in range(size):
        ci = y * inv - 1.0
        for x in range(row):
            byte = 0
            for bit in range(8):
                if inside((x * 8 + bit) * inv - 1.5, ci):
                    byte |= 0x80 >> bit
            px[y * row + x] = byte
    print(hashlib.md5(px).hexdigest())

main()
