#include <stdio.h>
#include <time.h>
#include <stdlib.h>

#define SIZE 2000000UL
#define ITERS 200UL


int main(int argx, const char * argv[])
{
    clock_t start, end;
    double cpu_time_used;
    float *my_array = (float *) malloc (SIZE * sizeof(float));
    // init the array
    for (size_t i = 0; i < SIZE; i++)
    {
        my_array[i] = (float)i;
    }
    start = clock();
    #pragma scop
    for (size_t i=0; i<ITERS; i+=1)
        for (size_t j=0; j<SIZE; j+=1)
        {
            my_array[i] +=1;
            // printf("%zu\n", i);
        }
    #pragma endscop
    end = clock();
    cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
    printf("CPU time used: %f seconds\n", cpu_time_used);
}
