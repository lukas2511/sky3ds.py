#!/usr/bin/env python3
import hashlib
import struct
import json
import sys
import os

def ncch_sha1sum(backupfp):
    backupfp.seek(0x1000)
    header = backupfp.read(0x200)
    return hashlib.sha1(header).hexdigest()

def ncsd_serial(backupfp):
    backupfp.seek(0x1150)
    serial = backupfp.read(0xa)
    return serial.decode("ascii")

def ncsd_header(raw_header_data):
    ncsd_header = {
        'sha256sig': raw_header_data[0x0:0x100],
        'ncsd': raw_header_data[0x100:0x104],
        'size': struct.unpack("i", raw_header_data[0x104:0x108])[0] * 0x200,
        'media_id': "%016x".upper() % struct.unpack("q", (raw_header_data[0x108:0x110])),
        'fs_type': raw_header_data[0x110:0x118],
        'crypt_type': raw_header_data[0x118:0x120],
        'partition_table': raw_header_data[0x120:0x160],
        'exheader': raw_header_data[0x160:0x180],
        'header_size': raw_header_data[0x180:0x184],
        'zero_offset': raw_header_data[0x184:0x188],
        'partition_flags': raw_header_data[0x188:0x190],
        'partition_id': raw_header_data[0x190:0x1d0],
        'reserved': raw_header_data[0x1d0:0x200],
    }
    if not ncsd_header['ncsd'].decode('ascii') == "NCSD":
        return False

    card_info_header = {
        'writable_address': struct.unpack("i", raw_header_data[0x200:0x204])[0] * 0x200,
        'card_info_bitmask': raw_header_data[0x204:0x208],
        'reserved1': raw_header_data[0x208:0x1000],
        'media_id_1': "%016x".upper() % struct.unpack("q", (raw_header_data[0x1000:0x1008])),
        'reserved2': raw_header_data[0x1008:0x1010],
        'ncch_header': {
            'ncch': raw_header_data[0x1100:0x1104],
            'size': struct.unpack("i", raw_header_data[0x1104:0x1108])[0] * 0x200,
            'partition_id': raw_header_data[0x1108:0x1110],
            'maker_code': raw_header_data[0x1110:0x1112],
            'version': raw_header_data[0x1112:0x1114],
            'reserved1': raw_header_data[0x1114:0x1118],
            'program_id': raw_header_data[0x1118:0x1120],
            'reserved2': raw_header_data[0x1120:0x1130],
            'logo_region_hash': raw_header_data[0x1130:0x1150],
            'product_code': raw_header_data[0x1150:0x1160].decode('ascii').rstrip('\0'),
            # ...
            'flags': raw_header_data[0x1188:0x1190],
            # ...
        },
    }

    part_flags = ncsd_header['partition_flags']

    if part_flags[3] > 0:
        if part_flags[1] > 0:
            save_crypto = ">6.x"
        else:
            save_crypto = "<6.x"
    else:
        save_crypto = "Repeat. Fail"

    contains_update = True if card_info_header['ncch_header']['flags'][5] & (1 << 2) else False
    #save_crypto += str(part_flags)

    return {
            'size': ncsd_header['size'],
            'media_id': ncsd_header['media_id'],
            'product_code': card_info_header['ncch_header']['product_code'],
            'card_type': ['Inner Device', 'Card1', 'Card2', 'Extended Device'][int(ncsd_header['partition_flags'][5])],
            'writable_address': card_info_header['writable_address'],
            'save_crypto': save_crypto,
            'contains_update': contains_update,
            }

