/* $Header: /u/yuanc/testbed/C/RCS/constructor4.C,v 1.1 2003/10/18 01:08:34 yuanc Exp $ */
#include<iostream>

enum e {
    DO_NOT_ACQUIRE = 123
};

class B {
public:
    B (const e x) {
    }
};

int main ( int argc, char **argv ) {
  std::cout << "Hello world" << std::endl;
  B b(DO_NOT_ACQUIRE);
}
