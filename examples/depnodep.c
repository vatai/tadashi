#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>

void
print_arr(int N, double *A) {
  for (int i = 0; i < N; ++i) {
    printf("%lf, ", A[i]);
  }
  printf("\n");
}

void
init_arr(int N, double *A) {
  for (int i = 0; i < N; ++i) {
    A[i] = random();
  }
}

const int N = 100000;

void
f(int N, double A[N][N]) {
#pragma scop
  for (int i = 1; i < N; i++) {
    for (int j = 0; j < N; j++) {
      A[i][j] = A[i][j] + A[i - 1][j];
    }
  }
#pragma endscop
}

int
main(int argc, char *argv[]) {
  long time;
  struct timeval tv;
  double A[N][N];

  for (int i = 0; i < N; ++i) {
    init_arr(N, A[i]);
  }
  gettimeofday(&tv, NULL);
  time = (long)tv.tv_sec * 1000 + (long)tv.tv_usec / 1000;
  f(N, A);
  gettimeofday(&tv, NULL);
  time = ((long)tv.tv_sec * 1000 + (long)tv.tv_usec / 1000) - time;
  printf("WALLTIME: %ld\n", time);
  return 0;
}
