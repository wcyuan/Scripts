/* $Header: /u/yuanc/testbed/C/weird_cpp/RCS/template4.C,v 1.1 2003/11/06 18:09:29 yuanc Exp yuanc $ */
/**
 * if the is the first access of D (i.e. D's point of instantiation)
 * is in the method of another class, it's an error because:
 * "B::foo is not accessible from D"
 *
 * (this is a Sun compiler bug, it works with g++)
 *
 * actually the problem is that B::foo isn't accessible from the point 
 * of instantiation.  but that shouldn't be an error.  
 *
 * possible solutions:
 * 1. instantiate D earlier (with "template class D<int>"
 * 2. declare a variable of type D earlier
 * 3. make B::foo public
 * 4. make class other a friend of B
 */

#include <iostream.h>

template<class C>
class B {
    // Solution 3. 
    //public:
    // Solution 4. 
    //friend class other;
protected:
    void foo () {}
};

template<class C>
class D : public B<C> {
protected:
    // a common purpose of the using clause would be if we have another
    // function foo with different arguments and we still want to be
    // able to access our parent's foo class.  
    // 
    // however, D::foo isn't necessary to generate the compiler bug.  
    //void foo (C i) {} 
    using B<C>::foo;
};

// Solution 1
//template class B<int>;
//template class D<int>;

// Solution 2. 
//D<int> dummy;

class other {
    void m () {
	D<int> d;
	d;
    }
public:
    void hello () {
	cout << "hello" << endl;
    }
};


int main () {
    other x;
    x.hello();
    return 0;
}
