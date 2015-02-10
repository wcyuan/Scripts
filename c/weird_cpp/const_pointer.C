#include <iostream>
using namespace std;

/*
 * why can't you assign a (double**) to a (const double**) ?
 */
int main(int argc, char **argv) 
{
    int    dargc = argc;
    char **dargv = argv;

    double *xp;
    xp = new double [10];
    for (int i = 0; i < 10; i++) {
	xp[i] = 0.0;
    }

    double *yp;
    yp = new double [10];
    for (int i = 0; i < 10; i++) {
	yp[i] = 0.0;
    }

    double **xpp;
    xpp = new double * [10];
    for (int i = 0; i < 10; i++) {
	xpp[i] = new double [10];
	for (int j = 0; j < 10; j++) {
	    xpp[i][j] = 0.0;
	}
    }

    // This is a variable pointer to a const double You can change
    // what it points to, but you can't use it to change what it's
    // pointing to.
    const double *cdblp;
    cdblp = xp;

    // These point to the same thing
    cout << xp[0] << endl;
    cout << cdblp[0] << endl;

    // You can still change the original, though
    xp[0] = 1.0;
    cout << xp[0] << endl;
    cout << cdblp[0] << endl;

    // You can change the pointer to point to a different thing
    cdblp = yp;
    cout << yp[0] << endl;
    cout << cdblp[0] << endl;
    yp[0] = 2.0;
    cout << yp[0] << endl;
    cout << cdblp[0] << endl;

    // But you can't use the pointer to the const to change the value.
    // The next line is a compiler error:
    //   assignment of read-only location
    //cdblp[0] = 0.0;

    // This is a pointer to a const pointer to a const double
    // You can set what it points to
    const double *const *cdblpcp;
    cdblpcp = xpp;

    // But you can't use it to set any values.  The following are
    // compiler errors.
    //cdblpcp[0] = xp;
    //cdblpcp[0][0] = 0.0;

    // This is a pointer to a pointer to a const double
    const double **cdblpp;
    // However, you can't set this equal to a regular pointer to a pointer to a double.
    // I'm not sure why.
    // The next line causes a compiler error
    //    invalid conversion from ‘double**’ to ‘const double**’
    //cdblpp = xpp;
    // Note, this is a slightly different error than the others

    // This is allowed
    cdblpp = new const double*[10];
    cdblpp[0] = xp;

    // This is the expected compiler error, since we can't use cdblpp
    // to change the double value
    //    assignment of read-only location
    //cdblpp[0][0] = 0.0;


    // The reason you can't set a const double** equal to a double** is described here:
    //
    // http://www.parashift.com/c++-faq-lite/constptrptr-conversion.html
    //
    // int main()
    // {
    // 	const Foo x;
    // 	Foo* p;
    // 	Foo const** q = &p;  // q now points to p; this is (fortunately!) an error
    // 	*q = &x;             // p now points to x
    // 	p->modify();         // Ouch: modifies a const Foo!!
    // 	...;
    // }
    //
    // and here:
    // 
    // http://c-faq.com/ansi/constmismatch.html
    //
    // const char c = 'x';		/* 1 */
    // char *p1;			/* 2 */
    // const char **p2 = &p1;		/* 3 */
    // *p2 = &c;			/* 4 */
    // *p1 = 'X';			/* 5 */

    return 0;
}
