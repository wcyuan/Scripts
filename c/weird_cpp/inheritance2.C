#include <iostream>
using namespace std;

class B {
public:
    virtual void foo () {
	cout << "B::foo" << endl;
    }
};

class D : public B{
public:
    virtual void foo () {
	cout << "D::foo" << endl;
    }

};

class DD : public D {
public:
    virtual void foo () {
	cout << "DD::foo" << endl;
	B::foo();
    }
};

int main () {
    DD dd;
    dd.foo();
    return 0;
}
