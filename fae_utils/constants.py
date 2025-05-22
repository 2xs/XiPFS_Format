class FAEConstants:

    SUFFIX = ".fae"


    BINUTILS_PREFIX = 'arm-none-eabi-'

    OBJCOPY = BINUTILS_PREFIX + 'objcopy'
    OBJDUMP = BINUTILS_PREFIX + 'objdump'

    ENDIANNESS = 'little'

    OBJCOPY_ARGS_BASE = f'{OBJCOPY} --input-target=elf32-littlearm --output-target=binary'
    OBJDUMP_ARGS_BASE = f'{OBJDUMP} -b binary -marm --endian={ENDIANNESS} -Mforce-thumb -D '


    MAGIC_NUMBER             = int(0xFACADE00)
    VERSION                  = int(0x10)
    MAGIC_NUMBER_AND_VERSION = MAGIC_NUMBER | VERSION

    CRT0_DEFAULT_PATH = "./crt0/"

    EXPORTED_SYMBOL_START        = 'start'
    EXPORTED_SYMBOL_ENTRYPOINT   = EXPORTED_SYMBOL_START
    EXPORTED_SYMBOL_ROM_RAM_SIZE = '__rom_ram_size'
    EXPORTED_SYMBOL_DATA_SIZE    = EXPORTED_SYMBOL_ROM_RAM_SIZE
    EXPORTED_SYMBOL_ROM_SIZE     = '__rom_size'
    EXPORTED_SYMBOL_TEXT_SIZE    = EXPORTED_SYMBOL_ROM_SIZE
    EXPORTED_SYMBOL_GOT_SIZE     = '__got_size'
    EXPORTED_SYMBOL_RAM_SIZE     = '__ram_size'
    EXPORTED_SYMBOL_BSS_SIZE     = EXPORTED_SYMBOL_RAM_SIZE

    EXPORTED_SYMBOLS = [
        EXPORTED_SYMBOL_START,
        EXPORTED_SYMBOL_ROM_RAM_SIZE,
        EXPORTED_SYMBOL_ROM_SIZE,
        EXPORTED_SYMBOL_GOT_SIZE,
        EXPORTED_SYMBOL_RAM_SIZE
    ]


    EXPORTED_RELOCATION_TABLES = [ '.rel.rom.ram' ]
    PARTITION_NAME = 'partition.fae'

    MAKE = 'make'
    RM   = 'rm'

    GDBINIT_FILENAME = 'gdbinit'


    BINARY_SIZE_BYTESIZE                = 4
    RELOCATION_ENTRIES_COUNT_BYTESIZE   = 4
    CRT0_SIZE_BYTESIZE                  = 4
    ENTRY_POINT_BYTESIZE                = 4
    ROM_RAM_SIZE_BYTESIZE               = 4
    ROM_SIZE_BYTESIZE                   = 4
    GOT_SIZE_BYTESIZE                   = 4
    RAM_SIZE_BYTESIZE                   = 4
    MAGIC_NUMBER_AND_VERSION_BYTESIZE   = 4

    FOOTER_BYTESIZE =          \
        RAM_SIZE_BYTESIZE     +\
        GOT_SIZE_BYTESIZE     +\
        ROM_SIZE_BYTESIZE     +\
        ROM_RAM_SIZE_BYTESIZE +\
        ENTRY_POINT_BYTESIZE  +\
        CRT0_SIZE_BYTESIZE    +\
        MAGIC_NUMBER_AND_VERSION_BYTESIZE

    # Offsets from the end of the file.
    FOOTER_RAM_SIZE_OFFSET                 = -28
    FOOTER_BSS_SIZE_OFFSET                 = FOOTER_RAM_SIZE_OFFSET
    FOOTER_GOT_SIZE_OFFSET                 = -24
    FOOTER_ROM_SIZE_OFFSET                 = -20
    FOOTER_TEXT_SIZE_OFFSET                = FOOTER_ROM_SIZE_OFFSET
    FOOTER_ROM_RAM_SIZE_OFFSET             = -16
    FOOTER_DATA_SIZE_OFFSET                = FOOTER_ROM_RAM_SIZE_OFFSET
    FOOTER_ENTRYPOINT_OFFSET               = -12
    FOOTER_CRT0_OFFSET                     = -8
    FOOTER_MAGIC_NUMBER_AND_VERSION_OFFSET = -4

    MINIMAL_BYTESIZE =                      \
        BINARY_SIZE_BYTESIZE              + \
        RELOCATION_ENTRIES_COUNT_BYTESIZE + \
        FOOTER_BYTESIZE


    # The default value used for padding. This value corresponds to
    # the default state of non-volatile NAND flash memories
    PADDING_VALUE         = b'\xff'

    # The binary size must be a multiple of this value.
    # It corresponds to the minimum alignment required by the MPU of
    # the ARMv7-M architecture
    PADDING_MPU_ALIGNMENT = 32
