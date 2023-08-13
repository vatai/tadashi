void f(int M,double* A1, double* B1, double* C1) {
  // double A1[M], B1[M], C1[M];
#pragma scop
  for(int i = -M+1; i >= 0; i--){
    C1[i] = A1[i] + B1[i];
  }
#pragma endscop
}
