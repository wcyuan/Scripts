#include <iostream.h>

class NON_EXPLICIT {
public:
    bool _b;
    NON_EXPLICIT(bool b = true) : _b(b) { }
};

void cNEfunc (const NON_EXPLICIT& ne) {
    if (ne._b) {
	cout << "TRUE" << endl;
    } else {
	cout << "FALSE" << endl;
    }
}

void NEfunc (NON_EXPLICIT& ne) {
    if (ne._b) {
	cout << "TRUE" << endl;
    } else {
	cout << "FALSE" << endl;
    }
}

int main (int argc, char** argv) {
    int i = 2;
    // no compiler warning!
    // reason:
    // i is cast to a NON_EXPLICIT, which calls NON_EXPLICIT's 
    // constructor with argument i.  the resulting anonymous 
    // NON_EXPLICIT object is kept on cNEfunc's stack and 
    // passed in as an argument to cNEfunc.  no warning necessary.
    // 
    // solution: 
    // make NON_EXPLICIT's constructor explicit
    // explicit NON_EXPLICIT(bool b = true) : _b(b) { }
    cNEfunc(i);
    // cryptic compiler warning: foofunc requires an lvalue
    // reason:
    // the anonymous NON_EXPLICIT object on NEfunc's stack 
    // (see above) is not a valid lvalue 
    // (this is just a safety feature they built into C++)
    NEfunc(i);
}

