#ifndef __CRT0_H__
#define __CRT0_H__

/**
 * @brief File format version number
 *
 * @warning MUST REMAIN SYNCHRONIZED with scripts/build_fae.py's definition.
 * @warning MUST REMAIN SYNCHRONIZED with xipfs's driver definition.
 */
#define CRT0_MAGIC_NUMBER_AND_VERSION ((uint32_t)0xFACADE11)

/**
 * @brief XIPFS Max Command Line arguments count.
 * @warning MUST REMAIN SYNCHRONIZED with xipfs's file definition.
 * @warning MUST REMAIN SYNCHRONIZED with stdriot's definition.
 */
#define XIPFS_EXEC_ARGC_MAX (64)

/**
 * @brief Data structure that describes the memory layout
 * required by the CRT0 to execute the relocatable binary
 *
 * @warning MUST REMAIN SYNCHRONIZED with xipfs's file definition.
 * @warning MUST REMAIN SYNCHRONIZED with stdriot's definition.
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

typedef void (*entryPoint_t)(crt0_ctx_t *crt0_ctx);

#endif /* __CRT0_H__ */
