/*
 * Copyright (C) 2024 Université de Lille
 *
 * This file is subject to the terms and conditions of the GNU Lesser
 * General Public License v2.1. See the file LICENSE in the top level
 * directory for more details.
 */

/**
 * @ingroup     examples
 * @{
 *
 * @file
 * @brief       Example of a post-issuance software
 *
 * @author      Damien Amara <damien.amara@univ-lille.fr>
 *
 * @}
 */

#include <stdriot.h>

typedef int (*func_ptr_t)(void);

int func_a(void) {
    //printf("func_a has been assigned to ");
    return 23;
}

int func_b(void) {
    //printf("func_b has been assigned to ");
    return 32;
}

volatile func_ptr_t func_ptr_extern_1 = func_a;
const int cst = 3;

int main(int argc, char **argv)
{
    /*
    int i;

    printf("Hello World!\n");

    for (i = 1; i < argc; i++) {
        printf("%s\n", argv[i]);
    }
    */

    if (argc > 1) {
        func_ptr_extern_1 = func_b;
    }

    int v = func_ptr_extern_1();
    char *string = "hello world !";
    printf("@string = %p\n", string);

    printf("@&string = %p\n", &string);
    printf("@&main = %p\n", &main);

    printf("&cst = %p\n", &cst);
    printf("cst = %d\n", cst);

    return v;
}
