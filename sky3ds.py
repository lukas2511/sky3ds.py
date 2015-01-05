#!/usr/bin/env python3
import os
import sys
import json
import time
import argparse

from appdirs import user_data_dir
from progressbar import FileTransferSpeed, ProgressBar, Percentage, Bar
import disk
import gamecard
import titles

if __name__ == '__main__':
    data_dir = user_data_dir('sky3ds', 'Aperture Laboratories')
    template_txt = os.path.join(data_dir, 'template.txt')
    template_json = os.path.join(data_dir, 'template.json')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if not os.path.exists(template_txt):
        print("Please put template.txt in %s" % data_dir)
        sys.exit(1)
    if not os.path.exists(template_json) or time.ctime(os.path.getmtime(template_txt)) > time.ctime(os.path.getmtime(template_json)):
        titles.convert_template_to_json()

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--disk', help='Sky3DS disk')

    parser.add_argument('-l', '--list', help='List roms on disk', action="store_true")
    parser.add_argument('-w', '--write', help='Write rom to disk')
    parser.add_argument('-b', '--backup', help='Backup rom from disk')
    parser.add_argument('-r', '--remove', help='Remove rom from disk')

    parser.add_argument('-W', '--write-savegame', help='Write savegame to disk')
    parser.add_argument('-B', '--backup-savegame', help='Backup savegame from disk')
    parser.add_argument('-R', '--erase-savegame', help='Erase savegame from disk')

    parser.add_argument('-s', '--slot', help='Slot ID for --backup and --backup-savegame')

    parser.add_argument('-f', '--format', help='Format disk', action="store_true")
    parser.add_argument('-c', '--confirm-format', action="store_true")

    parser.add_argument('-u', '--update', help='Update title database', action='store_true')

    parser.add_argument('-t', '--test', action="store_true")
    args = parser.parse_args()

    if not args.disk and not args.update:
        print("No disk specified.")
        sys.exit(1)

    if (args.backup != None) + (args.write != None) + (args.remove != None) + (args.backup_savegame != None) + (args.write_savegame != None) + (args.erase_savegame != None) + args.list + args.format + args.test + args.update != 1:
        print("Please specify exactly one operation.")
        sys.exit(1)

    if args.format:
        if not args.confirm_format:
            print("Please confirm format operation with '-c'.")
            sys.exit(1)
        disk.format(args.disk)

    if not args.update and not disk.check_if_sky3ds_disk(args.disk):
        print("This is not a sky3ds disk. Aborting.")
        sys.exit(1)

    if args.test:
        disk.write_savegame(args.disk, 1, bytearray([0xff]*0x00100000))
        disk.write_savegame(args.disk, 2, bytearray([0xff]*0x00100000))

    if args.remove != None:
        rom_list = disk.get_rom_list(args.disk)
        args.remove = int(args.remove)
        if args.remove in [i[0] for i in rom_list]:
            disk.delete_rom(args.disk, args.remove)
            print("Removed rom from slot %d" % args.remove)

    if args.list:
        rom_list = disk.get_rom_list(args.disk)
        diskfp = open(args.disk, "rb")
        rom_table = [['Slot', 'Start', 'Size', 'Type', 'Code', 'Title']]
        for rom in rom_list:
            slot = rom[0]
            start = rom[1]
            size = rom[2]
            diskfp.seek(start)
            rom_header = gamecard.ncsd_header(diskfp.read(0x1200))
            rom_info = titles.rom_info(rom_header['product_code'], rom_header['media_id'])
            if rom_info:
                title = rom_info['name']
            else:
                title = "???"
            rom_table += [[
                slot,
                "%d MB" % int(rom[1] / 1024 / 1024),
                "%d MB" % int(rom[2] / 1024 / 1024),
                rom_header['card_type'],
                rom_header['product_code'],
                title,
                ]]

        col_width = [max(len(str(x)) for x in col) for col in zip(*rom_table)]
        for line in rom_table:
            print("| " + " | ".join("{:{}}".format(x, col_width[i]) for i, x in enumerate(line)) + " |")

        print("")
        free_blocks = disk.get_free_blocks(args.disk)
        total_free_blocks = sum(512*i[1] for i in free_blocks)
        disk_size = disk.get_disk_size(args.disk)

        print("Disk Size: %d MB | Free space: %d MB | Largest free continous space: %d MB" % (disk_size/1024/1024, total_free_blocks/1024/1024, 512 * free_blocks[0][1]/1024/1024))

    if args.update:
        titles.update_title_db()

    if args.backup != None and args.slot == None:
        print("Please specify slot")
        sys.exit(1)
    elif args.backup != None and args.slot != None:
        disk.dump_rom(args.disk, int(args.slot), args.backup)

    if args.backup_savegame != None and args.slot == None:
        print("Please specify slot")
        sys.exit(1)
    elif args.backup_savegame != None and args.slot != None:
        disk.dump_savegame(args.disk, int(args.slot), args.backup_savegame)

    if args.write_savegame != None:
        disk.write_savegame(args.disk, args.write_savegame)

    if args.write != None:
        disk.write_rom(args.disk, args.write)


