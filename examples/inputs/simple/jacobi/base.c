#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#include "config.h"


void jacobi_2d_baseline(double **restrict grid1, double **restrict grid2) {
    #pragma scop
    double w, e, c, s, n;
    for (int iter = 0; iter < MAX_ITER; iter++) {
        for (int i = 0; i < N_x; i++) {
            for (int j = 0; j < N_y; j++) {
                c = grid1[i][j];
                w = (i == 0)    ? 0 : grid1[i-1][j];
                e = (i == N_x-1)  ? 0 : grid1[i+1][j];
                s = (j == 0)    ? 0 : grid1[i][j+1];
                n = (j == N_y-1)  ? 0 : grid1[i][j-1];
                grid2[i][j] = 0.20 * (w + e + c + n + s);
		//grid2[i][j] = 0.25 * (grid1[i+1][j] + grid1[i-1][j] + grid1[i][j+1] + grid1[i][j-1]);
            }
        }
        for (int i = 0; i < N_x; i++) {
            for (int j = 0; j < N_y; j++) {
                c = grid2[i][j];
                w = (i == 0)    ? 0 : grid2[i-1][j];
                e = (i == N_x-1)  ? 0 : grid2[i+1][j];
                s = (j == 0)    ? 0 : grid2[i][j+1];
                n = (j == N_y-1)  ? 0 : grid2[i][j-1];
                grid1[i][j] = 0.20 * (w + e + c + n + s);
		//grid1[i][j] = 0.25 * (grid2[i+1][j] + grid2[i-1][j] + grid2[i][j+1] + grid2[i][j-1]);
            }
        }
    }
    #pragma endscop
}

int main() {
    double **grid1 = (double **)malloc(N_x * sizeof(double *));
    double **grid2 = (double **)malloc(N_x * sizeof(double *));
    for (int i = 0; i < N_x; i++) {
        grid1[i] = (double *)malloc(N_y * sizeof(double));
        grid2[i] = (double *)malloc(N_y * sizeof(double));
    }
    
    initialize(grid1);
    
    clock_t start = clock();
    jacobi_2d_baseline(grid1, grid2);
    clock_t end = clock();
    printf("%f\n",grid2[0][0]);
    double time_baseline = ((double)(end - start)) / CLOCKS_PER_SEC;
    printf("Baseline execution time: %f seconds\n", time_baseline);

    initialize(grid1);

    for (int i = 0; i < N_x; i++) {
        free(grid1[i]);
        free(grid2[i]);
    }
    free(grid1);
    free(grid2);

    return 0;
}

