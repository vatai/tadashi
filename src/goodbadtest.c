#include <stdio.h>

#define N 4

double gold(double input[N]) {
  double result = 0;
  for (int i = 0; i < N; i++)
    result += input[i] * input[i];
  return result;
}

double cgpt(double input[N]) {
  double result = 0;
  for (int i = N - 1; i >= 0; i--)
    result += input[i] * input[i];
  return result;
}

double compare(double input[N]) {
  int equal = gold(input) == cgpt(input);
  double delta = gold(input) - cgpt(input);
  printf("Equal? %s; delta: %0.20lf; ", equal ? "yes" : "no ", delta);
  printf("gold: %f; cgpt: %f;\n", gold(input), cgpt(input));
}

int main(int argc, char *argv[]) {
  double tricky_input[] = {20000, 9e-5, 9e-4, 9e-4};
  compare(tricky_input);
  return 0;
}
