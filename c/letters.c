int main (int argc, char **argv) {
    int total = 0;
    for (--argc, ++argv; argc; --argc, ++argv) {
	int ii = 0;
	while(argv[0][ii] != '\0') {
	    total += (int)argv[0][ii++];
	}
    }
    printf ("%d\n", total);
    return EXIT_SUCCESS;
}
