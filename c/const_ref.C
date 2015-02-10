/* $Header: /u/yuanc/testbed/C/RCS/const_ref.C,v 1.1 2003/10/18 01:05:26 yuanc Exp $ */

#include <iostream.h>

void foo (const int & x) {
    cout << "foo called with " << x << endl;
}

void bar (const char * const &x) {
    cout << "bar called with " << x << endl;
}

template <class C>
class A {
public:
    void baz (C x) {
	cout << "baz called with " << x << endl;
    }
};

template <class C>
class CA {
public:

    //
    // "const C x"
    //
    // Note that, for example, if C is a char *
    // this translates into char * const x, not const char * x
    // because the * binds to the char more closely than the const
    // does.  
    //
    void baz (const C x) {
	cout << "baz called with " << x << endl;
    }
};


int main(int argc, char** argv)
{
    foo(4);

    int i = 5;
    foo(i);

    const int ci = 6;
    foo(ci);

    A<const int &>().baz(i);

    bar("hello");
    A<char * const>().baz("hello");

    char * there = "there";
    bar(there);
    A<char * const>().baz(there);

    const char * world = "world";
    bar(world);
    A<const char*>().baz(world);
    CA<char*>().baz(world);

    char * const something = "something";
    bar(something);
    A<char * const>().baz(something);

    const char *const other = "else";
    bar(other);
    A<const char * const>().baz(other);
    CA<char * const>().baz(other);


    return 0;
}
