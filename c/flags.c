int main (int argc, char **argv) {
    for (--argc, ++argv; argc; --argc, ++argv) {
	int shift = atoi(argv[1]);
	if (shift > 0)
	    printf("%x\n", 1 << (shift - 1));
    }
    return EXIT_SUCCESS;
}
