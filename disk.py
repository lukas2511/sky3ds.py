#!/usr/bin/env python3
import sys
import os
import struct
from progressbar import FileTransferSpeed, ProgressBar, Percentage, Bar

import gamecard
import titles

def format(disk):
    empty_img = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'empty.img')
    fatfp = open(empty_img, "rb")
    size = os.path.getsize(empty_img)

    diskfp = open(disk, "r+b")

    # write data from empty.img to sdcard (easy way to "format" the card)
    written = 0
    while written < size:
        chunk = fatfp.read(1024*1024)

        diskfp.write(chunk)
        os.fsync(diskfp)

        written = written + len(chunk)

    # erase savegame slots
    for i in range(1, 32):
        diskfp.seek(i * 0x100000)
        diskfp.write(bytearray([0xff] * 0x100000))

    fatfp.close()
    diskfp.close()

def get_rom_list(disk):
    # read slot headers on sd-card and return positions and sizes of roms
    diskfp = open(disk, "rb")
    position_header_length = 0x100
    raw_positions = diskfp.read(position_header_length)
    positions = []
    for i in range(0, int(position_header_length / 8)):
        position = struct.unpack("ii", raw_positions[i*8:i*8+8])
        if position[0] > 0 and position[1] > 0:
            positions += [[len(positions)] + [i*512 for i in position]]
    return positions

def get_disk_size(disk):
    # this is a workaround to get the size of the sd-card system independent
    # we basically seek to the end of the card and read how many bytes
    # were skipped
    diskfd = os.open(disk, os.O_RDONLY)
    disk_size = os.lseek(diskfd, 0, os.SEEK_END)
    disk_size = disk_size - disk_size % 0x2000000
    os.close(diskfd)
    return disk_size

def get_free_blocks(disk):
    # this function uses 32MB blocks instead of 512B sectors
    # to improve performance (a lot!)

    rom_list = get_rom_list(disk)
    disk_size = get_disk_size(disk)
    max_blocks = int(disk_size / 0x2000000)

    # create a map like ['X', ' ', ' ', 'X', 'X']
    # where 'X' is used space and ' ' is free space
    block_map = ['X'] + [' ']*(max_blocks-0x1)
    for rom in rom_list:
        start = int(rom[1] / 0x2000000)
        size = int(rom[2] / 0x2000000)
        end = start + size
        for i in range(start, end):
            block_map[i] = 'X'

    # inside the map find sequences of ' ' (free space)
    free_blocks = []
    start_block = 0
    i = 0
    for block in block_map:
        if block == ' ' and start_block == 0:
            start_block = i
        elif block == 'X' and not start_block == 0:
            free_blocks += [[ start_block, i - start_block ]]
            start_block = 0

        i+=1
    if not start_block == 0:
        free_blocks += [[ start_block, i - start_block ]]

    # sort sequences of free space by length (descending, useful for later stuff)
    free_blocks = sorted(free_blocks, key=lambda x: x[1], reverse=True)
    free_blocks = [[i*0x10000,j*0x10000] for i,j in free_blocks]

    return free_blocks

def write_rom(disk, rom):
    # get rom size and calculate block count
    rom_size = os.path.getsize(rom)
    rom_blocks = int(rom_size / 0x200)

    # get free blocks on sd-card and search for a block big enough for the rom
    free_blocks = get_free_blocks(disk)[::-1]
    start_block = 0
    for free_block in free_blocks:
        if free_block[1] >= rom_blocks:
            start_block = free_block[0]
            break

    if start_block == 0:
        print("Error: Not enough free continous blocks")
        return

    diskfp = open(disk, "r+b")
    position_header_length = 0x100

    # find free slot for game (card format is limited to 31 games)
    free_slot = -1
    for i in range(0, int(position_header_length / 0x8)):
        position = struct.unpack("ii", diskfp.read(0x8))
        if position == (-1, -1):
            free_slot = i
            break

    if free_slot == -1:
        print("Error: No free slot found. There can be a maximum of %d games on one card." % int(position_header_length / 0x8))
        return

    # seek to start of rom on sd-card
    diskfp.seek(start_block * 0x200)

    romfp = open(rom, "rb")

    # write rom (with fancy progressbar!)
    progress = ProgressBar(widgets=[Percentage(), Bar(), FileTransferSpeed()], maxval=rom_size).start()
    written = 0
    while written < rom_size:
        chunk = romfp.read(1024*1024)

        diskfp.write(chunk)
        os.fsync(diskfp)

        written = written + len(chunk)
        progress.update(written)
    progress.finish()

    # seek to slot header and write position + block-count of rom
    diskfp.seek(free_slot * 0x8)
    diskfp.write(struct.pack("ii", start_block, rom_blocks))

    # add savegame slot
    diskfp.seek(0x100000 * (1 + len(get_rom_list(disk))))
    diskfp.write(bytearray([0xff]*0x100000))

    # write data from template.txt to position 0x1400 in rom on sd-card
    serial = gamecard.ncsd_serial(rom)
    sha1 = gamecard.ncch_sha1sum(rom)
    template_data = titles.get_template(serial, sha1)
    card_data = bytes.fromhex(template_data['card_data'])
    diskfp.seek(start_block * 0x200 + 0x1400)
    diskfp.write(card_data)

    # cleanup
    romfp.close()
    os.fsync(diskfp)
    diskfp.close()

def dump_rom(disk, slot, output):
    rom_list = get_rom_list(disk)
    start = rom_list[slot][1]
    rom_size = rom_list[slot][2]

    diskfp = open(disk, "r+b")
    diskfp.seek(start)

    outputfp = open(output, "wb")

    # dump rom (with fancy progressbar!)
    progress = ProgressBar(widgets=[Percentage(), Bar(), FileTransferSpeed()], maxval=rom_size).start()
    written = 0
    while written < rom_size:
        chunk = diskfp.read(1024*1024)

        outputfp.write(chunk)
        os.fsync(outputfp)

        written = written + len(chunk)
        progress.update(written)
    progress.finish()

    # remove data at 0x1400
    outputfp.seek(0x1400)
    outputfp.write(bytearray([0xff]*0x200))

    # cleanup
    diskfp.close()
    os.fsync(outputfp)
    outputfp.close()

def delete_rom(disk, slot):
    diskfp = open(disk, "r+b")

    # remove savegame and rearrange the rest of the savegames
    current_save = slot

    while current_save < len(get_rom_list(disk)):
        diskfp.seek(0x100000 * (current_save + 2))
        tmp_savegame = diskfp.read(0x100000)
        diskfp.seek(0x100000 * (current_save + 1))
        diskfp.write(tmp_savegame)
        current_save += 1
    diskfp.write(bytearray([0xff]*0x100000))

    # remove slot header and rearrange the rest of the headers
    position_header_length = 0x100
    diskfp.seek(0x0)
    raw_positions = list(diskfp.read(position_header_length))
    new_raw_positions = bytearray(raw_positions[0:slot*8] + raw_positions[(slot+1)*8:] + [0xff]*8)
    diskfp.seek(0x0)
    diskfp.write(new_raw_positions)


def dump_savegame(disk, slot, output):
    rom_list = get_rom_list(disk)
    if slot >= len(rom_list):
        print("Slot not found")
        sys.exit(1)

    diskfp = open(disk, "rb")

    diskfp.seek(rom_list[slot][1])
    ncsd_header = gamecard.ncsd_header(diskfp.read(0x1200))

    if ncsd_header['card_type'] == 'Card1':
        savegamefp = open(output, "wb")
        savegamefp.write(b'CTR_SAVE')
        savegamefp.write(bytearray(ncsd_header['product_code'].encode('ascii')))
        savegamefp.write(bytearray([0x00]*0x2))
        savegamefp.write(bytearray([0xff]*0x44))
        diskfp.seek(0x100000 * (slot + 1))
        savegamefp.write(diskfp.read(0x100000))
        savegamefp.close()
    elif ncsd_header['card_type'] == 'Card2':
        savegamefp = open(output, "wb")
        savegamefp.write(b'CTR_SAVE')
        savegamefp.write(bytearray(ncsd_header['product_code'].encode('ascii')))
        savegamefp.write(bytearray([0x00, 0x01]))
        savegamefp.write(bytearray([0x00]*4))
        diskfp.seek(rom_list[slot][1] + 0x1440)
        savegamefp.write(diskfp.read(0x10))
        savegamefp.write(bytearray([0xff]*0x30))
        diskfp.seek(rom_list[slot][1] + ncsd_header['writable_address'])
        for i in range(0, 10):
            savegamefp.write(diskfp.read(0x100000))
        savegamefp.close()

    diskfp.close()

def find_game(disk, product_code):
    rom_list = get_rom_list(disk)
    diskfp = open(disk, "rb")
    slot = -1
    rom_count = 0
    for rom in rom_list:
        diskfp.seek(rom[1])
        ncsd_header = gamecard.ncsd_header(diskfp.read(0x1200))
        if ncsd_header['product_code'] == product_code:
            diskfp.close()
            return (rom_count, ncsd_header)
        rom_count+=1
    return (None, None)

def write_savegame(disk, savefile):
    savegamefp = open(savefile, "rb")
    ctr_save = savegamefp.read(0x8)
    if ctr_save != b'CTR_SAVE':
        print("Error: Not a valid savegame")
        sys.exit(1)

    product_code = savegamefp.read(0xa).decode('ascii')
    slot,ncsd_header = find_game(disk, product_code)

    savegamefp.read(0x46)

    if slot == None:
        print("Error: Game not on disk")
        sys.exit(1)

    diskfp = open(disk, "r+b")

    if ncsd_header['card_type'] == 'Card1':
        diskfp.seek(0x100000 * (slot + 1))
        diskfp.write(savegamefp.read(0x100000))
        os.fsync(diskfp)
    elif ncsd_header['card_type'] == 'Card2':
        rom_list = get_rom_list(disk)
        diskfp.seek(rom_list[slot][1] + ncsd_header['writable_address'])
        for i in range(0, 10):
            diskfp.write(savegamefp.read(0x100000))
            os.fsync(diskfp)

    savegamefp.close()
    diskfp.close()

def check_if_sky3ds_disk(disk):
    # check for "ROMS" signature on sd-card
    disk_data = open(disk,"rb").read(0x104)
    return b'ROMS' == disk_data[-4:]

