/* $Header: /u/yuanc/testbed/C/RCS/constructor2.C,v 1.1 2003/10/18 01:08:12 yuanc Exp $ */
#include<iostream>

class C {
public:
    int i;
    ~C () {
	std::cout << "destructed " << i << std::endl;
    }
    explicit C ( int j ) : i(j) { std::cout << "Constr with " << j << std::endl; }
    explicit C ( const C& x ) : i(x.i) { std::cout << "Copy constr " << std::endl; }
    const C& operator= ( const C& x ) {
	i = x.i;
	std::cout << "assigned " << i << std::endl;
	return *this;
    }
    C& foo() {
	std::cout << "foo " << i << std::endl;
	return *this;
    }
};

int main ( int argc, char **argv ) {
  std::cout << "Hello world" << std::endl;
  C a ( 1 );
  C b(a);
  C c = C( 2 );

  std::cout << "Hello world" << std::endl; 
}
