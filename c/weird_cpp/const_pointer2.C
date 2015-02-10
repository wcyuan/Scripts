#include <iostream>

using namespace std;

class C {
public:
    const int * _i;
    C(const int &foo) :
	_i(&foo)
	{ }
    const int * const & get_i () { return _i; }
};

class D {
public:
    int _i;
    D(const int foo) :
	_i(foo)
	{ }
    int const & get_i () { return _i; }
};

int main(int argc, char **argv) 
{
    // shouldn't be allowed?
    C foo(9);
    int a =  7;    
    C bar(a);

    int b = 4;

    // not allowed.
    //bar.get_i() = &b;

    D baz(5);
    // not allowed
    //baz.get_i() = 8;

    cout << &b << endl;;
    cout << &a << endl;;
    cout << foo.get_i() << endl;;
    cout << bar.get_i() << endl;;
    cout << baz.get_i() << endl;;

    return 0;
}
