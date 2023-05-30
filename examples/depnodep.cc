#include "common.h"

void f(size_t N, double **A) {
#pragma scop
  for (size_t i = 1; i < N; i++) {
    for (size_t j = 0; j < N; j++) {
      A[i][j] = A[i][j] + A[i - 1][j];
    }
  }
#pragma endscop
}

int main(int argc, char *argv[]) {
  const size_t N = 10;
  double A[N][N];
  for (int i = 0; i < N; ++i) {
    init_arr(N, A[i]);
    print_arr(N, A[i]);
  }
  f(N, A);
  for (int i = 0; i < N; ++i) {
    print_arr(N, A[i]);
  }

  return 0;
}
