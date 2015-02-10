#include <iostream.h>

int main () {
    int i = 3;
    int * ip = &i;
    char * cp = (char *)&i;

    if (ip == (int *)cp) {
	cout << "Equal!" << endl;
    }
    if ((char*)ip == cp) {
	cout << "Equal!" << endl;
    }

}

