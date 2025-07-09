void
f(double a1[30000], double a2[30000], int Ni, int Nj, int Nk, int N1, int N2,
  int Nt) {
#pragma scop
  for (int i = 0; i < Ni; i++) {
    for (int j = 0; j < Nj; j++) {
      for (int k = 0; k < Nk; k++) {
        for (int t = 0; t < Nt; ++t) {

          for (int i1 = 0; i1 < N1; i1++) {
            a1[i + j + i1] = k + i1;
            a1[i + j + i1] += k + i1 + 1;
          }
        }
        for (int i2 = 0; i2 < N1; i2++) {
          a2[i + j + i2 + k] = a1[i + j + k];
        }
      }
    }
  }
#pragma endscop
}
