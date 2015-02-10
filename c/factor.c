void factor(int n) {
    int ii;
    n = abs(n);
    printf("%d: \n", n);
    for(ii = 2; n > 1 && ii < sqrt(n); ii++) {
	while (n % ii == 0) {
	    printf("%d ", ii);
	    n /= ii;
	}
    }
    printf("%d\n", n);
}

int main (int argc, char **argv) {
    for( ; argc > 1; --argc , ++argv) {
	factor(atoi(argv[1]));
    }
    return EXIT_SUCCESS;
}
