/* $Header: /u/yuanc/testbed/C/weird_cpp/RCS/inheritance.C,v 1.1 2003/10/23 19:15:33 yuanc Exp $ */

#include <iostream.h>

class B {
public:
    void foo() {
	std::cout << "B::foo" << std::endl;
    }
};

class D1 : private B {
public:
    void bar() {
	std::cout << "D1::bar" << std::endl;
    }
};

class D2 : protected B {
public:
    void bar() {
	std::cout << "D2::bar" << std::endl;
    }
};

class D3 : public B {
public:
    void bar() {
	std::cout << "D3::bar" << std::endl;
    }
};

int main () {
    B b;
    D1 d1;
    D2 d2;
    D3 d3;
    B* bp;
    bp = &b;
    bp->foo();
    // error, can only do this if D1 inherits publicly from B
    bp = &d1;
    bp->foo();
    // error, can only do this if D2 inherits publicly from B
    bp = &d2;
    bp->foo();
    
    bp = &d3;
    bp->foo();

    return 0;
}

