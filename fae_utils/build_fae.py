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

from constants import FAEConstants

CLI_OPTION_CRT0_PATH = "--crt0_path"

def usage():
    """Print how to to use the script and exit"""
    print(f'usage: {sys.argv[0]} [{CLI_OPTION_CRT0_PATH} crt0_path] ELFFilename')
    print('')
    print(f'{sys.argv[0]} will build :')
    print( '    - a fae file from ELFFilename,')
    print(f'    - a {FAEConstants.gdbinit} file, to be used with gdb after editing.')
    print( 'Please note that both files will be generated to the path of ELFFilename.')
    print('')
    print(f'{CLI_OPTION_CRT0_PATH} crt0_path')
    print( '    This option allows to indicate a path to a custom crt0')
    print(f'    Default is {EXPORT_CRT0_TO_BYTEARRAY_DEFAULT_PATH}')
    sys.exit(1)


def die(message):
    """Print error message and exit"""
    print(f'\033[91;1m{sys.argv[0]}: {message}\033[0m', file=sys.stderr)
    sys.exit(1)


def export_crt0_to_bytearray(path_to_crt0, to_bytearray):
    make_args = f"{FAEConstants.MAKE} -C {os.path.abspath(path_to_crt0)} realclean all"

    result = subprocess.run(make_args, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        die(f'export_crt0_to_bytearray : failed to build crt0 : {result.stderr}')

    crt0_filepath = os.path.abspath(f'build/crt0{FAEConstants.SUFFIX}')
    with open(crt0_filepath, "rb") as crt0_file:
        to_bytearray += bytearray(crt0_file.read())
    print(f'Export CRT0 : {len(to_bytearray)} bytes')

def to_word(x):
    """Convert a python integer to a LE 4-bytes bytearray"""
    return x.to_bytes(4, byteorder=FAEConstants.ENDIANNESS)



def export_symbols_to_dict(elf_file, symbols_names, to_dict):
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
        to_dict[symbol_name] = symbols[0].entry['st_value']
        print(f'Export symbol {symbol_name} = {to_dict[symbol_name]} bytes')


def get_r_type(r_info):
    """Get the relocation type from r_info"""
    return r_info & 0xff

def export_relocation_table(elf_file, relocation_table_name, to_bytearray):
    """Parse a relocation section to extract the r_offset"""
    sh = elf_file.get_section_by_name(relocation_table_name)
    if not sh:
        print(f'No relocation section named {relocation_table_name}')
        to_bytearray += to_word(0)
        return
    if not isinstance(sh, RelocationSection):
        die(f'export_relocation_table : {relocation_table_name}: is not a relocation section')
    if sh.is_RELA():
        die(f'export_relocation_table : {relocation_table_name} : unsupported RELA')
    to_bytearray += to_word(sh.num_relocations())
    print(f'Export relocation table : entries count : {sh.num_relocations()}')
    for i, entry in enumerate(sh.iter_relocations()):
        if get_r_type(entry['r_info']) != r_types['R_ARM_ABS32']:
            die(f'export_relocation_table : {relocation_table_name} : entry {i}: unsupported relocation type')
        offset = entry['r_offset']
        to_bytearray += to_word(offset)
        print(f'\t- Exporting relocation entry {i} : offset {offset}')

def export_relocation_tables(elf_file, relocation_tables_names, to_bytearray):
    for relocation_table_name in relocation_tables_names:
        export_relocation_table(elf_file, relocation_table_name, to_bytearray)


def export_partition(elf_name, to_bytearray):

    partition_name = FAEConstants.PARTITION_NAME
    objcopy_args = f'{FAEConstants.OBJCOPY_ARGS_BASE} {elf_name} {partition_name}'

    result = subprocess.run(objcopy_args, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f'export_partition : {result.stdout}')
        die(f'export_partition : failed to run objcopy : {result.stderr}')

    with open(partition_name, "rb") as partition_file:
        to_bytearray += bytearray(partition_file.read())

    print(f'Export partition : {len(to_bytearray)} bytes')

    rm_args = f'{FAEConstants.RM} {partition_name}'

    result = subprocess.run(args=rm_args, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        die(f'export_partition : failed to remove {partition_name} : {result.stderr}')


def round(x, y):
    """Round x to the next power of two y"""
    return ((x + y - 1) & ~(y - 1))

def concatenate_and_pad_bytearray(
            crt0_bytearray,
            exported_symbols_dictionary,
            relocation_bytearray,
            partition_bytearray,
            to_bytearray):

    raw_binary_size = len(crt0_bytearray)               \
                    + FAEConstants.BINARY_SIZE_BYTESIZE \
                    + len(relocation_bytearray)         \
                    + len(partition_bytearray)

    padding_size =                                                 \
        round(raw_binary_size, FAEConstants.PADDING_MPU_ALIGNMENT) \
        - raw_binary_size
    # minimal padding size represents :
    # CRT0 size,               =>  4 bytes.
    # EntryPoint aka start     =>  4 bytes.
    # __rom_ram_size           =>  4 bytes.
    # Magic Number and Version =>  4 bytes.
    #--------------------------------------
    #                             16 bytes.
    if padding_size < FAEConstants.FOOTER_BYTESIZE:
        padding_size += FAEConstants.PADDING_MPU_ALIGNMENT

    padding_size -= FAEConstants.FOOTER_BYTESIZE

    # CRT0
    to_bytearray += crt0_bytearray
    # Binary Size
    to_bytearray += to_word( \
        raw_binary_size + padding_size + FAEConstants.FOOTER_BYTESIZE)
    # Relocation Table
    to_bytearray += relocation_bytearray
    # Partition
    to_bytearray += partition_bytearray
    # Padding - minimal_padding_size
    for i in range(padding_size):
        to_bytearray += FAEConstants.PADDING_VALUE

    # FOOTER_RAM_SIZE_OFFSET                 = -28
    # FOOTER_BSS_SIZE_OFFSET                 = FOOTER_RAM_SIZE_OFFSET
    to_bytearray += to_word( \
        exported_symbols_dictionary[FAEConstants.EXPORTED_SYMBOL_RAM_SIZE])
    # FOOTER_GOT_SIZE_OFFSET                 = -24
    to_bytearray += to_word( \
        exported_symbols_dictionary[FAEConstants.EXPORTED_SYMBOL_GOT_SIZE])
    # FOOTER_ROM_SIZE_OFFSET                 = -20
    # FOOTER_TEXT_SIZE_OFFSET                = FOOTER_ROM_SIZE_OFFSET
    to_bytearray += to_word( \
        exported_symbols_dictionary[FAEConstants.EXPORTED_SYMBOL_ROM_SIZE])
    # FOOTER_ROM_RAM_SIZE_OFFSET             = -16
    # FOOTER_DATA_SIZE_OFFSET                = FOOTER_ROM_RAM_SIZE_OFFSET
    to_bytearray += to_word( \
        exported_symbols_dictionary[FAEConstants.EXPORTED_SYMBOL_ROM_RAM_SIZE])
    # FOOTER_ENTRYPOINT_OFFSET               = -12
    to_bytearray += to_word( \
        exported_symbols_dictionary[FAEConstants.EXPORTED_SYMBOL_START])
    # FOOTER_CRT0_OFFSET                     = -8
    to_bytearray += to_word(len(crt0_bytearray))
    # FOOTER_MAGIC_NUMBER_AND_VERSION_OFFSET = -4
    to_bytearray += to_word(FAEConstants.MAGIC_NUMBER_AND_VERSION)



def generate_gdbinit(elf_file, crt0_path, metadata_size, exported_symbols_dictionary):
    text_size = \
        exported_symbols_dictionary[FAEConstants.EXPORTED_SYMBOL_ROM_SIZE]
    got_size  = \
        exported_symbols_dictionary[FAEConstants.EXPORTED_SYMBOL_GOT_SIZE]
    data_size = \
        exported_symbols_dictionary[FAEConstants.EXPORTED_SYMBOL_ROM_RAM_SIZE]
    bss_size  = \
        exported_symbols_dictionary[FAEConstants.EXPORTED_SYMBOL_RAM_SIZE]

    basepath           = elf_file.stream.name.split("/")[0]
    absolute_elf_path  = os.path.abspath(elf_file.stream.name)
    absolute_crt0_path = os.path.abspath(basepath + "/crt0.elf")

    gdbinit_filename = f"{basepath}/{FAEConstants.GDBINIT_FILENAME}"

    with open(gdbinit_filename, "w+") as gdbinit_file:
        gdbinit_file.write('set $flash_base = # Define the flash base address here\n')
        gdbinit_file.write('set $ram_base = # Define the RAM base address here\n')
        gdbinit_file.write('set $crt0_text = $flash_base\n')
        gdbinit_file.write(f'set $text = $crt0_text + {metadata_size}\n')
        gdbinit_file.write(f'set $got = $text + {text_size}\n')
        gdbinit_file.write(f'set $data = $got + {got_size}\n')
        gdbinit_file.write('set $rel_got = $ram_base\n')
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

    print(f'{os.path.abspath(gdbinit_filename)} has been generated.')

if __name__ == '__main__':
    argc = len(sys.argv)
    if argc != 2 and argc != 4:
        print(f"argc {argc}")
        usage()

    if argc == 2:
        elf_filename = sys.argv[1].strip()
        crt0_path = FAEConstants.CRT0_DEFAULT_PATH.strip()
    else :
        if (sys.argv[1] != CLI_OPTION_CRT0_PATH):
            usage()

        crt0_path = sys.argv[2].strip()
        elf_filename = sys.argv[3].strip()

    elf_filename_parts = elf_filename.split('.')
    if len(elf_filename_parts) != 2 or elf_filename_parts[1] != 'elf':
        print('Bad ELFFilename : should be something along the line of name.elf')
        usage()

    output_filename = elf_filename_parts[0] + FAEConstants.SUFFIX

    if crt0_path.endswith('/') == False:
        crt0_path += '/'

    array_of_bytes = bytearray()
    with open(elf_filename, 'rb') as f:
        elf_file = ELFFile(f)

        # Formerly known as crt0.fae
        crt0_bytearray = bytearray()
        export_crt0_to_bytearray(crt0_path, crt0_bytearray)

        # Formerly known as symbols.fae
        exported_symbols_dictionary = dict()
        export_symbols_to_dict(                      \
            elf_file, FAEConstants.EXPORTED_SYMBOLS, \
                exported_symbols_dictionary)

        # Formerly known as relocation.fae
        relocation_bytearray = bytearray()
        export_relocation_tables(                              \
            elf_file, FAEConstants.EXPORTED_RELOCATION_TABLES, \
            relocation_bytearray)
        metadata_size = len(array_of_bytes)

        # Formerly known as partition.fae
        partition_bytearray = bytearray()
        export_partition( elf_filename, partition_bytearray )

        concatenate_and_pad_bytearray(
            crt0_bytearray,
            exported_symbols_dictionary,
            relocation_bytearray,
            partition_bytearray,
            array_of_bytes)

        # gdbinit
        generate_gdbinit(
            elf_file,
            crt0_path,
            metadata_size,
            exported_symbols_dictionary)

    if (len(array_of_bytes) <= 0):
        die("Nothing has been written into array_of_bytes ! Please contact authors.")
    with open(output_filename, 'wb') as f:
        f.write(array_of_bytes)
    sys.exit(0)
