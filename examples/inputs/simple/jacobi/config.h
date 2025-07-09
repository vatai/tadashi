#define N_x 2000      // X dimension Grid size
#define N_y 2000      // Y dimension Grid size
#define MAX_ITER 100 // Fixed number of iterations
#define TILE_SIZE_x 512  // X dimension tile size

void initialize(double **grid) {
    for (int i = 0; i < N_x; i++) {
        for (int j = 0; j < N_y; j++) {
            grid[i][j] = (i == 0 || i == N_x-1 || j == 0 || j == N_y-1) ? 1.0 : 0.0;
        }
    }
}
