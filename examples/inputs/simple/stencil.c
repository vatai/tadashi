#include <stdio.h>
#include <stdlib.h>
#include <time.h>
# define TILE_SIZE 32

void stencil_2d(double *input, double *output, size_t rows, size_t cols) {
    #pragma scop
    for (size_t i = 1; i < rows - 1; i++) {
    for (size_t j = 1; j < cols - 1; j++) {
      output[i * cols + j] = (input[i * cols + j] +
                              input[(i - 1) * cols + j] +
                              input[(i + 1) * cols + j] +
                              input[i * cols + (j - 1)] +
                              input[i * cols + (j + 1)]) /
                              5.0;
      }
    }
    #pragma endscop
}

void stencil_2d_tiled(double *input, double *output, size_t rows, size_t cols) {
  
  for (size_t tile = 0; tile < cols/TILE_SIZE - 1; i++) {
  for (size_t i = 1; i < rows - 1; i++) {
  for (size_t j = 1; j < cols - 1; j++) {
    output[i * cols + j] = (input[i * cols + j] +
                            input[(i - 1) * cols + j] +
                            input[(i + 1) * cols + j] +
                            input[i * cols + (j - 1)] +
                            input[i * cols + (j + 1)]) /
                            5.0;
    }
  }
  
}

int main() {
  size_t rows = 1000;
  size_t cols = 200000;
  clock_t start, end;
  double cpu_time_used;

  // Allocate memory for input and output arrays
  double *input = (double *)malloc(rows * cols * sizeof(double));
  double *output = (double *)malloc(rows * cols * sizeof(double));

  // Initialize input array
  for (int i = 0; i < rows; i++) {
    for (int j = 0; j < cols; j++) {
      input[i * cols + j] = (double)((i * cols + j) % 3); // Example initialization
      output[i*cols +j] = 0.0; //initialize the output array to zero.
    }
  }

  // Apply stencil
  start = clock();
  stencil_2d(input, output, rows, cols);
  end = clock();
  cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
  // printf("CPU time used: %f seconds\n", cpu_time_used);
  printf("WALLTIME: %f\n", cpu_time_used);

  // Print output array
//   printf("Input array:\n");
//   for (int i = 0; i < 10; i++) {
//     for (int j = 0; j < 10; j++) {
//       printf("%.2f ", input[i * cols + j]);
//     }
//     printf("\n");
//   }

//   printf("\nOutput array:\n");
//   for (int i = 0; i < 10; i++) {
//     for (int j = 0; j < 10; j++) {
//       printf("%.2f ", output[i * cols + j]);
//     }
//     printf("\n");
//   }

  // Free allocated memory
  free(input);
  free(output);

  return 0;
}