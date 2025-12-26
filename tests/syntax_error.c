#include <stdio.h>

int main(int argc, char *argv[])
{
  #define N 100
  #pragma scop
  int sum = 0;
  for (int i = 0; i < N; ++i) {
    sum += i;
  }
  #pragma endscop
  this file is intentionally broken.
  return 0;
}
