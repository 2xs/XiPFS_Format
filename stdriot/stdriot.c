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
 */
typedef enum xipfs_syscall_e {
    XIPFS_SYSCALL_EXIT,
    XIPFS_SYSCALL_MAX
} xipfs_syscall_t;

typedef int (*xipfs_syscall_exit_t)(int status);

/**
 * @internal
 *
 * @def SHELL_DEFAULT_BUFSIZE
 *
 * @brief Default shell buffer size (maximum line length shell
 * can handle)
 *
 * @see sys/include/shell.h
 */
#define SHELL_DEFAULT_BUFSIZE 128

/**
 * @internal
 *
 * @def XIPFS_FREE_RAM_SIZE
 *
 * @brief Amount of free RAM available for the relocatable
 * binary to use
 *
 * @see sys/fs/xipfs/file.c
 */
#define XIPFS_FREE_RAM_SIZE (4096)

/**
 * @internal
 *
 * @def EXEC_STACKSIZE_DEFAULT
 *
 * @brief The default execution stack size of the binary
 *
 * @see sys/fs/xipfs/file.c
 */
#define EXEC_STACKSIZE_DEFAULT 1024

/**
 * @internal
 *
 * @def EXEC_ARGC_MAX
 *
 * @brief The maximum number of arguments to pass to the binary
 *
 * @see sys/fs/xipfs/include/file.h
 */
#define EXEC_ARGC_MAX (SHELL_DEFAULT_BUFSIZE / 2)

/**
 * @internal
 *
 * @def PANIC
 *
 * @brief This macro handles fatal errors
 */
#define PANIC() for (;;);

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
} crt0_ctx_t;

/**
 * @internal
 *
 * @brief Data structure that describes the execution context of
 * a relocatable binary
 *
 * @warning MUST REMAIN SYNCHRONIZED with xipfs's file.c.
 */
typedef struct exec_ctx_s {
    /**
     * Data structure required by the CRT0 to execute the
     * relocatable binary
     */
    crt0_ctx_t crt0_ctx;
    /**
     * Reserved memory space in RAM for the stack to be used by
     * the relocatable binary
     */
    char stkbot[EXEC_STACKSIZE_DEFAULT-4];
    /**
     * Last word of the stack indicating the top of the stack
     */
    char stktop[4];
    /**
     * Number of arguments passed to the relocatable binary
     */
    int argc;
    /**
     * Arguments passed to the relocatable binary
     */
    char *argv[EXEC_ARGC_MAX];

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
     * Reserved memory space in RAM for the free RAM to be used
     * by the relocatable binary
     */
    char ram_start[XIPFS_FREE_RAM_SIZE-1];
    /**
     * Last byte of the free RAM
     */
    char ram_end;
} exec_ctx_t;

/*
 * Internal types
 */

/*
 * Global variable
 */

/**
 * @internal
 *
 * @brief A pointer to the xipfs syscall table
 *
 * @see sys/fs/xipfs/file.c
 */
static const void **xipfs_syscall_table;

/**
 * @internal
 *
 * @brief A pointer to the user syscall table
 *
 * @see sys/fs/xipfs/file.c
 */
static const void **user_syscall_table;

/**
 * @brief Wrapper that branches to the xipfs_exit(3) function
 *
 * @param status The exit status of the program
 *
 * @see sys/fs/xipfs/file.c
 */
static void exit(int status)
{
    xipfs_syscall_exit_t func;

    /* No need to save the R10 register, which holds the address
     * of the program's relocated GOT, since this register is
     * callee-saved according to the ARM Architecture Procedure
     * Call Standard, section 5.1.1 */
    func = xipfs_syscall_table[XIPFS_SYSCALL_EXIT];
    (*func)(status);
}

/**
 * @brief Wrapper that branches to the RIOT's printf(3) function
 *
 * @param format The formatted string to print
 */
extern int printf(const char * format, ...)
{
    xipfs_user_syscall_vprintf_t func;
    int res = 0;
    va_list ap;

    /* No need to save the R10 register, which holds the address
     * of the program's relocated GOT, since this register is
     * callee-saved according to the ARM Architecture Procedure
     * Call Standard, section 5.1.1 */
    func = user_syscall_table[XIPFS_USER_SYSCALL_PRINTF];
    va_start(ap, format);
    res = (*func)(format, ap);
    va_end(ap);

    return res;
}

extern int get_temp(void) {
    xipfs_user_syscall_get_temp_t func;
    int res;

    func = user_syscall_table[XIPFS_USER_SYSCALL_GET_TEMP];
    res  = (*func)();
    return res;
}

extern int isprint(int character) {
    xipfs_user_syscall_isprint_t func;
    int res;

    func = user_syscall_table[XIPFS_USER_SYSCALL_ISPRINT];
    res  = (*func)(character);

    return res;
}

extern long strtol(const char *str, char **endptr, int base) {
    xipfs_user_syscall_strtol_t func;
    long res;

    func = user_syscall_table[XIPFS_USER_SYSCALL_STRTOL];
    res  = (*func)(str, endptr, base);
    return res;
}

extern int get_led(int pos) {
    xipfs_user_syscall_get_led_t func;
    int res;

    func = user_syscall_table[XIPFS_USER_SYSCALL_GET_LED];
    res  = (*func)(pos);
    return res;
}

extern int set_led(int pos, int val) {
    xipfs_user_syscall_set_led_t func;
    int res;

    func = user_syscall_table[XIPFS_USER_SYSCALL_SET_LED];
    res  = (*func)(pos, val);
    return res;
}

extern ssize_t copy_file(const char *name, void *buf, size_t nbyte) {
    xipfs_user_syscall_copy_file_t func;
    ssize_t res;

    func = user_syscall_table[XIPFS_USER_SYSCALL_COPY_FILE];
    res  = (*func)(name, buf, nbyte);
    return res;
}

extern int get_file_size(const char *name, size_t *size) {
    xipfs_user_syscall_get_file_size_t func;
    int res;

    func = user_syscall_table[XIPFS_USER_SYSCALL_GET_FILE_SIZE];
    res  = (*func)(name, size);
    return res;
}

extern void *memset(void *m, int c, size_t n) {
    xipfs_user_syscall_memset_t func;
    void *res;

    func = user_syscall_table[XIPFS_USER_SYSCALL_MEMSET];
    res  = (*func)(m, c, n);
    return res;
}

/**
 * @internal
 *
 * @brief The function to which CRT0 branches after the
 * executable has been relocated
 */
int start(exec_ctx_t *exec_ctx)
{
    int status, argc;
    char **argv;

    /* initialize syscall tables pointers */
    xipfs_syscall_table = exec_ctx->xipfs_syscall_table;
    user_syscall_table  = exec_ctx->user_syscall_table;

    /* initialize the arguments passed to the program */
    argc = exec_ctx->argc;
    argv = exec_ctx->argv;

    /* branch to the main() function of the program */
    extern int main(int argc, char **argv);
    status = main(argc, argv);

    /* exit the program */
    exit(status);

    /* should never be reached */
    PANIC();
}
