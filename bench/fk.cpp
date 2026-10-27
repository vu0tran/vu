#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <vector>
int main(int argc, char **argv) {
  int n = argc > 1 ? std::atoi(argv[1]) : 7;
  std::vector<int> perm(n), perm1(n), count(n);
  int max_flips = 0, checksum = 0, perm_count = 0, r = n;
  for (int i = 0; i < n; i++) perm1[i] = i;
  for (;;) {
    while (r != 1) { count[r - 1] = r; r--; }
    perm = perm1;
    int flips = 0;
    while (perm[0] != 0) {
      std::reverse(perm.begin(), perm.begin() + perm[0] + 1);
      flips++;
    }
    max_flips = std::max(max_flips, flips);
    checksum += perm_count % 2 == 0 ? flips : -flips;
    for (;;) {
      if (r == n) { std::printf("%d\nPfannkuchen(%d) = %d\n", checksum, n, max_flips); return 0; }
      std::rotate(perm1.begin(), perm1.begin() + 1, perm1.begin() + r + 1);
      if (--count[r] > 0) break;
      r++;
    }
    perm_count++;
  }
}
