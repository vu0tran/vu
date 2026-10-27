/* zlib-format decompression with C zlib, N times: zb FILE.z N (prints the size and CRC-32 of the result).
   zlib is given an output buffer of exactly the right size (its best case: no growing). */
#include <stdio.h>
#include <stdlib.h>
#include <zlib.h>
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "rb"); fseek(f, 0, SEEK_END); long n = ftell(f); rewind(f);
    unsigned char *in = malloc(n); if (fread(in, 1, n, f) != (size_t)n) return 1; fclose(f);
    unsigned long cap = 64ul << 20; unsigned char *out = malloc(cap); unsigned long got = 0;
    for (int k = 0; k < atoi(argv[2]); k++) {
        got = cap;
        if (uncompress(out, &got, in, n) != Z_OK) { puts("error"); return 1; }
    }
    printf("%lu %lu\n", got, crc32(0, out, got));
    return 0;
}
