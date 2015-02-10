#include <assert.h>
#include <iostream.h>
#include <strings.h>
#include <vector>
#include <string>
#include <math.h>
#include <sunmath.h>

class A {
public:
    A() { foo(); }
    virtual ~A() { foo(); }
    virtual void foo() const { cout << "A" << endl; }
};

class B : public A {
public:
    B() : A() { foo(); }
    virtual ~B() { foo(); }
    virtual void foo() const { cout << "B" << endl; }
};

class C : public B {
public:
    C() : B() { foo(); }
    virtual ~C() { foo(); }
    virtual void foo() const { cout << "C" << endl; }
};


int main(int argc, char** argv) {
    cout << 1 << endl;
    { A a; }

    cout << 2 << endl;
    { B b; }

    cout << 3 << endl;
    { C c; }

    return 0;
}
