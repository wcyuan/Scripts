/* $Header: /u/yuanc/testbed/C/RCS/strrev.c,v 1.3 2006/10/02 16:55:34 yuanc Exp $ */
void strrev (char * in_string) {
    int len, ii, front, back;
    if (in_string == NULL) {
	return;
    }
    len = strlen(in_string);
    if (1) {
	for (ii = 0; ii < len / 2; ii++) {
	    /* swap ii and len-ii-1 */
	    char tmp = in_string[ii];
	    in_string[ii] = in_string[len-ii-1];
	    in_string[len-ii-1] = tmp;
	}
    } else {
	/* or */
	for (front = 0, back = len -1; front < back; front++, back --) {
	    /* swap front and back */
	    char tmp = in_string[front];
	    in_string[front] = in_string[back];
	    in_string[back] = tmp;
	}
    }
}

int main (int argc, char **argv) {
    int ii;
    strrev(NULL);
    for (ii = 0; ii < argc; ii++) {
	strrev(argv[ii]);
	printf("%s ", argv[ii]);
    }
    printf("\n");
    return EXIT_SUCCESS;
}
