from sky3ds.disk import Sky3DS_Disk
import unittest
import filecmp

class Sky3DS_Disk_Test(unittest.TestCase):
    disk = None

    @classmethod
    def setUpClass(self):
        # create dummy file
        dummyfile = open("test.img","wb")
        dummyfile.seek(512*1024*1024)
        dummyfile.write(bytearray("yo", "ascii"))
        dummyfile.close()

    @classmethod
    def test_0_open(self):
        self.disk = Sky3DS_Disk("test.img")

    def test_1_is_sky3ds_disk_before(self):
        if self.disk.is_sky3ds_disk:
            raise Exception("'ROMS'-String check doesn't work correctly - should be False")

        if not len(self.disk.rom_list) == 0 or not len(self.disk.free_blocks) == 0:
            raise Exception("Rom slot detection and/or free-blocks detection broken")

    def test_2_format(self):
        self.disk.format()

    def test_3_is_sky3ds_disk_after_format(self):
        if not self.disk.is_sky3ds_disk:
            raise Exception("'ROMS'-String check doesn't work correctly - should be True")

        if not len(self.disk.rom_list) == 0 or not len(self.disk.free_blocks) == 1:
            raise Exception("Rom slot detection and/or free-blocks detection broken")

    @classmethod
    def test_4_open(self):
        self.disk = Sky3DS_Disk("test.img")

    def test_5_is_sky3ds_disk_after_reopen(self):
        if not self.disk.is_sky3ds_disk:
            raise Exception("'ROMS'-String check doesn't work correctly - should be True")

        if not len(self.disk.rom_list) == 0 or not len(self.disk.free_blocks) == 1:
            raise Exception("Rom slot detection and/or free-blocks detection broken")

    def test_6_write_rom(self):
        self.disk.write_rom("test.3ds", silent=True)
        if not len(self.disk.rom_list) == 1:
            raise Exception("Rom not written correctly or slot detection broken")

        self.disk.dump_rom(0, "test_restore.3ds", silent=True)
        if not filecmp.cmp("test.3ds", "test_restore.3ds"):
            raise Exception("Rom not written or dumped correctly")

    def test_7_dump_savegame(self):
        self.disk.dump_savegame(0, "test.sav")

    def test_8_restore_savegame(self):
        self.disk.write_savegame("test.sav")

    def test_9_delete_rom(self):
        self.disk.delete_rom(0)

        if not len(self.disk.rom_list) == 0:
            raise Exception("Rom not deleted correctly or slot detection broken")

if __name__ == '__main__':
        unittest.main()

