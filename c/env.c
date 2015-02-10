int main (int argc, char **argv) {
    for (--argc, ++argv; argc; --argc, ++argv) {
	char * val;
	if ((val = getenv(argv[0])) != NULL) 
	    printf("%s=%s\n", argv[0], getenv(argv[0]));
	else 
	    printf("no variable=%s\n", argv[0]);
    }
    return EXIT_SUCCESS;
}
