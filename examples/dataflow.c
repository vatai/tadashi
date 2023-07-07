#include <stdlib.h>

float f1(float);
float f2(float);

int main() {
  int n = 10;
  float t;
  float *A, *B;
  /* float *A = malloc(n * sizeof(*A)); */
  /* float *B = malloc(n * sizeof(*B)); */

#pragma scop
  for (int i = 0; i < n; ++i) {
  S:
    t = f1(A[i]);
  T:
    B[i] = f2(t);
  }
#pragma endscop
  return 0;
}
