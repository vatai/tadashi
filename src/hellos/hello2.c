extern double *data;

void g(double *a, int n) {
  for (int i = -n + 1; i <= 0; i++) {
    a[-i] = data[-i] * data[-i];
  }
}
