
void f(int n) {
  double a[n], b[n], M[n][n];
#pragma scop
  for (int i = 0; i <= n; i++) {
    a[i] = 0.0;
    for (int j = 0; j <= n; j++)
      a[i] += b[j] * M[i][j];
  }
#pragma endscop
}

void g(int n, double *a) {
#pragma scop
  for (int i = 1; i < n; i++) {
    a[i] = 2 * a[i - 1];
  }
#pragma endscop
}
