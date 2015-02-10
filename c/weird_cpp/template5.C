#include <iostream.h>

template<class C>
class B {
public:
    void foo () {
	cout << "B::foo" << endl;
    }
};

typedef B<int> B_int;

class D : public B_int {
public:
    void bar () {
	cout << "D::bar" << endl;
    }
};

int main () {
    B<char> b;
    b.foo();
    D d;
    d.bar();
    return 0;
}
