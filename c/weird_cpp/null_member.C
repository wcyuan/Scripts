/*
 * if the compiler inlines a member function call
 * then if you take a null pointer and call that
 * member function, it will succeed!
 */

/*
e.g.
    for (i = 0; i < nports; i++) {
	ports[i]->lose_shrd();
	if (close) {
	    close_ports[i]->lose_shrd();
	}
    }
*/


