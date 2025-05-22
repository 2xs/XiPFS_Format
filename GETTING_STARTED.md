# Getting Started with XIPFS Format

## Context
ELF files have a quite large memory footprint and are not that easy to parse;
two points that are not desired in an embedded software context or a post-issuance one.

XIPFS format is a custom made file format that only needs a few information to ensure
runtime execution.

XIPFS format toolchain parses off-board the ELF format to collect these data to
satisfy the XIPFS loader (located in `xipfs_file_exec`).

Once the ELF file converted to a FAE file, developers only have to upload the latter onto
the board, where XIPFS has been deployed before.

## Prerequisites
Developers will need :

+ a GNU ARM toolchain, as of today available on [ARM developer site](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads).

  Latest version can be downloaded, but at least arm-none-eabi version 13.3.1 is required.

  *The tools* **MUST** *be available system-wide :*
  - *either by creating aliases/symbolic links to their real locations,*
  - *or by adding their path to the PATH environment variable on Linux and alike systems.*
+ GNU Make version 4.3.
+ python3.
+ pyelftools, at least in version 0.30.

  *On Linux, according to distibutions, one may apt install them (`python3-pyelftools`)*.

## How to build your own code to XIPFS format ?
Because XIPFS format is a toolchain relying on different tools and linker scripts/options,
developers will first need their **sources to be included at the root of this very template**.

Then, **root Makefile needs to be modified accordingly to the target sources in order to build an ELF version of the program.**
Developers **may add and modify target rules and dependencies**, but also add both **compilation and linker options**.

**ELF name can be chosen by modifying the TARGET** make variable at the beginning of the Makefile.
*By default, it is defined as "hello-world".*

Once an ELF file is obtained, the **XIPFS toolchain is able to convert this ELF file to a FAE one automatically**, without any other modification.

No need to touch to the CRT0 or the fae_utils directories contents.

Once the root Makefile has been edited to include project sources and build directives, **just enter `make` in a terminal**.

The XIPFS will then **produce different files into the `build` directory** at project's root :

+ Intermediate files such as `*.o` object files,
+ ELF files,
+ FAE files,
+ gdbinit file, which is aimed at be sourced into `gdb` to ease debugging.

## How to use the generated gdbinit file ?
Two variables need to be completed to use the gdbinit file :

+ `$flash_base`, to a value corresponding to the executable XIPFS file to be debugged,
+ `$ram_base`, to the beginning of the RAM of the development board.

Then, the file can be loaded :

+ at startup as follows, '`arm-none-eabi-gdb -x path_to/build/gdbinit`'
+ later on in `gdb` by entering '`source path_to/build/gdbinit`'

With this file, both CRT0 and your own code can be debugged.

## How to inspect a FAE file off-board ?
It is possible to **retrieve information on a FAE file from a command line tool named `read_fae.py` in `fae_utils` directory.**
This tool also performs different **integrity checks and emits errors on malformed FAE files**.

Here is such an attempt on a valid FAE file :

```
$ fae_utils/read_fae.py build/hello-world.fae
- Binary size : 1152 bytes
- Magic Number And Version : 0xfacade10
- CRT0 : [start : @0 byte , end : @707 bytes] (size : 708 bytes)
- Relocation entries : [start : @712 bytes , end : @715 bytes] (size : 4 bytes)
        - Count : 1
- Entrypoint offset in .rom : 213 bytes
- .rom.ram : [start : @716 bytes , end : @719 bytes] (size : 4 bytes)
- .rom : [start : @720 bytes , end : @1051 bytes] (size : 332 bytes)
- .got : [start : @1052 bytes , end : @1107 bytes] (size : 56 bytes)
.bss : 4 bytes
- Integrity check : OK
```

**To access to `read_fae.py`'s options**, please enter simply :

```
$ fae_utils/read_fae.py
usage: fae_utils/read_fae.py [-Dcrt0, -Hcrt0, -Hreloc, -Hromram, -Drom, -Hrom, -Hgot, -v] FAEFilename

--Dcrt0 : will disassemble CRT0
--Hcrt0 : will hexdump CRT0
--Hreloc : will hexdump relocation table
--Hromram : will hexdump rom_ram section aka data
--Drom : will disassemble rom section aka text
--Hrom : will hexdump rom section aka text
--Hgot : will hexdump GOT
--v : will enable all options
```

**Hexdump options** will display an `hexdump -C` text according to the target :

```
$ fae_utils/read_fae.py -Hrom build/hello-world.fae
- Binary size : 1152 bytes
- Magic Number And Version : 0xfacade10
- CRT0 : [start : @0 byte , end : @707 bytes] (size : 708 bytes)
- Relocation entries : [start : @712 bytes , end : @715 bytes] (size : 4 bytes)
        - Count : 1
- Entrypoint offset in .rom : 213 bytes
- .rom.ram : [start : @716 bytes , end : @719 bytes] (size : 4 bytes)
- .rom : [start : @720 bytes , end : @1051 bytes] (size : 332 bytes)
00000000  17 20 70 47 20 20 70 47  13 b5 1a 4b 01 28 5a f8  |. pG  pG...K.(Z.|
00000010  03 30 03 dd 18 4a 5a f8  02 20 1a 60 1b 68 98 47  |.0...JZ.. .`.h.G|
00000020  16 4b 5a f8 03 10 16 4b  01 91 04 46 5a f8 03 00  |.KZ....K...FZ...|
00000030  00 f0 3c f8 13 4b 01 a9  5a f8 03 00 00 f0 36 f8  |..<..K..Z.....6.|
00000040  11 4b 5a f8 03 10 11 4b  5a f8 03 00 00 f0 2e f8  |.KZ....KZ.......|
00000050  0f 4b 5a f8 03 10 0f 4b  5a f8 03 00 00 f0 26 f8  |.KZ....KZ.....&.|
00000060  0d 4b 03 21 5a f8 03 00  00 f0 20 f8 20 46 02 b0  |.K.!Z..... . F..|
00000070  10 bd 00 bf 20 00 00 00  1c 00 00 00 00 00 00 00  |.... ...........|
00000080  04 00 00 00 08 00 00 00  24 00 00 00 0c 00 00 00  |........$.......|
00000090  28 00 00 00 10 00 00 00  14 00 00 00 02 4b 5a f8  |(............KZ.|
000000a0  03 30 1b 68 1b 68 18 47  18 00 00 00 0f b4 07 b5  |.0.h.h.G........|
000000b0  07 4b 5a f8 03 30 04 a9  1b 68 51 f8 04 0b 5b 68  |.KZ..0...hQ...[h|
000000c0  01 91 98 47 03 b0 5d f8  04 eb 04 b0 70 47 00 bf  |...G..].....pG..|
000000d0  18 00 00 00 08 b5 07 4b  5a f8 03 30 00 f5 a3 62  |.......KZ..0...b|
000000e0  00 f5 83 61 d0 f8 14 04  1a 60 ff f7 8d ff ff f7  |...a.....`......|
000000f0  d5 ff fe e7 18 00 00 00  68 65 6c 6c 6f 20 77 6f  |........hello wo|
00000100  72 6c 64 20 21 00 40 73  74 72 69 6e 67 20 3d 20  |rld !.@string = |
00000110  25 70 0a 00 40 26 73 74  72 69 6e 67 20 3d 20 25  |%p..@&string = %|
00000120  70 0a 00 40 26 6d 61 69  6e 20 3d 20 25 70 0a 00  |p..@&main = %p..|
00000130  26 63 73 74 20 3d 20 25  70 0a 00 63 73 74 20 3d  |&cst = %p..cst =|
00000130  26 63 73 74 20 3d 20 25  70 0a 00 63              |&cst = %p..c    |
- .got : [start : @1052 bytes , end : @1107 bytes] (size : 56 bytes)
.bss : 4 bytes
- Integrity check : OK
```

**Disassembly options** will use `arm-none-eabi-objdump` under the hood to provide output :

```
- Binary size : 1152 bytes
- Magic Number And Version : 0xfacade10
- CRT0 : [start : @0 byte , end : @707 bytes] (size : 708 bytes)
- Relocation entries : [start : @712 bytes , end : @715 bytes] (size : 4 bytes)
        - Count : 1
- Entrypoint offset in .rom : 213 bytes
- .rom.ram : [start : @716 bytes , end : @719 bytes] (size : 4 bytes)
- .rom : [start : @720 bytes , end : @1051 bytes] (size : 332 bytes)

/tmp/tmppybpuh4v/.rom:     file format binary


Disassembly of section .data:

00000000 <.data>:
   0:   2017            movs    r0, #23
   2:   4770            bx      lr
   4:   2020            movs    r0, #32
   6:   4770            bx      lr
   8:   b513            push    {r0, r1, r4, lr}
   a:   4b1a            ldr     r3, [pc, #104]  @ (0x74)
   c:   2801            cmp     r0, #1
   e:   f85a 3003       ldr.w   r3, [sl, r3]
  12:   dd03            ble.n   0x1c
  14:   4a18            ldr     r2, [pc, #96]   @ (0x78)
  16:   f85a 2002       ldr.w   r2, [sl, r2]
  1a:   601a            str     r2, [r3, #0]
  1c:   681b            ldr     r3, [r3, #0]
  1e:   4798            blx     r3
  20:   4b16            ldr     r3, [pc, #88]   @ (0x7c)
  22:   f85a 1003       ldr.w   r1, [sl, r3]
  26:   4b16            ldr     r3, [pc, #88]   @ (0x80)
  28:   9101            str     r1, [sp, #4]
  2a:   4604            mov     r4, r0
  2c:   f85a 0003       ldr.w   r0, [sl, r3]
  30:   f000 f83c       bl      0xac
  34:   4b13            ldr     r3, [pc, #76]   @ (0x84)
  36:   a901            add     r1, sp, #4
  38:   f85a 0003       ldr.w   r0, [sl, r3]
  3c:   f000 f836       bl      0xac
  40:   4b11            ldr     r3, [pc, #68]   @ (0x88)
  42:   f85a 1003       ldr.w   r1, [sl, r3]
  46:   4b11            ldr     r3, [pc, #68]   @ (0x8c)
  48:   f85a 0003       ldr.w   r0, [sl, r3]
  4c:   f000 f82e       bl      0xac
  50:   4b0f            ldr     r3, [pc, #60]   @ (0x90)
  52:   f85a 1003       ldr.w   r1, [sl, r3]
  56:   4b0f            ldr     r3, [pc, #60]   @ (0x94)
  58:   f85a 0003       ldr.w   r0, [sl, r3]
  5c:   f000 f826       bl      0xac
  60:   4b0d            ldr     r3, [pc, #52]   @ (0x98)
  62:   2103            movs    r1, #3
  64:   f85a 0003       ldr.w   r0, [sl, r3]
  68:   f000 f820       bl      0xac
  6c:   4620            mov     r0, r4
  6e:   b002            add     sp, #8
  70:   bd10            pop     {r4, pc}
  72:   bf00            nop
  74:   0020            movs    r0, r4
  76:   0000            movs    r0, r0
  78:   001c            movs    r4, r3
  7a:   0000            movs    r0, r0
  7c:   0000            movs    r0, r0
  7e:   0000            movs    r0, r0
  80:   0004            movs    r4, r0
  82:   0000            movs    r0, r0
  84:   0008            movs    r0, r1
  86:   0000            movs    r0, r0
  88:   0024            movs    r4, r4
  8a:   0000            movs    r0, r0
  8c:   000c            movs    r4, r1
  8e:   0000            movs    r0, r0
  90:   0028            movs    r0, r5
  92:   0000            movs    r0, r0
  94:   0010            movs    r0, r2
  96:   0000            movs    r0, r0
  98:   0014            movs    r4, r2
  9a:   0000            movs    r0, r0
  9c:   4b02            ldr     r3, [pc, #8]    @ (0xa8)
  9e:   f85a 3003       ldr.w   r3, [sl, r3]
  a2:   681b            ldr     r3, [r3, #0]
  a4:   681b            ldr     r3, [r3, #0]
  a6:   4718            bx      r3
  a8:   0018            movs    r0, r3
  aa:   0000            movs    r0, r0
  ac:   b40f            push    {r0, r1, r2, r3}
  ae:   b507            push    {r0, r1, r2, lr}
  b0:   4b07            ldr     r3, [pc, #28]   @ (0xd0)
  b2:   f85a 3003       ldr.w   r3, [sl, r3]
  b6:   a904            add     r1, sp, #16
  b8:   681b            ldr     r3, [r3, #0]
  ba:   f851 0b04       ldr.w   r0, [r1], #4
  be:   685b            ldr     r3, [r3, #4]
  c0:   9101            str     r1, [sp, #4]
  c2:   4798            blx     r3
  c4:   b003            add     sp, #12
  c6:   f85d eb04       ldr.w   lr, [sp], #4
  ca:   b004            add     sp, #16
  cc:   4770            bx      lr
  ce:   bf00            nop
  d0:   0018            movs    r0, r3
  d2:   0000            movs    r0, r0
  d4:   b508            push    {r3, lr}
  d6:   4b07            ldr     r3, [pc, #28]   @ (0xf4)
  d8:   f85a 3003       ldr.w   r3, [sl, r3]
  dc:   f500 62a3       add.w   r2, r0, #1304   @ 0x518
  e0:   f500 6183       add.w   r1, r0, #1048   @ 0x418
  e4:   f8d0 0414       ldr.w   r0, [r0, #1044] @ 0x414
  e8:   601a            str     r2, [r3, #0]
  ea:   f7ff ff8d       bl      0x8
  ee:   f7ff ffd5       bl      0x9c
  f2:   e7fe            b.n     0xf2
  f4:   0018            movs    r0, r3
  f6:   0000            movs    r0, r0
  f8:   6568            str     r0, [r5, #84]   @ 0x54
  fa:   6c6c            ldr     r4, [r5, #68]   @ 0x44
  fc:   206f            movs    r0, #111        @ 0x6f
  fe:   6f77            ldr     r7, [r6, #116]  @ 0x74
 100:   6c72            ldr     r2, [r6, #68]   @ 0x44
 102:   2064            movs    r0, #100        @ 0x64
 104:   0021            movs    r1, r4
 106:   7340            strb    r0, [r0, #13]
 108:   7274            strb    r4, [r6, #9]
 10a:   6e69            ldr     r1, [r5, #100]  @ 0x64
 10c:   2067            movs    r0, #103        @ 0x67
 10e:   203d            movs    r0, #61 @ 0x3d
 110:   7025            strb    r5, [r4, #0]
 112:   000a            movs    r2, r1
 114:   2640            movs    r6, #64 @ 0x40
 116:   7473            strb    r3, [r6, #17]
 118:   6972            ldr     r2, [r6, #20]
 11a:   676e            str     r6, [r5, #116]  @ 0x74
 11c:   3d20            subs    r5, #32
 11e:   2520            movs    r5, #32
 120:   0a70            lsrs    r0, r6, #9
 122:   4000            ands    r0, r0
 124:   6d26            ldr     r6, [r4, #80]   @ 0x50
 126:   6961            ldr     r1, [r4, #20]
 128:   206e            movs    r0, #110        @ 0x6e
 12a:   203d            movs    r0, #61 @ 0x3d
 12c:   7025            strb    r5, [r4, #0]
 12e:   000a            movs    r2, r1
 130:   6326            str     r6, [r4, #48]   @ 0x30
 132:   7473            strb    r3, [r6, #17]
 134:   3d20            subs    r5, #32
 136:   2520            movs    r5, #32
 138:   0a70            lsrs    r0, r6, #9
 13a:   6300            str     r0, [r0, #48]   @ 0x30
 13c:   7473            strb    r3, [r6, #17]
 13e:   3d20            subs    r5, #32
 140:   2520            movs    r5, #32
 142:   0a64            lsrs    r4, r4, #9
 144:   0000            movs    r0, r0
 146:   0000            movs    r0, r0
 148:   0003            movs    r3, r0
        ...

- .got : [start : @1052 bytes , end : @1107 bytes] (size : 56 bytes)
.bss : 4 bytes
- Integrity check : OK
```
