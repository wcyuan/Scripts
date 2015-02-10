// $Header: /u/yuanc/testbed/C/weird_cpp/RCS/virtual_in_constructor.C,v 1.1 2006/10/25 21:29:30 yuanc Exp yuanc $
// Calling a virtual function from a contructor

#include <stdio.h> 

class A
{
 public:
    virtual void f(){ printf("A\n");};
    void g(){
	printf("In A::g\n");
	f();
    };
    A(){
	printf("In A::A about to call f\n");
	f(); 
	printf("In A::A about to call g\n");
	g();
    };


};


class B: public A
{
public:
    // implicitly calls A's constructor
    // B() : A () { ...
    B() {
	printf("In B::B about to call f\n");
	f(); 
	printf("In B::B about to call g\n");
	g();
    };
    virtual void f(){ printf("B\n");};
};


int   main (int argc, char *argv)
{
    argc; argv;
    printf("making B\n");
    A *pA=new B();
    printf("Calling g\n");
    pA->g();
    return 0;
}
