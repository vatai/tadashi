#include <iostream>
#include <random>
#include <stddef.h>

void print_arr(size_t N, double *A) {
  for (int i = 0; i < N; ++i) {
    std::cout << A[i] << ", ";
  }
  std::cout << std::endl;
}

void init_arr(size_t N, double *A) {
  std::random_device rd;
  std::mt19937 gen(rd());
  std::uniform_real_distribution<double> dis(0.0, 1.0);
  for (int i = 0; i < N; ++i) {
    A[i] = dis(gen);
  }
}

#define MAIN(fn_arr)                                                           \
  int main(int argc, char *argv[]) {                                           \
    size_t N = 8;                                                              \
    double A[N];                                                               \
                                                                               \
    init_arr(N, A);                                                            \
    print_arr(N, A);                                                           \
    fn_arr(N, A);                                                              \
    print_arr(N, A);                                                           \
                                                                               \
    return 0;                                                                  \
  }
