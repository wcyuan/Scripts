#include <iostream.h>

class B {
public:
    static void foo () {
	cout << "B::foo" << endl;
    }
};

class D : public B {
};

int main () {
    D::foo();

    return 0;
}
