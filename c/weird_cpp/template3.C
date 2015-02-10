/*
 * $Header: /u/yuanc/testbed/C/RCS/template3.C,v 1.1 2003/10/18 01:07:25 yuanc Exp $
 *
 * a template parameter has to be a constant.
 * but you can make it a constant pointer to something non constant,
 * including a function.  
 */
#include "ios"
//#include "strstream"
#include <iostream.h>

template <class OBJECT_TYPE, class RETURN_TYPE>
class Foo {
public:
    Foo(OBJECT_TYPE obj)        { _obj =  obj; }
    OBJECT_TYPE obj  () const   { return _obj; }
    RETURN_TYPE obj2 () const   { return _obj; }
private:
    OBJECT_TYPE _obj;
};

typedef const int const_int;

class Bar {
public:
    Bar(int &obj)              { _obj = &obj; }
          int *obj  () const   { return _obj; }
    const int *obj2 () const   { return _obj; }
private:
    int *_obj;
};


int main () {

    int five = 5;
    Foo<int*, const int*> f(&five);
    //Bar f(five);

    int  *i = f.obj();
    int *ci = f.obj2();

    std::cout << "before" << std::endl;
    std::cout << "i:  " << *i  << std::endl;
    std::cout << "ci: " << *ci << std::endl;

    *i = 6;
    *ci = 6;
    
    std::cout << "after" << std::endl;
    std::cout << "i:  " << *i  << std::endl;
    std::cout << "ci: " << *ci << std::endl;

    return 0;
}
