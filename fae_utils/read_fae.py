#!/usr/bin/env python3

# Copyright (C) 2025 Université de Lille
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

import sys
import tempfile
import subprocess

from constants import FAEConstants

def die(message):
    """Print error message and exit"""
    print(f'\033[91;1m{sys.argv[0]} : {message}\033[0m', file=sys.stderr)
    sys.exit(1)

def die_on_invalid_file(message) :
    die(f'Invalid file {sys.argv[1]} : {message}')

def die_on_negative_value_from_file(message) :
    die(f'negative value  : {message}')

def check_negative_value_from_file(message, value):
    if value < 0:
        die_on_negative_value_from_file(message)

def check_less_than_binary_size(label, value, binary_size):
    if value >= binary_size:
        die_on_invalid_file(f'{label} ({crt0_size}) is greater than or equal to binary size')

def check_value_from_file(label, value, binary_size):
    check_negative_value_from_file(label, value)
    check_less_than_binary_size(label, value, binary_size)


def get_word_from_memoryview(from_memoryview, start_index_in_bytes):
    '''Generic word (four bytes) memoryview getter according to endianness.
       Supports negative value for start_index_in_bytes'''
    if start_index_in_bytes < 0 and (start_index_in_bytes + 4 == 0):
        this_memoryview = from_memoryview[start_index_in_bytes:]
    else:
        this_memoryview = from_memoryview[ \
            start_index_in_bytes:start_index_in_bytes + 4]
    these_bytes     = this_memoryview.tobytes()
    this_word       = int.from_bytes(these_bytes, byteorder=FAEConstants.ENDIANNESS)

    return this_word


def get_bytes_text_suffix(value):
    return 'bytes' if value > 1 else 'byte'

def print_bytesize(label, value):
    '''Prints the bytesize of a label and a corresponding value'''
    bytes_text_suffix = get_bytes_text_suffix(value)
    print(f'{label} : {value} {bytes_text_suffix}')

def print_chunk(chunk_name, chunk_start, chunk_end, chunk_size):
    '''Prints a memory chunk as a triplet [start,end)(size)'''
    print(f'- {chunk_name} : '
          f'[start : @{chunk_start} {get_bytes_text_suffix(chunk_start)} , '
          f'end : @{chunk_end} {get_bytes_text_suffix(chunk_end)}] '
          f'(size : {chunk_size} {get_bytes_text_suffix(chunk_end)})')

def print_disassembly(label, fae_memory, start, end):
    '''Prints code disassembly for bytes in fae_memory[start:end]'''
    with tempfile.TemporaryDirectory() as tmp_directory_name:
        filename = tmp_directory_name + "/" + label
        with open(filename, "wb") as this_file:
            this_memoryview = fae_memoryview[start:end]
            these_bytes     = this_memoryview.tobytes()
            this_file.write(these_bytes)

        objdump_args  = FAEConstants.OBJDUMP_ARGS_BASE + filename
        result = subprocess.run(objdump_args, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            die(f'Failed to disassemble {label}')
        print(result.stdout)

def print_hexdump_line(line_number, a_memoryview, start_index_in_bytes, bytescount):
    line_number_string = f'{hex(line_number)}'[2:]
    line_number_string = line_number_string.rjust(8, '0')

    if bytescount > 16:
        this_bytes_count = 16
        these_bytes = a_memoryview.obj[start_index_in_bytes:start_index_in_bytes + 16]
        a = these_bytes[0:8].hex(' ',1)
        b = these_bytes[8:16].hex(' ',1)
    elif bytescount > 8:
        this_bytes_count = bytescount
        these_bytes = a_memoryview.obj[start_index_in_bytes:start_index_in_bytes + bytescount]
        a = these_bytes[0:8].hex(' ',1)
        b = these_bytes[8:8+(bytescount - 8)]
        b = b.hex(' ', 1).ljust(23, ' ')
    else :
        this_bytes_count = bytescount
        these_bytes = a_memoryview.obj[start_index_in_bytes:start_index_in_bytes + bytescount]
        a = these_bytes[0:bytescount].hex(' ',1)
        b = '                                   '

    c = '|'
    for i in range(this_bytes_count):
        this_byte = these_bytes[i:i+1]
        if this_byte.isascii():
            d  = this_byte.decode("ascii")
            c += d if d.isprintable() else '.'
        else:
            c += '.'
    c = c.ljust(17)
    c += '|'

    print(f'{line_number_string}  {a}  {b}  {c}')

def print_hexdump(fae_memoryview):
    size = len(fae_memoryview)
    nb_blocks_of_16_bytes = size // 16
    remaining = size % 16

    start = 0
    for i in range(nb_blocks_of_16_bytes):
        start = i * 16
        print_hexdump_line(start, fae_memoryview, start, size)
        size -= 16

    if size > 0:
        print_hexdump_line(start, fae_memoryview, start, size)


CLI_OPTION_DISASSEMBLE_CRT0    = "-Dcrt0"
CLI_OPTION_HEXDUMP_CRT0        = "-Hcrt0"

CLI_OPTION_HEXDUMP_RELOCATIONS = "-Hreloc"

CLI_OPTION_HEXDUMP_ROM_RAM     = "-Hromram"

CLI_OPTION_DISASSEMBLE_TEXT    = "-Drom"
CLI_OPTION_HEXDUMP_TEXT        = "-Hrom"

CLI_OPTION_HEXDUMP_GOT         = "-Hgot"

CLI_OPTION_VERBOSE             = "-v"

CLI_OPTIONS = {                                                               \
    CLI_OPTION_DISASSEMBLE_CRT0    : 'will disassemble CRT0',                 \
    CLI_OPTION_HEXDUMP_CRT0        : 'will hexdump CRT0',                     \
    CLI_OPTION_HEXDUMP_RELOCATIONS : 'will hexdump relocation table',         \
    CLI_OPTION_HEXDUMP_ROM_RAM     : 'will hexdump rom_ram section aka data', \
    CLI_OPTION_DISASSEMBLE_TEXT    : 'will disassemble rom section aka text', \
    CLI_OPTION_HEXDUMP_TEXT        : 'will hexdump rom section aka text',     \
    CLI_OPTION_HEXDUMP_GOT         : "will hexdump GOT",                      \
    CLI_OPTION_VERBOSE             : "will enable all options"
}

def usage():
    """Print how to to use the script and exit"""
    summary = f'usage: {sys.argv[0]} ['
    separator = ''
    for k,v in CLI_OPTIONS.items():
        summary += separator + k
        separator = ", "
    summary += "] FAEFilename"
    print(summary)
    print('')
    for k,v in CLI_OPTIONS.items():
        print(f'-{k} : {v}')
    sys.exit(1)

def parse_options():
    argc = len(sys.argv)
    if argc < 2:
        usage()
    if sys.argv[argc - 1].startswith('-'):
        print("Last command line argument cannot be an option.")
        print("Last command line argument must be a FAE filename.")
        usage()

    options = set()
    for i in range(1, argc - 1):
        if sys.argv[i] in CLI_OPTIONS:
            if sys.argv[i] != CLI_OPTION_VERBOSE:
                options.add(sys.argv[i])
            else:
                for k,v in CLI_OPTIONS.items():
                    if k != CLI_OPTION_VERBOSE:
                        options.add(k)
        else:
            print(f'{sys.argv[i]} is not a recognized command line option')
            usage()

    return options


if __name__ == '__main__':

    options = parse_options()

    fae_bytearray = bytearray()
    with open(sys.argv[len(sys.argv) - 1], "rb") as fae_file:
        fae_bytearray += bytearray(fae_file.read())

    # Binary size
    binary_size = len(fae_bytearray)
    print_bytesize('- Binary size', binary_size)

    if binary_size == 0:
        die_on_invalid_file('Empty file')

    check_negative_value_from_file('Binary size', binary_size)

    if binary_size <= FAEConstants.MINIMAL_BYTESIZE:
        die_on_invalid_file(f'Binary size is less than or equal to '
                            f'minimal bytesize ({FAEConstants.MINIMAL_BYTESIZE})')

    fae_memoryview = memoryview(fae_bytearray)

    # 0 : Magic number and version
    magic_number_and_version = get_word_from_memoryview(
        fae_memoryview, FAEConstants.FOOTER_MAGIC_NUMBER_AND_VERSION_OFFSET)

    print(f'- Magic Number And Version : {hex(magic_number_and_version)}')

    check_negative_value_from_file('Magic Number And Version', \
                                   magic_number_and_version)
    if magic_number_and_version < FAEConstants.MAGIC_NUMBER:
        die_on_invalid_file(f'invalid magic number and version : '
                            f'{magic_number_and_version}')
    version = magic_number_and_version - FAEConstants.MAGIC_NUMBER
    if version != FAEConstants.VERSION:
        die_on_invalid_file(f'version not supported : {version}')

    # 1 : CRT0size
    crt0_size = get_word_from_memoryview(
        fae_memoryview, FAEConstants.FOOTER_CRT0_OFFSET)

    check_value_from_file('CRT0_size', crt0_size, binary_size)
    if crt0_size == 0:
        die_on_invalid_file(f'CRT0_size is equal to 0')

    print_chunk('CRT0', 0, crt0_size - 1, crt0_size)
    if CLI_OPTION_DISASSEMBLE_CRT0 in options:
        print_disassembly('CRT0', fae_memoryview, 0, crt0_size - 1)
    if CLI_OPTION_HEXDUMP_CRT0 in options:
        this_bytearray = fae_memoryview.obj[0:crt0_size]
        print_hexdump(memoryview(this_bytearray))

    # Binary size hosted within the file
    binary_size_from_file = get_word_from_memoryview(fae_memoryview, crt0_size)
    if binary_size_from_file != binary_size:
        die_on_invalid_file(f'binary_size_from_file ({binary_size_from_file}' \
                            ') is different from binary size')

    # + 4 is for the hosted binary size
    iterator = crt0_size + 4

    # Relocations
    relocation_entries_start = iterator
    relocation_entries_count = get_word_from_memoryview(
        fae_memoryview, relocation_entries_start)
    check_negative_value_from_file( 'relocations entries count', \
                                    relocation_entries_count )
    relocation_entries_size = relocation_entries_count * 4
    check_less_than_binary_size( 'relocation entries size', \
                                 relocation_entries_size, binary_size)
    if relocation_entries_size > 0:
        relocation_entries_end = relocation_entries_start + \
                                relocation_entries_size - 1
        print_chunk('Relocation entries',     \
                    relocation_entries_start, \
                    relocation_entries_end,   \
                    relocation_entries_size)
        print(f'\t- Count : {relocation_entries_count}')
        if CLI_OPTION_HEXDUMP_RELOCATIONS in options:
            this_bytearray = fae_memoryview.obj[ \
                relocation_entries_start:        \
                relocation_entries_start + relocation_entries_size]
            print_hexdump(memoryview(this_bytearray))

        iterator = relocation_entries_end + 1
    else:
        print('- Relocation entries : none.')


    # 2 : Entrypoint
    entrypoint_offset = get_word_from_memoryview(
        fae_memoryview, FAEConstants.FOOTER_ENTRYPOINT_OFFSET)
    print_bytesize('- Entrypoint offset in .rom', entrypoint_offset)
    check_value_from_file('Entrypoint offset', entrypoint_offset, binary_size)

    # 3 : Rom ram size aka data size
    rom_ram_size = get_word_from_memoryview(
        fae_memoryview, FAEConstants.FOOTER_ROM_RAM_SIZE_OFFSET)
    check_value_from_file('rom_ram_size', rom_ram_size, binary_size)

    rom_ram_start = iterator
    if rom_ram_size > 0:
        rom_ram_end = rom_ram_start + rom_ram_size - 1

        print_chunk('.rom.ram', rom_ram_start, rom_ram_end, rom_ram_size)
        if CLI_OPTION_HEXDUMP_ROM_RAM in options:
            this_bytearray = fae_memoryview.obj[rom_ram_start:rom_ram_end + 1]
            print_hexdump(memoryview(this_bytearray))

        iterator = rom_ram_end + 1
    else:
        print('- .rom.ram : none.')

    # 4 : Rom size aka text size
    rom_size = get_word_from_memoryview(
        fae_memoryview, FAEConstants.FOOTER_ROM_SIZE_OFFSET)
    check_value_from_file('rom_size', rom_size, binary_size)

    rom_start = iterator
    if rom_size > 0:
        rom_end = rom_start + rom_size - 1

        print_chunk('.rom', rom_start, rom_end, rom_size)
        if CLI_OPTION_DISASSEMBLE_TEXT in options:
            print_disassembly('.rom', fae_memoryview, rom_start, rom_end)
        if CLI_OPTION_HEXDUMP_TEXT in options:
            this_bytearray = fae_memoryview.obj[rom_start:rom_end + 1]
            print_hexdump(memoryview(this_bytearray))

        if entrypoint_offset > rom_size:
            die_on_invalid_file( \
                'Entrypoint offset is out of .rom aka text section')

        iterator = rom_end + 1
    else:
        print('- .rom : none.')

    # 5 : GOT size
    got_size = get_word_from_memoryview(
        fae_memoryview, FAEConstants.FOOTER_GOT_SIZE_OFFSET)
    check_value_from_file('got size', got_size, binary_size)

    got_start = rom_end + 1
    if got_size > 0:
        got_end = got_start + got_size - 1
        print_chunk(".got", got_start, got_end, got_size)
        if CLI_OPTION_HEXDUMP_GOT in options:
            this_bytearray = fae_memoryview.obj[got_start:got_end + 1]
            print_hexdump(memoryview(this_bytearray))
    else:
        print('.got : none.')


    # 6 : Ram size aka BSS size
    ram_size = get_word_from_memoryview(
        fae_memoryview, FAEConstants.FOOTER_RAM_SIZE_OFFSET)
    check_negative_value_from_file("RAM size", ram_size)

    print_bytesize(".bss", ram_size)

    print("- Integrity check : OK")
