#include<iostream>

class B {
public:
    B () { std::cout << "B: Default constr " << std::endl; }
    B ( int j ) { std::cout << "B:Constr with " << j << std::endl; }
    B ( const B& b ) {
	std::cout << "B::copy constr" << std::endl;
    }

protected:
    void foo(int j) {
	std::cout << "B::foo " << j << std::endl;
    }
};

class D : public B {
public:
    int i;
    D ( int j ) : i(j) { std::cout << "Constr with " << j << std::endl; }
    D ( const D& x ) : i(x.i) { std::cout << "Copy constr " << std::endl; }
    void foo() {
	std::cout << "D::foo" << std::endl;
	B::foo(4);
    }
    //protected:
    //using B::foo;
};

int main ( int argc, char **argv ) {
  std::cout << "Hello world" << std::endl;
  D a ( 1 );
  a.foo();
}
