void
f(int _PB_H, int _PB_W, float imgOut[_PB_W][_PB_H], float y1[_PB_W][_PB_H]) {
  int j, i;
  float tm1;
#pragma scop
  for (j = 0; j < _PB_H; j++) {
    tm1 = 0.0;
    for (i = 0; i < _PB_W; i++) {
      y1[i][j] = imgOut[i][j] + tm1;
      tm1 = imgOut[i][j];
    }
  }
#pragma endscop
}
