int square (int c) {
    return c * c;
}

int main (int argc, char ** argv) {
    int (*func_pointer)(int c);
    func_pointer = square;
    printf("%d\n", (*func_pointer)(argc));
    return 0;
}
