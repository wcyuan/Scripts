/* $Header: /u/yuanc/testbed/C/weird_cpp/RCS/constructor.C,v 1.1 2006/05/09 22:47:58 yuanc Exp $ */
#include<iostream>

class B {
public:
    B () {}
    B ( int j ) { std::cout << "B:Constr with " << j << std::endl; }
    B ( const B& b ) {
	std::cout << "B::copy constr" << std::endl;
    }
};

class C : public B {
public:
  int i;
  C ( int j ) : i(j) { std::cout << "Constr with " << j << std::endl; }
  C ( const C& x ) : i(x.i) { std::cout << "Copy constr " << std::endl; }
};

int main ( int argc, char **argv ) {
  std::cout << "Hello world" << std::endl;
  C a ( 1 );
  C b = a;
  B c = C ( 2 );
}
