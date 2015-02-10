#include <iostream.h>
int main (int argc, char** argv) {
    int y = 4;
    int &x = y;
    cout << x << " " <<  y << endl;
    y = 5;
    cout << x << " " <<  y << endl;

    int i = 8, *j, &k = i;
    j=&i;
    cout << k << endl;
    return 1;
}
