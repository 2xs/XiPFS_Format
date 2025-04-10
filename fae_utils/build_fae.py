#!/usr/bin/env python3

# Copyright (C) 2025 Université de Lille
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

import os
import sys
import subprocess

from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from elftools.elf.relocation import RelocationSection
from elftools.elf.enums import ENUM_RELOC_TYPE_ARM as r_types

FAE_SUFFIX      = ".fae"
CRTO_CLI_OPTION = "--crt0_path"
EXPORT_CRT0_TO_BYTEARRAY_DEFAULT_PATH = "./crt0/"

def usage():
    """Print how to to use the script and exit"""
    print(f'usage: {sys.argv[0]} [{CRTO_CLI_OPTION} crt0_path] ELFFilename')
    print('')
    print(f'{sys.argv[0]} will build :')
    print(f'    - a fae file from ELFFilename,')
    print(f'    - a gdbinit file, to be used with gdb after editing.')
    print(f'Please note that both files will be generated to the path of ELFFilename.')
    print('')
    print(f'{CRTO_CLI_OPTION} crt0_path')
    print(f'    This option allows to indicate a path to a custom crt0')
    print(f'    Default is {EXPORT_CRT0_TO_BYTEARRAY_DEFAULT_PATH}')
    sys.exit(1)


def die(message):
    """Print error message and exit"""
    print(f'\033[91;1m{sys.argv[0]}: {message}\033[0m', file=sys.stderr)
    sys.exit(1)


def export_crt0_to_bytearray(path_to_crt0, to_bytearray):
    make_args = f"make -C {os.path.abspath(path_to_crt0)} realclean all"

    result = subprocess.run(make_args, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        die(f'export_crt0_to_bytearray : failed to build crt0 : {result.stderr}')

    crt0_filepath = path_to_crt0 + "/crt0.fae"
    with open(crt0_filepath, "rb") as crt0_file:
        to_bytearray += bytearray(crt0_file.read())

def to_word(x):
    """Convert a python integer to a LE 4-bytes bytearray"""
    return x.to_bytes(4, byteorder='little')

EXPORTED_SYMBOLS = [
    # The order of the symbols matter, as it reflects the
    # writing order in the symbols.bin file
    'start',
    '__rom_size',
    '__rom_ram_size',
    '__ram_size',
    '__got_size',
    '__rom_ram_end',
]

def export_symbols_to_bytearray(elf_file, symbols_names, to_bytearray):
    """Parse the symbol table sections to extract the st_value"""
    sh = elf_file.get_section_by_name('.symtab')
    if not sh:
        die(f'export_symbols_to_bytearray : .symtab : no section with this name found')
    if not isinstance(sh, SymbolTableSection):
        die(f'export_symbols_to_bytearray : .symtab : is not a symbol table section')
    if sh['sh_type'] != 'SHT_SYMTAB':
        die(f'export_symbols_to_bytearray : .symtab : is not a SHT_SYMTAB section')
    for symbol_name in symbols_names:
        symbols = sh.get_symbol_by_name(symbol_name)
        if not symbols:
            die(f'export_symbols_to_bytearray : .symtab : {symbol_name}: no symbol with this name')
        if len(symbols) > 1:
            die(f'export_symbols_to_bytearray : .symtab : {symbol_name}: more than one symbol with this name')
        to_bytearray += to_word(symbols[0].entry['st_value'])


EXPORTED_RELOCATION_TABLES = [ '.rel.rom.ram' ]

def get_r_type(r_info):
    """Get the relocation type from r_info"""
    return r_info & 0xff

def export_relocation_table(elf_file, relocation_table_name, to_bytearray):
    """Parse a relocation section to extract the r_offset"""
    sh = elf_file.get_section_by_name(relocation_table_name)
    if not sh:
        die(f'export_relocation_table : {relocation_table_name}: is not a relocation section')
    if not isinstance(sh, RelocationSection):
        die(f'export_relocation_table : {relocation_table_name}: is not a relocation section')
    if sh.is_RELA():
        die(f'export_relocation_table : {relocation_table_name} : unsupported RELA')
    to_bytearray += to_word(sh.num_relocations())
    for i, entry in enumerate(sh.iter_relocations()):
        if get_r_type(entry['r_info']) != r_types['R_ARM_ABS32']:
            die(f'export_relocation_table : {relocation_table_name} : entry {i}: unsupported relocation type')
        to_bytearray += to_word(entry['r_offset'])

def export_relocation_tables(elf_file, relocation_tables_names, to_bytearray):
    for relocation_table_name in relocation_tables_names:
        export_relocation_table(elf_file, relocation_table_name, to_bytearray)


EXPORT_PARTITION_OBJCOPY_DEFAULT_NAME = "arm-none-eabi-objcopy"

EXPORT_PARTITION_OBJCOPY_FLAGS = [
    "--input-target=elf32-littlearm", "--output-target=binary"
]

def export_partition(elf_name, objcopy_name, objcopy_flags, to_bytearray):
    partition_name = "partition.fae"

    objcopy_args = objcopy_name
    for objcopy_flag in objcopy_flags:
        objcopy_args += f' {objcopy_flag}'
    objcopy_args += f' {elf_name} {partition_name}'

    result = subprocess.run(objcopy_args, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f'export_partition : {result.stdout}')
        die(f'export_partition : failed to run objcopy : {result.stderr}')

    with open(partition_name, "rb") as partition_file:
        to_bytearray += bytearray(partition_file.read())

    rm_args = f'rm {partition_name}'

    result = subprocess.run(args=rm_args, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        die(f'export_partition : failed to remove {partition_name} : {result.stderr}')


# The default value used for padding. This value corresponds to
# the default state of non-volatile NAND flash memories
PADDING_VALUE = b'\xff'


# The Pip binary size must be a multiple of this value. It
# corresponds to the minimum alignment required by the MPU of
# the ARMv7-M architecture
PADDING_MPU_ALIGNMENT = 32

def round(x, y):
    """Round x to the next power of two y"""
    return ((x + y - 1) & ~(y - 1))

def pad_bytearray(to_bytearray):
    size = len(to_bytearray)
    padding = round(size, PADDING_MPU_ALIGNMENT) - size
    for i in range(padding):
        to_bytearray += PADDING_VALUE


GENERATE_GDBINIT_DEFAULT_SYMBOLS_TO_FIND = [
    '__rom_size',
    '__got_size',
    '__rom_ram_size',
    '__ram_size',
]

def gdbinit_find_symbols(elf_file, symbols_to_find):
    """Parse the symbol table sections to extract the st_value"""
    sh = elf_file.get_section_by_name('.symtab')
    if not sh:
        die(f'gdbinit_find_symbols : .symtab : no section with this name found')
    if not isinstance(sh, SymbolTableSection):
        die(f'gdbinit_find_symbols : .symtab : is not a symbol table section')
    if sh['sh_type'] != 'SHT_SYMTAB':
        die(f'gdbinit_find_symbols : .symtab : is not a SHT_SYMTAB section')
    found_symbols = []
    for symbol_name in symbols_to_find:
        symbols = sh.get_symbol_by_name(symbol_name)
        if not symbols:
            die(f'gdbinit_find_symbols : .symtab : {symbol_name}: no symbol with this name')
        if len(symbols) > 1:
            die(f'gdbinit_find_symbols : .symtab : {symbol_name}: more than one symbol with this name')
        found_symbols.append(symbols[0].entry['st_value'])
    return found_symbols

def generate_gdbinit(elf_file, crt0_path, metadata_size):
    found_symbols = gdbinit_find_symbols(elf_file, GENERATE_GDBINIT_DEFAULT_SYMBOLS_TO_FIND)

    text_size = found_symbols[0]
    got_size  = found_symbols[1]
    data_size = found_symbols[2]
    bss_size  = found_symbols[3]

    basepath           = elf_file.stream.name.split("/")[0]
    absolute_elf_path  = os.path.abspath(elf_file.stream.name)
    absolute_crt0_path = os.path.abspath(crt0_path + "crt0.elf")

    with open(f"{basepath}/gdbinit", "w+") as gdbinit_file:
        gdbinit_file.write(f'set $flash_base = # Define the flash base address here\n')
        gdbinit_file.write(f'set $ram_base = # Define the RAM base address here\n')
        gdbinit_file.write(f'set $crt0_text = $flash_base\n')
        gdbinit_file.write(f'set $text = $crt0_text + {metadata_size}\n')
        gdbinit_file.write(f'set $got = $text + {text_size}\n')
        gdbinit_file.write(f'set $data = $got + {got_size}\n')
        gdbinit_file.write(f'set $rel_got = $ram_base\n')
        gdbinit_file.write(f'set $rel_data = $rel_got + {got_size}\n')
        gdbinit_file.write(f'set $bss = $rel_data + {data_size}\n')
        gdbinit_file.write(f'add-symbol-file {absolute_crt0_path} -s .text $crt0_text\n')
        gdbinit_file.write(f'add-symbol-file {absolute_elf_path} '
                           '-s .rom $text '
                           '-s .got $rel_got '
                           '-s .rom.ram $rel_data '
                           '-s .ram $bss\n')
        gdbinit_file.write('set $flash_end = $flash_base + '
                           f'{metadata_size + text_size + got_size + data_size}\n')
        gdbinit_file.write(f'set $ram_end = $ram_base + {got_size + data_size + bss_size}\n')


if __name__ == '__main__':
    argc = len(sys.argv)
    if argc != 2 and argc != 4:
        print(f"argc {argc}")
        usage()



    if argc == 2:
        elf_filename = sys.argv[1].strip()
        crt0_path = EXPORT_CRT0_TO_BYTEARRAY_DEFAULT_PATH.strip()
    else :
        if (sys.argv[1] != CRTO_CLI_OPTION):
            usage()

        crt0_path = sys.argv[2].strip()
        elf_filename = sys.argv[3].strip()

    elf_filename_parts = elf_filename.split('.')
    if len(elf_filename_parts) != 2 or elf_filename_parts[1] != 'elf':
        print('Bad ELFFilename : should be something along the line of name.elf')
        usage()

    output_filename = elf_filename_parts[0] + FAE_SUFFIX

    if crt0_path.endswith('/') == False:
        crt0_path += '/'

    array_of_bytes = bytearray()
    with open(elf_filename, 'rb') as f:
        elf_file = ELFFile(f)

        # Formerly known as crt0.fae
        export_crt0_to_bytearray(crt0_path, array_of_bytes)

        # Formerly known as symbols.fae
        export_symbols_to_bytearray(elf_file, EXPORTED_SYMBOLS, array_of_bytes)

        # Formerly known as relocation.fae
        export_relocation_tables(elf_file, EXPORTED_RELOCATION_TABLES, array_of_bytes)
        metadata_size = len(array_of_bytes)

        # Formerly known as partition.fae
        export_partition(
            elf_filename,
            EXPORT_PARTITION_OBJCOPY_DEFAULT_NAME,
            EXPORT_PARTITION_OBJCOPY_FLAGS,
            array_of_bytes)

        #Formerly known as padding.fae
        pad_bytearray(array_of_bytes)

        # gdbinit
        generate_gdbinit( elf_file, crt0_path, metadata_size )

    if (len(array_of_bytes) <= 0):
        die("Nothing has been written into array_of_bytes ! Please contact authors.")
    with open(output_filename, 'wb') as f:
        f.write(array_of_bytes)
    sys.exit(0)
