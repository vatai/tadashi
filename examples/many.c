#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

void f(size_t M, size_t N, double data[M][N]) {
  // first scop: horizontal stencil
  for (size_t i = 0; i < M; i++) {
    for (size_t j = 1; j < N - 1; j++) {
      data[i][j] = (data[i - 1][j] + data[i][j] + data[i + 1][j]) / 3;
    }
  }

  // non-scop part;
  int r = rand() % (N * M);
  for (size_t t = 1; t < r; t++) {
    // int r = rand();
    size_t i = r / N, j = r % N;
    if (r == 0) {
      data[i][j] = 0;
    } else if (r % 2 == 0) {
      data[i][j] -= 0.5 * data[i][j];
    } else {
      data[i][j] -= 1.5 * data[i][j];
    }
  }

  // second scop: vertical stencil
  for (size_t i = 1; i < M - 1; i++) {
    for (size_t j = 0; j < N; j++) {
      data[i][j] = (data[i][j - 1] + data[i][j] + data[i][j + 1]) / 3;
    }
  }
}

void g(size_t M, size_t N, double data[M][N]) {
  // third stencil
  for (size_t i = 1; i < M - 1; i++) {
    for (size_t j = 1; j < N - 1; j++) {
      data[i][j] = (data[i][j - 1] + data[i - 1][j] + data[i][j] +
                    data[i + 1][j] + data[i][j + 1]) /
                   5;
    }
  }
}

void init(size_t M, size_t N, double data[M][N]) {
  for (size_t i = 0; i < M; i++) {
    for (size_t j = 0; j < N; j++) {
      data[i][j] = rand();
    }
  }
}

void print_matrix(size_t M, size_t N, double data[M][N]) {

  for (size_t i = 0; i < M; i++) {
    for (size_t j = 1; j < N - 1; j++) {
      size_t idx = i * N + j;
      printf("%15.2lf ", data[i][j]);
    }
    printf("\n");
  }
}

int main(int argc, char *argv[]) {
  size_t M = 10, N = 10;
  double data[M][N];

  init(M, N, data);
  print_matrix(M, N, data);
  f(M, N, data);
  g(M, N, data);
  printf("====\n");
  print_matrix(M, N, data);
  printf("Done\n");
  return 0;
}
