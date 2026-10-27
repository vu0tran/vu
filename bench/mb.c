#include <openssl/evp.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
static bool inside(double cr, double ci) {
  double zr = 0, zi = 0, tr = 0, ti = 0;
  for (int b = 0; b < 10; b++) {
    for (int k = 0; k < 5; k++) { zi = (zr + zr) * zi + ci; zr = tr - ti + cr; tr = zr * zr; ti = zi * zi; }
    if (tr + ti > 4.0) return false;
  }
  return true;
}
int main(int argc, char **argv) {
  int size = ((argc > 1 ? atoi(argv[1]) : 200) + 7) / 8 * 8, row = size / 8;
  double inv = 2.0 / size;
  printf("P4\n%d %d\n", size, size);
  unsigned char *px = malloc((size_t)size * row);
  for (int y = 0; y < size; y++) {
    double ci = y * inv - 1.0;
    for (int x = 0; x < row; x++) {
      unsigned char byte = 0;
      for (int bit = 0; bit < 8; bit++) if (inside((x * 8 + bit) * inv - 1.5, ci)) byte |= 0x80 >> bit;
      px[y * row + x] = byte;
    }
  }
  unsigned char md[16]; unsigned int len;
  EVP_Digest(px, (size_t)size * row, md, &len, EVP_md5(), NULL);
  for (int i = 0; i < 16; i++) printf("%02x", md[i]);
  printf("\n");
  free(px);
}
