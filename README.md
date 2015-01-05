sky3ds.py
=========

This is a python cli clone of Sky3DS DiskWriter.

It works for me, but there may be some flaws and it is still in development so things may change, so use with caution.

## Switches

| Short | Long | Description |
| ----- | ---- | ----------- |
| -h | --help | Show help message |
| -d sdcard | --disk sdcard | Path to Sky3DS sdcard (e.g. /dev/mmcblk0) |
| -l | --list | List roms on sdcard |
| -w rom.3ds | --write rom.3ds | Write rom to sdcard |
| -b rom.3ds | --backup rom.3ds | Backup rom from sdcard |
| -r #slot | --remove #slot | Remove game in specified slot |
| -W save.sav | --write-savegame save.sav | Write savegame backup to sdcard |
| -B save.sav | --backup-savegame save.sav | Backup savegame from sdcard |
| -s #slot | --slot #slot | Slot (required for --backup and --backup-savegame) |
| -f | --format | Format sdcard |
| -c | --confirm-format | Confirm format sdcard |
| -u | --update | Update title database (game titles, not template.txt) |

Slot IDs may be retrieved with the ```--list``` option. Keep in mind that Slot IDs may change after deleting a game.
