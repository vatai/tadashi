#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define SIZE 2200

int
main() {
  // double mat1[SIZE][SIZE], mat2[SIZE][SIZE], result[SIZE][SIZE];
  double *mat1, *mat2, *result;
  mat1 = (double *)malloc(SIZE * SIZE * sizeof(double));
  mat2 = (double *)malloc(SIZE * SIZE * sizeof(double));
  result = (double *)malloc(SIZE * SIZE * sizeof(double));
  clock_t start, end;

  for (size_t i = 0; i < SIZE * SIZE; ++i)
    result[i] = -i * i % 7;
  double cpu_time_used;
  start = clock();

// result[i * SIZE + j] = 0;
#pragma scop
  for (int i = 0; i < SIZE; i++) {
    for (int j = 0; j < SIZE; j++) {
      for (int k = 0; k < SIZE; k++) {
        result[i * SIZE + j] += mat1[i * SIZE + k] * mat2[k * SIZE + j];
      }
    }
  }
#pragma endscop
  end = clock();
  cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
  // printf("CPU time used: %f seconds\n", cpu_time_used);
  double sum = 0;
  for (size_t i = 0; i < SIZE * SIZE; ++i)
    sum += result[i];
  fprintf(stderr, "%f\n", sum);
  printf("WALLTIME: %f\n", cpu_time_used);

  // // Print the result matrix
  // printf("Resultant matrix:\n");
  // for (int i = 0; i < rows1; i++) {
  //     for (int j = 0; j < cols2; j++) {
  //         printf("%d ", result[i][j]);
  //     }
  //     printf("\n");
  // }
  // print()
  // printf("%d ", result[i][j]);
  return 0;
}
