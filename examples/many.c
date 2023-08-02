#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

void init(double *data, size_t M, size_t N) {
  for (size_t i = 0; i < M * N; i++) {
    data[i] = rand();
  }
}

void print_matrix(double *data, size_t M, size_t N) {

  for (size_t i = 0; i < M; i++) {
    for (size_t j = 1; j < N - 1; j++) {
      size_t idx = i * M + j;
      printf("%15.2lf ", data[idx]);
    }
    printf("\n");
  }
}

void f(double *data, size_t M, size_t N) {
  // first scop: horizontal stencil
  for (size_t i = 0; i < M; i++) {
    for (size_t j = 1; j < N - 1; j++) {
      size_t idx = i * M + j;
      data[idx] = (data[idx - 1] + data[idx] + data[idx + 1]) / 3;
    }
  }

  // non-scop part;
  for (size_t t = 0; t < M * N; t++) {
    int r = rand();
    if (r == 0) {
      data[t] = 0;
    } else if (r % 2 == 0) {
      data[t] = -data[t];
    } else {
      data[t] = 2 * data[t];
    }
  }

  // second scop: vertical stencil
  for (size_t i = 1; i < M - 1; i++) {
    for (size_t j = 0; j < N; j++) {
      size_t idx = i * M + j;
      data[idx] = (data[idx - M] + data[idx] + data[idx + M]) / 3;
    }
  }
}

void g(double *data, size_t M, size_t N) {
  // third stencil
  for (size_t i = 1; i < M - 1; i++) {
    for (size_t j = 0; j < N; j++) {
      size_t idx = i * M + j;
      data[idx] = (data[idx - M] + data[idx - 1] + data[idx] + data[idx + 1] +
                   data[idx + M]) /
                  5;
    }
  }
}

int main(int argc, char *argv[]) {
  size_t M = 10, N = 10;
  double *data = malloc(M * N * sizeof(double));

  init(data, M, N);
  print_matrix(data, M, N);
  f(data, M, N);
  g(data, M, N);
  printf("====\n");
  print_matrix(data, M, N);
  free(data);
  printf("Done\n");
  return 0;
}
