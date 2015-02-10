/*
 * $Header: /u/yuanc/testbed/C/RCS/template2.C,v 1.1 2003/10/18 01:07:08 yuanc Exp $
 *
 * a template parameter has to be a constant.
 * but you can make it a constant pointer to something non constant,
 * including a function.  
 */
#include <iostream.h>

template <class OBJECT_TYPE, OBJECT_TYPE (*PTR)() >
class Foo {
public:
    OBJECT_TYPE run () {
	return PTR();
    }
};

int j(bool set = 0, int val = 6) {
    static int ret = val;

    if (set) {
	ret = val;
    }
    
    return ret;
}

int main () {

    Foo<int, &j> f;

    cout << j() << " "
	 << f.run() << " " 
	 << endl;

    j(false, 4);
    
    cout << j() << " "
	 << f.run() << " " 
	 << endl;

    j(true, 40);
    
    cout << j() << " "
	 << f.run() << " " 
	 << endl;

    // sample output:
    return 0;
}
