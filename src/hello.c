
void f(int n) {
#pragma scop
  double a[n], b[n], M[n][n];
  for (int i = 0; i <= n; i++) {
    a[i] = 0.0;
    for (int j = 0; j <= n; j++)
      a[i] += b[j] * M[i][j];
  }
#pragma endscop
}

void g(int n) {
#pragma scop
  double a[n];
  for (int i = 0; i < n; i++) {
    a[i] = 0.0;
  }
#pragma endscop
}
