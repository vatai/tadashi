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

const int N = 1000;

void
f(int N, double A[N][N]) {
#pragma scop
  for (int c0 = 20 * N + 1; c0 < 21 * N; c0 += 1)
    for (int c1 = 0; c1 < N; c1 += 1)
      A[-20 * N + c0][c1] = (A[-20 * N + c0][c1] + A[-20 * N + c0 - 1][c1]);
#pragma endscop
}

int
main(int argc, char *argv[]) {
  long time;
  struct timeval tv;
  double A[N][N];

  for (int i = 0; i < N; ++i) {
    init_arr(N, A[i]);
    print_arr(N, A[i]);
  }
  gettimeofday(&tv, NULL);
  time = (long)tv.tv_sec * 1000 + (long)tv.tv_usec / 1000;
  f(N, A);
  gettimeofday(&tv, NULL);
  time = ((long)tv.tv_sec * 1000 + (long)tv.tv_usec / 1000) - time;
  /* for (int i = 0; i < N; ++i) { */
  /*   print_arr(N, A[i]); */
  /* } */
  printf("WALLTIME: %ld\n", time);
  return 0;
}
