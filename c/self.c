#define p "#define p %c%s%c %cmain() {printf(p, 34, p,34, 10,10);}%c"
main() {printf(p, 34, p, 34, 10,10);}
