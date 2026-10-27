import sys, zlib
data = open(sys.argv[1], 'rb').read()
for _ in range(int(sys.argv[2])): out = zlib.decompress(data)
print(len(out), zlib.crc32(out))
