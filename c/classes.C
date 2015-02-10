#include <iostream>
using namespace std;

class B {
public:
    virtual void foo () {
	cout << "B::foo()" << endl;
    }
    virtual void bar () {
	foo();
    }
};

class D : public B {
public:
    virtual void foo () {
	cout << "D::foo()" << endl;
	B::foo();
    }
};

int
main() {
    D d;
    d.bar();
    return 0;
}

