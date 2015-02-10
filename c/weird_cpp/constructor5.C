/* $Header: /u/yuanc/testbed/C/RCS/constructor4.C,v 1.1 2003/10/18 01:08:34 yuanc Exp $ */
#include<iostream.h>


class B {
public:
    B () : _i(0) {
	cout << "B::ctor: default" << endl;
    }
    B (int i) : _i(i) {
	cout << "B::ctor: " << _i << endl;
    }
    ~B() {
	cout << "B:dtor: " << _i << endl;
    }
    int _i;
};

class D : public B {
public:
    D () {
	cout << "D::ctor" << endl;
	// creates an object, doesn't call the initializer
	B(4);
    }
    ~D () {
	cout << "D::dtor" << endl;
    }
    
    void foo() {
	cout << "D::foo" << endl;
    }
};

int main () {
    D d;
    d.foo();
}
