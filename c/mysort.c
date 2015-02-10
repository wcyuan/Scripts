void swap(int* arr, int i, int j) 
{
    int t = arr[i];
    arr[i] = arr[j];
    arr[j] = t;
}

void bsort(int* arr, int size) 
{
    int i, j;
    for(j = size-1; j > 0; j--)
	for (i = 0; i < j; i++)
	    if (arr[i] > arr[i+1])
		swap(arr, i, i+1);
}

void qusort(int* arr, int size) 
{
    int i, j = 1;
    if (size < 2) return;
    for (i = 1; i < size; i++) 
	if (arr[i] < arr[0]) 
	    swap(arr, i, j++);
    swap(arr, 0, j-1);
    qusort(arr+j,size-j);
    qusort(arr,j);
}

void mergesort(int* arr, int size) 
{
    int i,j,k = size/2;
    if (size < 2) return;
    mergesort(arr,k);
    mergesort(arr+k,size-k);
    for(i = 0; i < size; i++)
	/* 
	 * doesn't work 
	 * probably can't do mergesort in place
	 */
	if (arr[i] > arr[k])
	    swap(arr,i,k++);
}

#define MAX_ARR 100

int main (int argc, char** argv) 
{
    int i,j;
    int a[MAX_ARR];
    /* eat the program name */
    argc--; argv++;
    for (i = 0; i < argc && i < MAX_ARR; i++)
	a[i] = atoi(argv[i]);
    bsort (a,i);
    for (j = 0; j < i; j++)
	printf("%d ", a[j]);
    printf ("\n");
    return EXIT_SUCCESS;
}
