#include <iostream.h>

class B {
public:
    virtual const B& operator= (const B& b) {
	cout << "B::operator=" << endl;
	return *this;
    }
};


class D : public B {
public:
    virtual const D& operator= (const D& d) {
	cout << "D::operator=" << endl;
	return *this;
    }
};


int main () {

    B b;
    D d;
    
    B *bp;
    B *bp2;
    D *dp;

    bp = &b;
    bp2 = &d;
    dp = &d;

    b = b;
    // calls B::operator=
    b = d;
    d = d;
    // compile time error
    //d = b;
    *bp = d;
    *bp = b;
    *bp2 = b;
    *bp2 = d;

    D d1;
    D d2;
    bp = &d1;
    bp2 = &d2;
    // even though these are two objects of type D, 
    // this calls B::operator= because it looks at the type of the pointer
    *bp = *bp2;

    // this calls D::operator=
    d1 = d2;

    // compile time error
    //*dp = b;
    *dp = d;

    return 0;
}
