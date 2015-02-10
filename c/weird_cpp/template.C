/*
 * $Header: /u/yuanc/testbed/C/RCS/template.C,v 1.1 2003/10/18 01:06:50 yuanc Exp $
 *
 * you can use the address of a non-const object as a non-type
 * template parameter, but only if it's of namespace scope.  otherwise
 * it fails silently.  
 */
#include <iostream.h>

template <class OBJECT_TYPE, OBJECT_TYPE * PTR>
class Foo {
public:
    OBJECT_TYPE * bar () {
	return PTR;
    }
};

int j = 6;

int main () {
    int i = 5;
    int * a = &i;
    Foo<int, &i> f;
    Foo<int, a> g;
    Foo<int, &j> h;

    cout << &i << " "
	 << f.bar() << " " 
	 << g.bar() << " "
	 << &j << " "
	 << h.bar() << " "
	 << j << " "
	 << *(h.bar()) << " "
	 << endl;

    // sample output:
    // yuanc@casqa1:~/testbed/C 1044> ./template
    // ffbef488 ffbef418 22028 22018 22018 6 6 
    // only works for the variable of namespace scope

    return 0;
}
