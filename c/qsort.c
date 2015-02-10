/*
 * $Header: /u/yuanc/testbed/c/RCS/qsort.c,v 1.2 2014/05/07 19:34:02 yuanc Exp $
 *
 * A simple program that does a quick sort.
 */

/*
 * Swap two elements in an array in-place
 */
void swap(int *arr, int first, int second) {
    int temp = arr[first];
    arr[first] = arr[second];
    arr[second] = temp;
}

/*
 * Sorts an integer array in-place
 *
 * start is the index of the first element
 * end is the index of the last element
 */
void quicksort(int *arr, int start, int end) {
    int pivot, first, ii;

    if (start >= end) {
        return;
    }
    pivot = arr[start];
    /* first points to the first element that is >= pivot */
    first = start + 1;
    for (ii = start + 1; ii <= end; ii++) {
        if (arr[ii] < pivot) {
            swap(arr, first, ii);
            first++;
        }
    }
    swap(arr, start, first-1);
    quicksort(arr, start, first-2);
    quicksort(arr, first, end);
}

/*
 * Convert an array of strings into an array of integers.
 * Strings that cannot be converted into integers become zero.
 */
int *convert_to_int(int argc, char **argv) {
    int *arr = malloc((argc-1)*sizeof(int));
    int ii;
    for (ii = 1; ii < argc; ii++) {
        arr[ii-1] = atoi(argv[ii]);
    }
    return arr;
}

/*
 * Print an array of integers
 */
void print_int_arr(int *arr, int len) {
    for (ii = 0; ii < len; ii++) {
        printf("%d ", arr[ii]);
    }
    printf("\n");
}

/*
 * The arguments should all be integers.
 * We'll sort them, then output a space-separated sorted list.
 */
int main(int argc, char **argv) {
    int *arr = convert_to_int(argc, argv);
    quicksort(arr, 0, argc-2);
    print_int_arr(arr, argc-1);
    return 0;
}

