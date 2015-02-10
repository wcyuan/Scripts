int fib (int n) {
    int i, a = 1, b = 0;
    for (i = 0; i < n; i++) {
	a += b;
	b = a - b;
    }
    return a;
}

int main (int argc, char ** argv) 
{
    if (argc == 2) {
	int n = atoi(argv[1]);
	printf("%d\n", fib(n));
    }
    return EXIT_SUCCESS;
}
