# Copyright (C) 2024 Université de Lille
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

PREFIX          = arm-none-eabi-
CC              = $(PREFIX)gcc
LD              = $(PREFIX)gcc

CFLAGS          = -Wall
CFLAGS         += -Wextra
CFLAGS         += -Werror
CFLAGS         += -mthumb
CFLAGS         += -mcpu=cortex-m4
CFLAGS         += -mfloat-abi=hard
CFLAGS         += -mfpu=fpv4-sp-d16
CFLAGS         += -msingle-pic-base
CFLAGS         += -mpic-register=sl
CFLAGS         += -mno-pic-data-is-text-relative
CFLAGS         += -fPIC
CFLAGS         += -ffreestanding
ifdef DEBUG
CFLAGS         += -Og
CFLAGS         += -ggdb
else
CFLAGS         += -Os
endif
CFLAGS         += -Wno-unused-parameter
CFLAGS         += -Istdriot

LDFLAGS         = -nostartfiles
LDFLAGS        += -nodefaultlibs
LDFLAGS        += -nolibc
LDFLAGS        += -nostdlib
LDFLAGS        += -Tlink.ld
LDFLAGS        += -Wl,-q
# Disable the new linker warning '--warn-rwx-segments' introduced by
# Binutils 2.39, which causes the following message: "warning:
# $(TARGET).elf has a LOAD segment with RWX permissions".
ifeq ($(shell $(PREFIX)ld --help | grep -q 'warn-rwx-segments'; echo $$?), 0)
LDFLAGS        += -Wl,--no-warn-rwx-segments
endif


TARGET          = hello-world

all: build/$(TARGET).fae

build :
	mkdir -p build

build/$(TARGET).fae: build/$(TARGET).elf
	./fae_utils/build_fae.py $<
	@chmod 644 $@

build/$(TARGET).elf: build/main.o build/stdriot.o
	$(LD) $(LDFLAGS) $^ -o $@

build/stdriot.o: stdriot/stdriot.c stdriot/stdriot.h | build
	$(CC) $(CFLAGS) -c $< -o $@

build/main.o: main.c | build
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	$(RM) build/main.o build/stdriot.o
	make -C crt0 clean

realclean: clean
	$(RM) -rf build

.PHONY: all clean realclean
