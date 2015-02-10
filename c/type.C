#include <iostream.h>

int main () 
{

    cout << "       char: " << sizeof(char)        << endl;
    cout << "      short: " << sizeof(short)       << endl;
    cout << "        int: " << sizeof(int)         << endl;
    cout << "    pointer: " << sizeof(int*)        << endl;
    cout << "       long: " << sizeof(long)        << endl;
    cout << "      float: " << sizeof(float)       << endl;
    cout << "     double: " << sizeof(double)      << endl;
    cout << "long double: " << sizeof(long double) << endl;


    long lo = -100;
    int si = -100;
    unsigned int ui = 1;

    // result lo + ui is unsigned
    cout << "(long) -100 + (unsigned int) 1 = " << lo + ui << endl;
    cout << "sizeof(long + unsigned int): " << sizeof(lo+ui) << endl;

    // result si + ui is unsigned
    cout << "(int) -100 + (unsigned int) 1 = " << si + ui << endl;
    cout << "sizeof(int + unsigned int): " << sizeof(si+ui) << endl;

    return 0;
}
