#ifndef __CRT0_H__
#define __CRT0_H__

/**
 * @brief File format version number
 *
 * @warning MUST REMAIN SYNCHRONIZED with scripts/build_fae.py's definition
 */
#define CRT0_MAGIC_NUMBER_AND_VERSION ((uint32_t)0xFACADE10)

/**
 * @brief Data structure that describes the memory layout
 * required by the CRT0 to execute the relocatable binary
 *
 * @warning MUST REMAIN SYNCHRONIZED with xipfs's file definition.
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

typedef void (*entryPoint_t)(crt0_ctx_t *crt0_ctx);

#endif /* __CRT0_H__ */
