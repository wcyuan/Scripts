/*
 * greycode.c
 *
 * grey codes are a complete ordering on binary numbers such that 
 * only one bit needs to be flipped from one number to the next.
 *
 * if you abstract flipping a bit to changing one place value by
 * one or negative one, this algorithm can be generalized to any
 * base.  
 *
 * $Id$
 *
 */

int total_bits, debug;

void initialize_array (int * array, int bits, int value) {
    int ii;
    for (ii = 0; ii <= bits; ii++) {
	array[ii] = value;
    }
}

void print_array (int * array, int bits) {
    int ii;
    for (ii = bits; ii >= 0; ii--) {
	printf ("%d", array[ii]);
    }
    printf ("\n");
}

void grey_code (int * array, int bits, int base, int parity) {
    int ii, next_parity; 
    if (bits < 0) {
	print_array (array, total_bits);
	return;
    }
    if (debug) 
	printf ("grey_code (array, %d, %d, %d)\n", bits, base,
		parity);

    /* either of these works */
    next_parity = (bits && array[bits-1]) ? -1 : 1;
    next_parity = (base % 2) ? parity : 1;

    for (ii = 1; ii < base; ii++) {
	grey_code (array, bits-1, base, next_parity);
	array[bits] += parity;
	next_parity *= -1;
    }
    grey_code (array, bits-1, base, next_parity);
}

int main (int argc, char ** argv) 
{
    int array[50];
    int base = 2;
    total_bits = 4;
    debug = 0;
    switch (argc) {
    case 4:
	debug = 1;
    case 3:
	base = atoi(argv[2]);
    case 2:
	total_bits = atoi(argv[1]) - 1;
	break;
    default:
	break;
    }
    initialize_array (array, total_bits, 0);
    grey_code (array, total_bits, base, 1);
    return EXIT_SUCCESS;
}
