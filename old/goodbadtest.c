/*
 * Demo of numerical instability not easily caught by testing.
 *
 * Emil Vatai
 *
 */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 3

double gold(double input[N]) {
  double result = 0;
  for (int i = 0; i < N; i++)
    result += input[i];
  return result;
}

double cgpt(double input[N]) {
  double result = 0;
  for (int i = N - 1; i >= 0; i--)
    result += input[i];
  return result;
}

double compare(double input[N]) {
  double delta = gold(input) - cgpt(input);
  int equal = delta == 0.0;
  printf("Equal? %s; delta: %0.20lf; ", equal ? "yes" : "no ", delta);
  printf("gold: %f; cgpt: %f;\n", gold(input), cgpt(input));
}

void unittest(int kpass) {
  srand((unsigned int)time(NULL));
  double input[N];
  for (int k = 0; k < kpass; k++) {
    for (int i = 0; i < N; i++) {
      input[i] = (double)rand();
    }
    compare(input);
  }
}

int main(int argc, char *argv[]) {
  unittest(10);
  double tricky_input[] = {400000000, 9e-8, 9e-8};
  printf("And now for some tricky input:\n");
  compare(tricky_input);
  return 0;
}
