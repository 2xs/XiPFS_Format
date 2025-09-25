/*******************************************************************************/
/*  © Université de Lille, The Pip Development Team (2015-2024)                */
/*                                                                             */
/*  This software is a computer program whose purpose is to run a minimal,     */
/*  hypervisor relying on proven properties such as memory isolation.          */
/*                                                                             */
/*  This software is governed by the CeCILL license under French law and       */
/*  abiding by the rules of distribution of free software.  You can  use,      */
/*  modify and/ or redistribute the software under the terms of the CeCILL     */
/*  license as circulated by CEA, CNRS and INRIA at the following URL          */
/*  "http://www.cecill.info".                                                  */
/*                                                                             */
/*  As a counterpart to the access to the source code and  rights to copy,     */
/*  modify and redistribute granted by the license, users are provided only    */
/*  with a limited warranty  and the software's author,  the holder of the     */
/*  economic rights,  and the successive licensors  have only  limited         */
/*  liability.                                                                 */
/*                                                                             */
/*  In this respect, the user's attention is drawn to the risks associated     */
/*  with loading,  using,  modifying and/or developing or reproducing the      */
/*  software by the user in light of its specific status of free software,     */
/*  that may mean  that it is complicated to manipulate,  and  that  also      */
/*  therefore means  that it is reserved for developers  and  experienced      */
/*  professionals having in-depth computer knowledge. Users are therefore      */
/*  encouraged to load and test the software's suitability as regards their    */
/*  requirements in conditions enabling the security of their systems and/or   */
/*  data to be ensured and,  more generally, to use and operate it in the      */
/*  same conditions as regards security.                                       */
/*                                                                             */
/*  The fact that you are presently reading this means that you have had       */
/*  knowledge of the CeCILL license and that you accept its terms.             */
/*******************************************************************************/

/**
 * @file stdriot.c
 *
 * This file is the counterpart of xipfs definitions, such
 * as exec_ctx_t or syscall_index_t.
 *
 * @warning THIS FILE MUST REMAIN SYNCHRONIZED with xipfs, otherwise crashes and UB are to
 * be expected.
 */

#include <stdarg.h>

#include "stdriot.h"

/**
 * @warning The order of the members in the enumeration must
 * remain synchronized with the order of the members of the same
 * enumeration declared in caller site (xipfs.h's one).
 *
 * @brief An enumeration describing the index of functions.
 *
 * @see xipfs/include/xipfs.h
 */
typedef enum xipfs_user_syscall_e {
    XIPFS_USER_SYSCALL_PRINTF,
    XIPFS_USER_SYSCALL_GET_TEMP,
    XIPFS_USER_SYSCALL_ISPRINT,
    XIPFS_USER_SYSCALL_STRTOL,
    XIPFS_USER_SYSCALL_GET_LED,
    XIPFS_USER_SYSCALL_SET_LED,
    XIPFS_USER_SYSCALL_COPY_FILE,
    XIPFS_USER_SYSCALL_GET_FILE_SIZE,
    XIPFS_USER_SYSCALL_MEMSET,
    XIPFS_USER_SYSCALL_MAX
} xipfs_user_syscall_t;

typedef int (*xipfs_user_syscall_vprintf_t)(const char *format, va_list ap);
typedef int (*xipfs_user_syscall_get_temp_t)(void);
typedef int (*xipfs_user_syscall_isprint_t)(int character);
typedef long (*xipfs_user_syscall_strtol_t)(
    const char *str, char **endptr, int base);
typedef int (*xipfs_user_syscall_get_led_t)(int pos);
typedef int (*xipfs_user_syscall_set_led_t)(int pos, int val);
typedef ssize_t (*xipfs_user_syscall_copy_file_t)(
    const char *name, void *buf, size_t nbyte);
typedef int (*xipfs_user_syscall_get_file_size_t)(
    const char *name, size_t *size);
typedef void *(*xipfs_user_syscall_memset_t)(void *m, int c, size_t n);

/**
 * @brief An enumeration describing the index of xipfs functions.
 *
 * @warning MUST REMAIN SYNCHRONIZED with xipfs file.c's one.
 *
 * @see xipfs/src/file.c
 */
typedef enum xipfs_syscall_e {
    XIPFS_SYSCALL_FIRST = XIPFS_USER_SYSCALL_MAX,
    XIPFS_SYSCALL_EXIT  = XIPFS_SYSCALL_FIRST,
    XIPFS_SYSCALL_MAX
} xipfs_syscall_t;

typedef int (*xipfs_syscall_exit_t)(int status);

/**
 * @internal
 *
 * @def XIPFS_EXEC_ARGC_MAX
 *
 * @brief The maximum number of arguments to pass to the binary
 *
 * @warning Must be synchronized with xipfs' one
 *
 * @see xipfs/include/xipfs.h
 */
#define XIPFS_EXEC_ARGC_MAX 64

/**
 * @internal
 *
 * @def XIPFS_SYSCALL_SVC_NUMBER
 *
 * The Supervisor Virtual Call number through which SVCs are performed.
 *
 * @warning Must be synchronized with xipfs' one
 *
 * @see xipfs/src/file.c
 */
#define XIPFS_SYSCALL_SVC_NUMBER 3

/**
 * @internal
 *
 * @def PANIC
 *
 * @brief This macro handles fatal errors
 */
#define PANIC() for (;;);

/**
 * @internal
 *
 * @def STR_HELPER
 *
 * @brief Used for preprocessing in asm statements
 */
#define STR_HELPER(x) #x

/**
 * @internal
 *
 * @def STR
 *
 * @brief Used for preprocessing in asm statements
 */
#define STR(x) STR_HELPER(x)

/*
 * Internal structures
 */

/**
 * @internal
 *
 * @brief Data structure that describes the memory layout
 * required by the CRT0 to execute the relocatable binary
 *
 * @see sys/fs/xipfs/file.c
 * @warning MUST REMAIN SYNCHRONIZED with xipfs's file.c.
 * @warning MUST REMAIN SYNCHRONIZED with crt0's definition.
 */
typedef struct crt0_ctx_s {
    /**
     * Start address of the binary in the NVM
     */
    void *bin_base;
    /**
     * Start address of the available free RAM
     */
    void *ram_start;
    /**
     * End address of the available free RAM
     */
    void *ram_end;
    /**
     * Start address of the free NVM
     */
    void *nvm_start;
    /**
     * End address of the free NVM
     */
    void *nvm_end;
    /**
     * Start address of the file in NVM,
     * which is the text segment of the xipfs file.
     */
    void *file_base;
    /**
     * true if the context is executed in user mode with configured MPU regions,
     * false otherwise
     */
    unsigned char is_safe_call;
    /**
     * Number of arguments passed to the relocatable binary
     */
    int argc;
    /**
     * Arguments passed to the relocatable binary
     */
    char *argv[XIPFS_EXEC_ARGC_MAX];
    /**
     * Table of function pointers for functions
     * used by xipfs_format's CRT0 and/or stdriot.
     * These functions are not meant to be shared with
     * end users.
     */
    const void **xipfs_syscall_table;
    /**
     * Table of function pointers for the RIOT functions
     * used by the relocatable binary
     */
    const void **user_syscall_table;
    /**
     * When using xipfs_file_safe_exec, syscalls results will be written here.
     */
    int syscall_result;
} crt0_ctx_t;

/*
 * Internal types
 */

/*
 * Global variable
 */
/**
 * @internal
 *
 * @brief true if the call is a safe one, false otherwise
 *
 * @see xipfs/src/file.c
 */
static unsigned char is_safe_call;

/**
 * @internal
 *
 * @brief A pointer to the xipfs syscall table
 *
 * @see xipfs/src/file.c
 */
static const void **xipfs_syscall_table;

/**
 * @internal
 *
 * @brief A pointer to the user syscall table
 *
 * @see xipfs/src/file.c
 */
static const void **user_syscall_table;

static int *syscall_result_ptr;

/**
 * @brief Wrapper that branches to the xipfs_exit(3) function
 *
 * @param status The exit status of the program
 *
 * @see xipfs/src/file.c
 */
static void exit(int status)
{
    /* No need to save the R10 register, which holds the address
     * of the program's relocated GOT, since this register is
     * callee-saved according to the ARM Architecture Procedure
     * Call Standard, section 5.1.1 */
    if (is_safe_call) {
        asm volatile(
            "mov r0, %0                            \n"
            "mov r1, %1                            \n"
            "svc #" STR(XIPFS_SYSCALL_SVC_NUMBER) "\n"
            ::"g"(XIPFS_SYSCALL_EXIT), "g"(status)
            : "r0", "r1"
        );
    } else {
        xipfs_syscall_exit_t func;

        func = xipfs_syscall_table[XIPFS_SYSCALL_EXIT - XIPFS_SYSCALL_FIRST];
        (*func)(status);
    }
}

/**
 * @brief Wrapper that branches to the RIOT's printf(3) function
 *
 * @param format The formatted string to print
 */
extern int printf(const char * format, ...)
{
    int res;
    va_list ap;

    /* No need to save the R10 register, which holds the address
     * of the program's relocated GOT, since this register is
     * callee-saved according to the ARM Architecture Procedure
     * Call Standard, section 5.1.1 */
    va_start(ap, format);

    if (is_safe_call){
        asm volatile(
            "mov r0, %0                            \n"
            "mov r1, %1                            \n"
            "mov r2, %2                            \n"
            "svc #" STR(XIPFS_SYSCALL_SVC_NUMBER) "\n"
            :
            :"r"(XIPFS_USER_SYSCALL_PRINTF), "r"(format), "r"(&ap)
            : "r0", "r1", "r2"
        );
        res = *syscall_result_ptr;
    } else {
        xipfs_user_syscall_vprintf_t func;

        func = user_syscall_table[XIPFS_USER_SYSCALL_PRINTF];
        res = (*func)(format, ap);
    }

    va_end(ap);

    return res;
}

extern int get_temp(void) {
    int res;

    if (is_safe_call) {
        asm volatile (
            "mov r0, %0                            \n"
            "svc #" STR(XIPFS_SYSCALL_SVC_NUMBER) "\n"
            :
            : "r"(XIPFS_USER_SYSCALL_GET_TEMP)
            : "r0"
        );
        res = *syscall_result_ptr;
    } else {
        xipfs_user_syscall_get_temp_t func;

        func = user_syscall_table[XIPFS_USER_SYSCALL_GET_TEMP];
        res  = (*func)();
    }
    return res;
}

extern int isprint(int character) {
    int res;

    if (is_safe_call) {
        asm volatile(
            "mov r0, %0                            \n"
            "mov r1, %1                            \n"
            "svc #" STR(XIPFS_SYSCALL_SVC_NUMBER) "\n"
            :
            : "r"(XIPFS_USER_SYSCALL_ISPRINT), "r"(character)
            : "r0", "r1"
        );
        res = *syscall_result_ptr;
    } else {
        xipfs_user_syscall_isprint_t func;

        func = user_syscall_table[XIPFS_USER_SYSCALL_ISPRINT];
        res  = (*func)(character);
    }

    return res;
}

extern long strtol(const char *str, char **endptr, int base) {

    long res;

    if (is_safe_call) {
        asm volatile (
            "mov r0, %0                            \n"
            "mov r1, %1                            \n"
            "mov r2, %2                            \n"
            "mov r3, %3                            \n"
            "svc #" STR(XIPFS_SYSCALL_SVC_NUMBER) "\n"
            :
            : "r"(XIPFS_USER_SYSCALL_STRTOL), "r"(str), "r"(endptr), "r"(base)
            : "r0", "r1", "r2", "r3"
        );

        res = *syscall_result_ptr;
    } else {
        xipfs_user_syscall_strtol_t func;

        func = user_syscall_table[XIPFS_USER_SYSCALL_STRTOL];
        res  = (*func)(str, endptr, base);
    }

    return res;
}

extern int get_led(int pos) {

    int res;

    if (is_safe_call) {
        asm volatile(
            "mov r0, %0                            \n"
            "mov r1, %1                            \n"
            "svc #" STR(XIPFS_SYSCALL_SVC_NUMBER) "\n"
            :
            : "r"(XIPFS_USER_SYSCALL_GET_LED), "r"(pos)
            : "r0", "r1"
        );
        res = *syscall_result_ptr;
    } else {
        xipfs_user_syscall_get_led_t func;

        func = user_syscall_table[XIPFS_USER_SYSCALL_GET_LED];
        res  = (*func)(pos);
    }
    return res;
}

extern int set_led(int pos, int val) {
    int res;

    if (is_safe_call) {
        asm volatile (
            "mov r0, %0                            \n"
            "mov r1, %1                            \n"
            "mov r2, %2                            \n"
            "svc #" STR(XIPFS_SYSCALL_SVC_NUMBER) "\n"
            :
            : "r"(XIPFS_USER_SYSCALL_SET_LED), "r"(pos), "r"(val)
            : "r0", "r1", "r2"
        );
        res = *syscall_result_ptr;
    } else {
        xipfs_user_syscall_set_led_t func;

        func = user_syscall_table[XIPFS_USER_SYSCALL_SET_LED];
        res  = (*func)(pos, val);
    }

    return res;
}

extern ssize_t copy_file(const char *name, void *buf, size_t nbyte) {
    ssize_t res;

    if (is_safe_call) {
        asm volatile(
            "mov r0, %0                            \n"
            "mov r1, %1                            \n"
            "mov r2, %2                            \n"
            "mov r3, %3                            \n"
            "svc #" STR(XIPFS_SYSCALL_SVC_NUMBER) "\n"
            :
            : "r"(XIPFS_USER_SYSCALL_COPY_FILE), "r"(name), "r"(buf), "r"(nbyte)
            : "r0", "r1", "r2", "r3"
        );
        res = *syscall_result_ptr;
    } else {
        xipfs_user_syscall_copy_file_t func;

        func = user_syscall_table[XIPFS_USER_SYSCALL_COPY_FILE];
        res  = (*func)(name, buf, nbyte);
    }

    return res;
}

extern int get_file_size(const char *name, size_t *size) {
    int res;

    if (is_safe_call) {
        asm volatile(
            "mov r0, %0                            \n"
            "mov r1, %1                            \n"
            "mov r2, %2                            \n"
            "svc #" STR(XIPFS_SYSCALL_SVC_NUMBER) "\n"
            :
            : "r"(XIPFS_USER_SYSCALL_GET_FILE_SIZE), "r"(name), "r"(size)
            : "r0", "r1", "r2"
        );
        res = *syscall_result_ptr;
    } else {
        xipfs_user_syscall_get_file_size_t func;

        func = user_syscall_table[XIPFS_USER_SYSCALL_GET_FILE_SIZE];
        res  = (*func)(name, size);
    }

    return res;
}

extern void *memset(void *m, int c, size_t n) {
    xipfs_user_syscall_memset_t func;
    void *res;
    if (is_safe_call) {
        asm volatile(
            "mov r0, %0                            \n"
            "mov r1, %1                            \n"
            "mov r2, %2                            \n"
            "mov r3, %3                            \n"
            "svc #" STR(XIPFS_SYSCALL_SVC_NUMBER) "\n"
            :
            : "r"(XIPFS_USER_SYSCALL_MEMSET), "r"(m), "r"(c), "r"(n)
            : "r0", "r1", "r2", "r3"
        );
        res = (void *)(uintptr_t)(*syscall_result_ptr);
    } else {
        func = user_syscall_table[XIPFS_USER_SYSCALL_MEMSET];
        res  = (*func)(m, c, n);
    }
    return res;
}

/**
 * @internal
 *
 * @brief The function to which CRT0 branches after the
 * executable has been relocated
 */
int start(crt0_ctx_t *crt0_ctx)
{
    int status, argc;
    char **argv;

    /* Are we executing a safe exec call ? */
    is_safe_call = crt0_ctx->is_safe_call;

    /* initialize syscall tables pointers */
    if (is_safe_call) {
        /* We'll be relying onto SVC to perform the required functions */
        xipfs_syscall_table = NULL;
        user_syscall_table  = NULL;
        syscall_result_ptr  = &(crt0_ctx->syscall_result);
    } else {
        /* We'll be relying onto syscall tables to perform the required functions */
        xipfs_syscall_table = crt0_ctx->xipfs_syscall_table;
        user_syscall_table  = crt0_ctx->user_syscall_table;
        syscall_result_ptr  = NULL;
    }

    /* initialize the arguments passed to the program */
    argc = crt0_ctx->argc;
    argv = crt0_ctx->argv;

    /* branch to the main() function of the program */
    extern int main(int argc, char **argv);
    status = main(argc, argv);

    /* exit the program */
    exit(status);

    /* should never be reached */
    PANIC();
}
