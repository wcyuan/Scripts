/* $Header: /u/yuanc/testbed/C/RCS/constructor3.C,v 1.1 2003/10/18 01:08:23 yuanc Exp $ */
#include<iostream>

class B {
public:
    B () {
	std::cout << "B:default constructor" << std::endl; 
    }
    B ( int j ) { std::cout << "B:Constr with " << j << std::endl; }
    B ( const B& b ) {
	std::cout << "B::copy constr" << std::endl;
    }
    ~B () {
	std::cout << "B:DTOR" << std::endl; 
    }
};

enum E {
    ONE = 1,
    TWO, 
    THREE
};

class D : public B {
public:
  int i;

    D ( bool j ) : B(j) { 
	std::cout << "D:bool Constr with " << j << std::endl; 
	// creates a new object, which can't be accessed
	D((int)j);
    }

    D ( E j ) { 
	std::cout << "D: enum Constr with " << j << std::endl; 
	// creates a new object, which can't be accessed
	// no way to call the other constructor.  
	D((int)j);
    }

    D ( int j ) : i(j+1) { 
	std::cout << "Constr with " << j << " " << i << std::endl; 
    }

    D ( const D& x ) : i(x.i) { 
	std::cout << "Copy constr " << std::endl; 
    }

    void print () {
	std::cout << "D:print: " << i << std::endl; 
    }

    ~D () {
	std::cout << "D:DTOR: " << i << std::endl; 
    }
};

int main ( int argc, char **argv ) {
  std::cout << "Hello world" << std::endl;
  D a ( TWO );
  a.print();
  std::cout << std::endl;
  D b ( false );
  b.print();
  std::cout << std::endl;
  D c ( 4 );
  c.print();
}
