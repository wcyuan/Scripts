#define STRINGIFY(x) #x
#define PRINT_TYPE_SIZE(type) printf(STRINGIFY(type: %u\n), sizeof(type))

#define VARNAME(x) var_ ## x
#define PRINT_MAX_TYPE(type) \
    type VARNAME(type) = -1; \
    printf(STRINGIFY(type\tsize: %d max: %u\n), sizeof(type), VARNAME(type));

int main (int argc, char **argv) {
    PRINT_TYPE_SIZE(int);
    PRINT_TYPE_SIZE(char);
    PRINT_TYPE_SIZE(long);
    PRINT_TYPE_SIZE(float);
    PRINT_TYPE_SIZE(double);
    PRINT_TYPE_SIZE(long double);

    PRINT_MAX_TYPE(int);
    PRINT_MAX_TYPE(char);
    PRINT_MAX_TYPE(long);

    return EXIT_SUCCESS;
}
