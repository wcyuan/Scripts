#define MULT_BY_8(x) (MULT_BY_7(x)+(x))
#define MULT_BY_7(x) (MULT_BY_6(x)+(x))
#define MULT_BY_6(x) (MULT_BY_5(x)+(x))
#define MULT_BY_5(x) (MULT_BY_4(x)+(x))
#define MULT_BY_4(x) (MULT_BY_3(x)+(x))
#define MULT_BY_3(x) (MULT_BY_2(x)+(x))
#define MULT_BY_2(x) ((x)+(x))

/* concatenates "AB" and another letter to the end of the argument */
#define ADD_ABX(x) ADD_BX(x ## A)
/* concatenates "B" and another letter to the end of the argument */
/* we start out by having the other letter be "C" */
#define ADD_BX(x) ADD_C(x ## B)
/* concatenates "C" to the end of the argument and makes it a string */
#define ADD_C(x) #x "C"

int main() {

    printf("%d\n", MULT_BY_8(4));
    printf("%s\n", ADD_ABX(A));

/* concatenates "D" to the end of the argument and makes it a string */
#define ADD_D(x) #x "D"
/* from now on, ADD_BX should concatenate BD instead of BC to the end of the strings.  */
#undef ADD_BX
#define ADD_BX(x) ADD_D(x ## B)

    printf("%s\n", ADD_ABX(A));

    return EXIT_SUCCESS;
}

