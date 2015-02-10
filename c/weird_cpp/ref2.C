#include <iostream.h>
#include <string>

class PAIR {
public:
    PAIR() : _a(""), _b("") { }
    // should precede this constructor with "explicit"
    // see below
    PAIR(const char* a, const char* b = "goodbye") : _a(a), _b(b) { }
    std::string _a;
    std::string _b;
};

int main(int argc, char** argv)
{
    // initializing a const reference means first
    // implicit type conversion to a PAIR
    // the resulting value is placed in a temporary variable
    // of type PAIR.  and that variable is passed to
    // the initializer of the reference.  
    //
    // however, here the comma operator takes effect
    // so hello is discarded, world is passed as the first 
    // argument and the second argument defaults to 
    // goodbye
    const PAIR& pair1("hello", "world");

    // the above is the same as this:
    const PAIR& pair2 = ("hello", "world");
    
    // and the comma operator is used, 
    // so the above is the same as this:
    const PAIR& pair3 = "world";

    // the difference between pair1 and pair2 and pair3
    // is that if the PAIR constructor were declared explicit
    // then the compiler would complain about pair2 and pair3
    // but not about pair1.  

    // on the other hand, this works
    const PAIR& pair4 = PAIR("hello", "world");

    // as does this
    PAIR temp = PAIR("hello", "world");
    const PAIR& pair5 = temp;

    // prints "world goodbye"
    cout << pair1._a << " " << pair1._b << endl;
    cout << pair2._a << " " << pair2._b << endl;
    cout << pair3._a << " " << pair2._b << endl;
    // prints "hello world"
    cout << pair4._a << " " << pair4._b << endl;
    cout << pair5._a << " " << pair4._b << endl;

    return 0;
}
