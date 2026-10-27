#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>
static double a(int i, int j) { return 1.0 / ((i + j) * (i + j + 1) / 2 + i + 1); }
static void mul_av(const std::vector<double> &v, std::vector<double> &out) {
  for (size_t i = 0; i < v.size(); i++) { double s = 0; for (size_t j = 0; j < v.size(); j++) s += a(i, j) * v[j]; out[i] = s; }
}
static void mul_atv(const std::vector<double> &v, std::vector<double> &out) {
  for (size_t i = 0; i < v.size(); i++) { double s = 0; for (size_t j = 0; j < v.size(); j++) s += a(j, i) * v[j]; out[i] = s; }
}
static void mul_atav(const std::vector<double> &v, std::vector<double> &out, std::vector<double> &tmp) { mul_av(v, tmp); mul_atv(tmp, out); }
int main(int argc, char **argv) {
  int n = argc > 1 ? std::atoi(argv[1]) : 100;
  std::vector<double> u(n, 1.0), v(n), tmp(n);
  for (int i = 0; i < 10; i++) { mul_atav(u, v, tmp); mul_atav(v, u, tmp); }
  double vbv = 0, vv = 0;
  for (int i = 0; i < n; i++) { vbv += u[i] * v[i]; vv += v[i] * v[i]; }
  std::printf("%.9f\n", std::sqrt(vbv / vv));
}
