#!/usr/bin/env python
import os
import sys
import json
import time
import argparse
import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

if not os.path.exists("third_party/appdirs/appdirs.py") or not os.path.exists("third_party/progressbar/progressbar"):
    print("Uuuh!1 Can't find appdirs or progressbar module, did you load git submodules?!")
    sys.exit(1)

sys.path.append("third_party/appdirs")
sys.path.append("third_party/progressbar")
from appdirs import user_data_dir

from sky3ds import disk, gamecard, titles

try:
    data_dir = user_data_dir('sky3ds', 'Aperture Laboratories')
    template_txt = os.path.join(data_dir, 'template.txt')
    template_json = os.path.join(data_dir, 'template.json')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if not os.path.exists(template_txt):
        print("Please put template.txt in %s" % data_dir)
        sys.exit(1)
    if not os.path.exists(template_json) or time.ctime(os.path.getmtime(template_txt)) > time.ctime(os.path.getmtime(template_json)):
        print("Found updated template.txt. Converting...")
        titles.convert_template_to_json()

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--disk', help='Sky3DS disk')

    parser.add_argument('-l', '--list', help='List roms on disk (default operation)', action='store_true')
    parser.add_argument('-v', '--verbose', help='More details', action='store_true')
    parser.add_argument('-w', '--write', help='Write rom to disk')
    parser.add_argument('-H', '--do-not-use-header-bin', help='Ignore header.bin', action='store_true')
    parser.add_argument('-b', '--backup', help='Backup rom from disk')
    parser.add_argument('-r', '--remove', help='Remove rom from disk')

    parser.add_argument('-W', '--write-savegame', help='Write savegame to disk')
    parser.add_argument('-B', '--backup-savegame', help='Backup savegame from disk')
#    parser.add_argument('-R', '--erase-savegame', help='Erase savegame from disk')
    parser.add_argument('-Z', '--backup-all-savegames', help='Backup all savegames', action='store_true')

    parser.add_argument('-s', '--slot', help='Slot ID for --backup and --backup-savegame')

    parser.add_argument('-f', '--format', help='Format disk', action="store_true")
    parser.add_argument('-c', '--confirm-format', action="store_true")

    parser.add_argument('-u', '--update', help='Update title database', action='store_true')
    args = parser.parse_args()

    if not args.disk and not args.update:
        print("No disk specified.")
        sys.exit(1)

    disk = disk.Sky3DS_Disk(args.disk)

    if (args.backup != None) + (args.write != None) + (args.remove != None) + (args.backup_savegame != None) + (args.write_savegame != None) + args.format + args.backup_all_savegames + args.update > 1:
        print("Please specify only one operation.")
        sys.exit(1)

    if args.format:
        if not args.confirm_format:
            print("Please confirm format operation with '-c'.")
            sys.exit(1)
        disk.format()

    if not args.update and not disk.is_sky3ds_disk:
        print("This is not a sky3ds disk. Aborting.")
        sys.exit(1)

    if args.remove != None:
        args.remove = int(args.remove)
        if args.remove in [i[0] for i in disk.rom_list]:
            disk.delete_rom(args.remove)
            print("Removed rom from slot %d" % args.remove)

    if args.update:
        titles.update_title_db()

    if args.backup != None and args.slot == None:
        print("Please specify slot")
        sys.exit(1)
    elif args.backup != None and args.slot != None:
        disk.dump_rom(int(args.slot), args.backup)

    if args.backup_savegame != None and args.slot == None:
        print("Please specify slot")
        sys.exit(1)
    elif args.backup_savegame != None and args.slot != None:
        disk.dump_savegame(int(args.slot), args.backup_savegame)

    if args.write_savegame != None:
        disk.write_savegame(args.write_savegame)

    if args.write != None:
        disk.write_rom(args.write, use_header_bin=not args.do_not_use_header_bin, verbose=args.verbose)

    rom_table = [['Slot', 'Start', 'Size', 'Type', 'Code', 'Title']]
    if args.verbose:
        rom_table[0] += ['Sav-Crypt', 'Firm', 'Card ID', 'Unique ID']

    if args.backup_all_savegames:
        for rom in disk.rom_list:
            slot = rom[0]
            rom_header = disk.ncsd_header(slot)
            rom_info = titles.rom_info(rom_header['product_code'], rom_header['media_id'])

            savegames_dir = os.path.join(data_dir, 'savegames')

            if not os.path.exists(savegames_dir):
                os.mkdir(savegames_dir)

            savegame_dir = os.path.join(savegames_dir, ''.join(filter(lambda x: x in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-+& ', rom_info['name'])))

            if not os.path.exists(savegame_dir):
                os.mkdir(savegame_dir)

            savegame_file = os.path.join(savegame_dir, "%s_%s.sav" % (rom_header['product_code'], datetime.datetime.now().strftime("%Y_%m_%d__%H_%M")))
            disk.dump_savegame(slot, savegame_file)

    for rom in disk.rom_list:
        slot = rom[0]
        start = rom[1]
        size = rom[2]
        rom_header = disk.ncsd_header(slot)
        sky3ds_header = disk.sky3ds_header(slot)
        card_id = " ".join("%.2x" % x for x in sky3ds_header[0x04:0x08]).upper()
        unique_id = " ".join("%.2x" % x for x in sky3ds_header[0x40:0x50]).upper()
        rom_info = titles.rom_info(rom_header['product_code'], rom_header['media_id'])
        if rom_info:
            title = rom_info['name']
            firmware = rom_info['firmware']
        else:
            title = "???"
            firmware = "???"
        rom_table += [[
            slot,
            "%d MB" % int(rom[1] / 1024 / 1024),
            "%d MB" % int(rom[2] / 1024 / 1024),
            rom_header['card_type'],
            rom_header['product_code'],
            title,
            ]]
        if args.verbose:
            rom_table[-1] += [
                rom_header['save_crypto'].rjust(9),
                firmware,
                card_id,
                unique_id,
            ]

    col_width = [max(len(str(x)) for x in col) for col in zip(*rom_table)]
    for line in rom_table:
        print("| " + " | ".join("{:{}}".format(x, col_width[i]) for i, x in enumerate(line)) + " |")

    print("")
    total_free_blocks = sum(512*i[1] for i in disk.free_blocks)

    print("Disk Size: %d MB | Free space: %d MB | Largest free continous space: %d MB" % (disk.disk_size/1024/1024, total_free_blocks/1024/1024, 512 * disk.free_blocks[0][1]/1024/1024))
except Exception as e:
    logging.error(e)
