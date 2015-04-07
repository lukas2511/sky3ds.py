#!/usr/bin/env python2

# this script was written by somebody else, i have no idea how well it works, but people like clicky things
# i especially dislike the sudo workaround, and i didn't really read the code, but i tested the gui,
# it was working, i like it, so yea, here you go
#
# please also note that this file is not under the LICENSE of the rest of the code (for now)

# import all the stuff the gui needs
from Tkinter import *
import Tkinter as tk
import tkFileDialog
from Tkinter import _setit
from ttk import *

import os, sys, ttk, subprocess, plistlib, tkMessageBox, traceback

# if we aren't sudoing this
if os.getuid() != 0:
    print "Root permission needed to access /dev block devices."

    sudo_bin = "/usr/bin/sudo"
    if not os.path.exists("/usr/bin/sudo"):
        sudo_bin = "/bin/su --command"

    python = sys.executable
    script = sys.argv[0]

    command = [sudo_bin, python, script]
    os.execlp(sudo_bin, *command )
else:
    pass

# change working path to sky3ds folder in case it is run with terminal in a separate folder
os.chdir(os.path.dirname(os.path.realpath(__file__)))

# import the backend stuff
sys.path.append("sky3ds")
sys.path.append("third_party/appdirs")
sys.path.append("third_party/progressbar")
import sky3ds
from sky3ds import disk as disk_functions # 'disk' is too generic a name to avoid confusion
from sky3ds import titles, gamecard
from appdirs import user_data_dir


# the good stuff:
root = Tk()

class View(Frame):

    def __init__(self, root):
        Frame.__init__(self, root)

        # Exception catcher. Use this for catching exceptions in the backend code. Works since tk loop is already going and won't be completely broken by an interruption.
        tk.Tk.report_callback_exception = self.exception

        self.root = root

        self.root.title("SKY3DS Diskwriter")

        self.create_widgets()
        self.create_menus()
        self.modify_window()

        controller.check_for_template()

    def create_widgets(self):
        frame_master = Frame(root, padding = 5)

        frame_top_row = Frame(frame_master)

        label_choose_disk = Label(frame_top_row, text = "Choose Disk:")
        label_choose_disk.pack(side=LEFT)

        self.disk_choice = StringVar()
        self.menu_choose_disk = OptionMenu(frame_top_row, self.disk_choice, '')
        self.menu_choose_disk.pack(side = LEFT, fill=BOTH, expand=1)
        self.update_disk_optionmenu()

        self.button_open_disk = Button(frame_top_row, text = "Open Disk", command = controller.open_disk)
        self.button_open_disk.pack(side=RIGHT)

        button_refresh_list = Button(frame_top_row, text = "Refresh List", command = self.update_disk_optionmenu )
        button_refresh_list.pack(side = RIGHT)

        frame_top_row.pack(fill=BOTH, expand=1, pady = 3)

        frame_rom_list = Frame(frame_master)

        rom_table_columns = ["Slot", "Start", "Size", "Type", "Code", "Title", "Save Crypto"]
        self.tree_rom_table = ttk.Treeview(frame_rom_list, height = 10, columns = rom_table_columns, selectmode="extended")
        self.tree_rom_table.pack()

        self.tree_rom_table.heading('#1', text='Slot', anchor=W)
        self.tree_rom_table.heading('#2', text='Start', anchor=W)
        self.tree_rom_table.heading('#3', text='Size', anchor=W)
        self.tree_rom_table.heading('#4', text='Type', anchor=W)
        self.tree_rom_table.heading('#5', text='Code', anchor=W)
        self.tree_rom_table.heading('#6', text='Title', anchor=W)
        self.tree_rom_table.heading('#7', text='Save Crypto', anchor=W)

        self.tree_rom_table.column('#1', stretch=False, minwidth=40, width=40)
        self.tree_rom_table.column('#2', stretch=NO, minwidth=72, width=72)
        self.tree_rom_table.column('#3', stretch=NO, minwidth=72, width=72)
        self.tree_rom_table.column('#4', stretch=NO, minwidth=72, width=72)
        self.tree_rom_table.column('#5', stretch=NO, minwidth=100, width=100)
        self.tree_rom_table.column('#6', stretch=NO, minwidth=200, width=200)
        self.tree_rom_table.column('#7', stretch=NO, minwidth=90, width=90)
        self.tree_rom_table.column('#0', stretch=NO, minwidth=0, width=0) #width 0 to not display it

        frame_rom_list.pack()

        frame_disk_use_info = Frame(frame_master)

        self.disk_name = StringVar()
        label_disk_name = Label(frame_disk_use_info, textvariable = self.disk_name)
        label_disk_name.pack(side=LEFT)

        self.disk_free_space = StringVar()
        label_disk_free_space = Label(frame_disk_use_info, textvariable = self.disk_free_space)
        label_disk_free_space.pack(side=LEFT, padx = 10)

        self.disk_continuous_space = StringVar()
        label_disk_continuous_space = Label(frame_disk_use_info, textvariable = self.disk_continuous_space)
        label_disk_continuous_space.pack(side=LEFT)

        frame_disk_use_info.pack(fill = BOTH, expand = 1, pady = 3)


        separator = Separator(frame_master, orient = HORIZONTAL )
        separator.pack(fill = BOTH, expand = 1, padx = 10)

        frame_write_buttons = Frame(frame_master)

        button_write_rom = Button(frame_write_buttons, text = "Write Rom", command = controller.write_rom )
        button_write_rom.pack(side=LEFT)

        button_delete_rom = Button(frame_write_buttons, text = "Delete Rom", command = controller.delete_rom )
        button_delete_rom.pack(side=LEFT)

        button_backup_rom = Button(frame_write_buttons, text = "Backup Rom", command = controller.backup_rom )
        button_backup_rom.pack(side=LEFT)

        button_write_save = Button(frame_write_buttons, text = "Write Save", command = controller.write_save )
        button_write_save.pack(side=RIGHT)

        button_backup_save = Button(frame_write_buttons, text = "Backup Save", command = controller.backup_save )
        button_backup_save.pack(side=RIGHT)

        frame_write_buttons.pack(fill = BOTH, expand = 1, pady = 5)

        frame_master.pack()

    def update_disk_optionmenu(self):
        disk_list = controller.get_disk_list()
        menu = self.menu_choose_disk['menu']
        # clear all options
        menu.delete(0, 'end')
        # add new
        if not disk_list:
            raise Exception("No Acceptable disks found")
        else:
            for disk in disk_list:
                menu.add_command(label=disk, command=_setit(self.disk_choice,disk))
                self.disk_choice.set(disk)

    def create_menus(self):
        menu_bar = Menu(root)

        menu_file = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=menu_file)
        menu_file.add_command(label="Exit", command=root.quit)

        menu_tools = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Tools", menu=menu_tools)
        menu_tools.add_command(label="Update Template", command = lambda: update_template() )
        menu_tools.add_command(label="Update Titles", command = lambda: update_titles() )
        menu_tools.add_separator()
        menu_tools.add_command(label="Format Disk", command = lambda: format_disk() )

        #menu_help = Menu(menu_bar, tearoff=0)
        #menu_bar.add_cascade(label="Help", menu=menu_help)
        #menu_help.add_command(label="Diskwriter Help", command = lambda: help_window() )

        root.config(menu=menu_bar)

    def modify_window(self):
        self.root.resizable(0,0) # stops user from resizing window
        root.withdraw()                                                 # un-draw window
        root.update_idletasks()                                         # Update "reqwidth" and "reqheight" from geometry manager
        x = (root.winfo_screenwidth() - root.winfo_reqwidth()) / 2      # Figures out location based on screen and window size
        y = (root.winfo_screenheight() - root.winfo_reqheight()) / 2    #  "
        root.geometry("+%d+%d" % (x, y))                                # places the window at that loction
        root.deiconify()                                                # redraws window

    def exception(self, *args):
        self.top = Toplevel()
        self.top.title("Something broke.")
        self.err = args[1]

        frame_master = Frame(self.top, padding = 5)

        label_error = Label(frame_master, text = self.err)
        label_error.pack()

        close = Button(frame_master, text = "OK", width = 8, command= lambda: self.top.destroy() )
        close.pack(side=RIGHT)

        frame_master.pack()

        self.top.resizable(0,0) # stops user from resizing window
        self.top.withdraw()                                                 # un-draw window
        self.top.update_idletasks()                                         # Update "reqwidth" and "reqheight" from geometry manager
        x = (self.top.winfo_screenwidth() - self.top.winfo_reqwidth()) / 2      # Figures out location based on screen and window size
        y = (self.top.winfo_screenheight() - self.top.winfo_reqheight()) / 2    #  "
        self.top.geometry("+%d+%d" % (x, y))                                # places the window at that loction
        self.top.deiconify()                                                # redraws window

class Controller:

    def __init__(self):
        pass

    def get_disk_list(self):
        disk_size_list = []
        if sys.platform == 'darwin':
            # get plist of disks from diskutil
            list_command = ['diskutil', 'list', '-plist']
            try:
                output = subprocess.check_output(list_command)
            except subprocess.CalledProcessError as err:
                raise Exception( "Could not get list of disks. \nError: %s" % err)

            list_plist = plistlib.readPlistFromString(output)

            disk_list =  list_plist["WholeDisks"]
            # parse the plist for sizes. this might be able to be combined with first step eventually.
            for disk in disk_list:
                # maybe someday check for usb drives only. meh.

                size_command = ['diskutil', 'info', '-plist', disk]

                try:
                    output = subprocess.check_output(size_command)
                except subprocess.CalledProcessError as err:
                    raise Exception("Could not get disk information. \nError: %s" % err)

                size_plist = plistlib.readPlistFromString(output)
                size = self.bytes_to_mb( size_plist["TotalSize"] )
                disk_path = "/dev/" + disk

                disk_size_list.append( (disk_path, size, "MB") )

        else:
            disk_size_list = []
            #get list of disks using lsblk
            list_command =  ["lsblk", "-d", "-n", "-o", "NAME,SIZE,TYPE"]
            try:
                output = subprocess.check_output(list_command)
            except subprocess.CalledProcessError as err:
                raise Exception( "Could not get list of disks. Make sure you have 'lsblk' installed. \nError: %s" % err )

            disk_list =  output.splitlines()

            for disk in disk_list:
                disk_info = disk.split()
                disk_path = "/dev/" + disk_info[0]
                if disk_info[2] == "disk":
                    disk_size_list.append( (disk_path, disk_info[1]) )

        return disk_size_list

    def bytes_to_mb(self, bytes):
        mb = bytes / 1048576
        return mb

    def open_disk(self):
        sd = view.disk_choice.get()
        sd = tuple([x for x in sd[1:-1].split("'")]) #super ugly way to make string into tuple
        sd = sd[1]

        global sd_card
        sd_card = disk_functions.Sky3DS_Disk(sd)
        self.fill_rom_table()

    def get_rom_info(self, rom_list):
        rom_data = []
        for rom in rom_list:
            slot = rom[0]
            start = rom[1]
            size = rom[2]
            rom_header = sd_card.ncsd_header(slot)
            rom_info = titles.rom_info(rom_header['product_code'], rom_header['media_id'])
            if rom_info:
                title = rom_info['name']
                firmware = rom_info['firmware']
            else:
                title = "???"
                firmware = "???"
            rom_data.append( [
                slot,
                "%d MB" % int(rom[1] / 1024 / 1024),
                "%d MB" % int(rom[2] / 1024 / 1024),
                rom_header['card_type'],
                rom_header['product_code'],
                title,
                rom_header['save_crypto'].rjust(12),
                ] )
        return rom_data

    def fill_rom_table(self):
        # clear it out first
        rom_table = view.tree_rom_table

        rom_table.delete(*rom_table.get_children());

        rom_data = self.get_rom_info(sd_card.rom_list)

        for rom in rom_data:
            rom_table.insert("", "end", "", values=(rom) )

        total_free_blocks = sum(512*i[1] for i in sd_card.free_blocks)/1024/1024
        view.disk_free_space.set("Free space: %d MB" % total_free_blocks)

        cont_space = 512 * sd_card.free_blocks[0][1]/1024/1024
        view.disk_continuous_space.set("Largest Continuous Space: %d MB" % cont_space)

        view.disk_name.set("Disk: %s " % sd_card.disk_path)

    def write_rom(self):
        try:
            disk = sd_card.disk_path
        except:
            raise Exception("Please open a disk before attempting to write a rom.")

        file_path = tkFileDialog.askopenfilename( initialdir = os.path.expanduser('~/Desktop'), filetypes=[ ("3DS Rom","*.3ds")] )

        if file_path:
            # follow symlink
            file_path = os.path.realpath(file_path)

            # if the template data doesn't exist we might as well just shut it down right here. If the progress window shows up the exception will stop the process so I can't destrot that toplevel.
            if not self.get_rom_template_data(file_path):
                tkMessageBox.showinfo("Missing Template Data", "Template entry not found.")
                return None

            # get rom size and calculate block count
            rom_size = os.path.getsize(file_path)

            self.message = "Writing %s" % os.path.basename(file_path)
            progress_bar = progress_bar_window("Writing Rom", self.message, mode = "determinate", maximum = rom_size, task = "write")

            root.wait_visibility(progress_bar.window)

            sd_card.write_rom(file_path, progress=progress_bar)

            controller.fill_rom_table()

        else:
            return

    def get_rom_template_data(self, rom_path):

        # open rom file
        romfp = open(rom_path, "rb")

        # get card specific data from template.txt
        serial = gamecard.ncsd_serial(romfp)
        sha1 = gamecard.ncch_sha1sum(romfp)
        template_data = titles.get_template(serial, sha1)
        if not template_data:
            return None
        else:
            return template_data

    def delete_rom(self):
        try:
            rom_list = sd_card.rom_list
        except:
            raise Exception("Please open a disk before attempting to delete a rom.")

        index = view.tree_rom_table.focus()
        if index:
            item = view.tree_rom_table.item(index)

            slot = item['values'][0]

            delete_list = []
            delete_list.append(rom_list[slot])

            rom_info = controller.get_rom_info(delete_list)[0]

            title = rom_info[5]
            slot = rom_info[0] # Instead of relying on the treeview and sd_card to be identical I just pull all of the info out of the sd_card

        else:
            raise Exception("Please select a rom to delete")

        message = "Delete rom %s, %s?" % (slot, title)

        confirm = tkMessageBox.askokcancel("Confirm Delete", message)

        if confirm == True:
            message = "Deleting %s." % title
            task_text = "delete"

            progress_bar = progress_bar_window("Deleting Rom", message, mode = "indeterminate", maximum = 100, task = task_text)

            root.wait_visibility(progress_bar.progress)

            progress_bar.start_indeterminate()

            sd_card.delete_rom(slot)

            progress_bar.progress_complete()

            controller.fill_rom_table()

        else:
            return

    def backup_rom(self):
        try:
            rom_list = sd_card.rom_list
        except:
            raise Exception("Please open a disk before attempting to dump a rom.")

        index = view.tree_rom_table.focus()
        if index:
            item = view.tree_rom_table.item(index)

            tree_slot = item['values'][0]

            delete_list = []
            delete_list.append(rom_list[tree_slot])

            rom_info = controller.get_rom_info(delete_list)[0]

            title = rom_info[5]
            rom_code = rom_info[4]
            index = rom_info[0] # Instead of relying on the treeview and sd_card to be identical I just pull all of the info out of the sd_card
            slot = rom_list[index][0]
            rom_size = rom_list[index][2]

        else:
            raise Exception("Please select a rom to dump.")

        destination_folder = tkFileDialog.askdirectory( initialdir = os.path.expanduser('~/Desktop'), mustexist = True)

        message = "Dump rom %s, %s to %s?" % (slot, title, destination_folder)

        if destination_folder:
            confirm = tkMessageBox.askokcancel("Confirm Rom Dump", message)
        else:
            return

        if confirm == True:
            destination_file = destination_folder + "/" + rom_code + ".3ds"

            message = "Dumping %s to %s" % (rom_code, destination_folder)
            task_text = "%s backup" % title

            progress_bar = progress_bar_window("Dumping Rom", message, mode = "determinate", maximum = rom_size, task = task_text)
            root.wait_visibility(progress_bar.window)

            sd_card.dump_rom( slot, destination_file, progress=progress_bar)
        else:
            return

    def backup_save(self):
        try:
            rom_list = sd_card.rom_list
        except:
            raise Exception("Please open a disk before attempting to backup a save.")

        index = view.tree_rom_table.focus()
        if index:
            item = view.tree_rom_table.item(index)

            tree_slot = item['values'][0]

            delete_list = []
            delete_list.append(rom_list[tree_slot])

            rom_info = controller.get_rom_info(delete_list)[0]

            title = rom_info[5]
            rom_code = rom_info[4]
            index = rom_info[0] # Instead of relying on the treeview and sd_card to be identical I check the rom_list
            slot = rom_list[index][0]

        else:
            raise Exception("Please select a rom to backup a save")

        destination_folder = tkFileDialog.askdirectory( initialdir = os.path.expanduser('~/Desktop'), mustexist = True)

        message = "Backup save for rom %s, %s to %s?" % (slot, title, destination_folder)

        if destination_folder:
            confirm = tkMessageBox.askokcancel("Confirm Save Backup", message)
        else:
            return

        if confirm == True:
            destination_file = destination_folder + "/" + rom_code + ".sav"

            message = "Dumping save from %s to %s" % (rom_code, destination_folder)
            task_text = "%s save backup" % title

            progress_bar = progress_bar_window("Dumping Save", message, mode = "indeterminate", maximum = 100, task = task_text)

            root.wait_visibility(progress_bar.progress)

            progress_bar.start_indeterminate()

            sd_card.dump_savegame( slot, destination_file )

            progress_bar.progress_complete()

        else:
            return


    def write_save(self):
        try:
            disk = sd_card.disk_path
        except:
            raise Exception("Please open a disk before attempting to write a save.")

        file_path = tkFileDialog.askopenfilename( initialdir = os.path.expanduser('~/Desktop'), filetypes=[ ("3DS Save","*.sav")] )

        if file_path:
            # follow symlink
            file_path = os.path.realpath(file_path)

            self.message = "Writing %s" % os.path.basename(file_path)

            progress_bar = progress_bar_window("Writing Save", self.message, mode = "indeterminate", maximum = 100, task = "write save")

            root.wait_visibility(progress_bar.progress)

            progress_bar.start_indeterminate()

            sd_card.write_savegame(file_path)

            progress_bar.progress_complete()

            controller.fill_rom_table()

        else:
            return


    def check_for_template(self):
        root.update_idletasks() #since this is run during view __init__ before mainloop finishes a loop we have to update tk() so it responds properly to input events.

        data_dir = user_data_dir('sky3ds', 'Aperture Laboratories')
        template_txt = os.path.join(data_dir, 'template.txt')

        if not os.path.isfile(template_txt):
            tkMessageBox.showinfo("Template.txt not found.", "Template.txt not found, please select a Sky3ds template file")
            update_template()
        else:
            pass


class progress_bar_window:
    def __init__(self, title, message, mode, maximum, task):
        self.message = message
        self.mode = mode
        self.maximum = maximum
        self.task = task

        self.window = Toplevel(background = "#e2e2e2")
        self.window.wm_attributes("-topmost", 1)
        self.window.resizable(0,0) # stops user from resizing window
        self.window.title(title)
        self.window.grab_set()

        self.create_widgets()

        self.window.protocol('WM_DELETE_WINDOW', self.on_progress_bar_close )

        self.bar_position = 0

        self.start_indeterminate()

    def create_widgets(self):

        frame_master = Frame(self.window, padding = 5)

        label_message = Label(frame_master, text = self.message)
        label_message.pack()

        self.progress = ttk.Progressbar(frame_master, mode = self.mode, orient="horizontal", length = 300)
        self.progress.pack()
        self.progress['maximum'] = self.maximum

        frame_master.pack()

    def start_indeterminate(self):
        if self.mode == "indeterminate":
            self.progress.start(50)
            root.update_idletasks()
        else:
            pass

    def update(self, total_written):
        amount = total_written - self.bar_position

        self.bar_position = self.bar_position + amount

        if total_written == self.maximum:
            self.progress_complete()
        else:
            self.progress["value"] = total_written
            self.progress.update_idletasks()

    def progress_complete(self):
        capital_task = self.task.capitalize()
        message = "%s successful." % capital_task
        self.window.grab_release()
        self.window.wm_attributes("-topmost", 0)
        done = tkMessageBox.showinfo("Complete", message)
        self.window.destroy()

    def on_progress_bar_close(self):
        message = "Please wait for %s to complete." % self.task
        tkMessageBox.showinfo("Cannot Close", message)


class update_template:
    def __init__(self):
        data_dir = user_data_dir('sky3ds', 'Aperture Laboratories')
        template_txt = os.path.join(data_dir, 'template.txt')

        file_name = tkFileDialog.askopenfile( initialdir = os.path.expanduser('~/Desktop'), filetypes=[ ("Text files","*.txt")] )

        if file_name:
            try:
                new_template = file_name.read()
                write_template = open(template_txt, 'w')
                write_template.write(new_template)

                file_name.close()
                write_template.close()

                tkMessageBox.showinfo("Template Updated", "Template.txt updated successfully")

            except:
                raise Exception("Template.txt could not be updated")

            try:
                titles.convert_template_to_json()
            except:
                raise Exception("Template.txt could not converted to JSON. Please verify that your template.txt is not corrupt.")
        else:
            return

class update_titles:
    def __init__(self):
        try:
            message = "Update Titles database"

            progress_bar = progress_bar_window("Updating Titles", message, mode="indeterminate", maximum = 100, task = "Titles update")

            root.wait_visibility(progress_bar.progress)

            progress_bar.start_indeterminate()

            titles.update_title_db()

            progress_bar.progress_complete()

        except:
            raise Exception("Titles database could not be updated.")


class format_disk:
    def __init__(self):
        self.window = Toplevel()
        self.window.wm_attributes("-topmost", 1)
        self.window.title("Format Disk")
        self.window.grab_set()

        self.create_widgets()

        self.modify_window()

        self.update_disk_optionmenu()

        self.window.protocol('WM_DELETE_WINDOW', self.on_format_window_close )

    def create_widgets(self):
        frame_master = Frame(self.window, padding = 5)

        frame_top_row = Frame(frame_master)

        label_choose = Label(frame_top_row, text = "Choose Disk:")
        label_choose.pack(side=LEFT)

        self.disk_choice = StringVar()
        self.menu_choose_disk = OptionMenu(frame_top_row, self.disk_choice, '')
        self.menu_choose_disk.pack(side = LEFT, fill=BOTH, expand=1)
        self.menu_choose_disk.configure(width = 30)

        button_refresh_list = Button(frame_top_row, text = "Refresh List", command = self.update_disk_optionmenu )
        button_refresh_list.pack(side=LEFT)

        frame_top_row.pack()

        frame_bottom_row = Frame(frame_master)

        button_format_disk = Button(frame_bottom_row, text = "Format Disk", command = self.format_confirm )
        button_format_disk.pack(side=LEFT)

        frame_bottom_row.pack()

        frame_master.pack()

    def modify_window(self):
        self.window.resizable(0,0) # stops user from resizing window
        self.window.withdraw()                                                 # un-draw window
        self.window.update_idletasks()                                         # Update "reqwidth" and "reqheight" from geometry manager
        x = (self.window.winfo_screenwidth() - self.window.winfo_reqwidth()) / 2      # Figures out location based on screen and window size
        y = (self.window.winfo_screenheight() - self.window.winfo_reqheight()) / 2    #  "
        self.window.geometry("+%d+%d" % (x, y))                                # places the window at that loction
        self.window.deiconify()                                                # redraws window

    def update_disk_optionmenu(self):
        disk_list = controller.get_disk_list()
        menu = self.menu_choose_disk['menu']
        # clear all options
        menu.delete(0, 'end')
        # add new
        if not disk_list:
            raise Exception("No Acceptable disks found")
        else:
            for disk in disk_list:
                menu.add_command(label=disk, command=_setit(self.disk_choice,disk))
                self.disk_choice.set(disk)

    def format_confirm(self):
        sd = self.disk_choice.get()
        sd = tuple([x for x in sd[1:-1].split("'")]) #super ugly way to make string into tuple
        sd = sd[1]

        message = "Formatting %s will permanently erase all data and partitions on %s. \nPlease confirm that you have chosen the correct disk to format. \n \nFormatting can take several minutes to complete, please be patient." % (sd, sd)

        self.window.grab_release()
        self.window.wm_attributes("-topmost", 0)
        confirm = tkMessageBox.askokcancel("Confirm Format", message)
        self.window.wm_attributes("-topmost", 1)
        self.window.grab_set()

        if confirm == True:
            self.format_disk(sd)
        else:
            return

    def format_disk(self, sd):
        #first unmount all volums from disk
        if sys.platform == 'darwin':
            list_command = ["diskutil", "unmountDisk", sd]
            try:
                output = subprocess.check_output(list_command)
            except subprocess.CalledProcessError as err:
                raise Exception( "Could not get unmount partitions on %s. \nError: %s" % (sd, err) )
        else:
            # linux really just doesn't care if a volume is mounted, it'll let us format it anyway
            pass

        # pass it along to disk class
        disk_to_format = disk_functions.Sky3DS_Disk(sd)

        message = "Formatting %s" % sd

        progress_bar = progress_bar_window("Formatting Disk", message, mode="indeterminate", maximum = 100, task = "format")

        root.wait_visibility(progress_bar.progress)

        progress_bar.start_indeterminate()

        disk_to_format.format()

        progress_bar.progress_complete()

    def on_format_window_close(self):
        view.update_disk_optionmenu()
        self.window.destroy()

class help_window:
    def __init__(self):
        self.top = Toplevel()
        #root.grab_set() # keeps other windows from being active over this one
        self.top.wm_attributes('-topmost', 1) # keeps this window on top of other
        self.top.title("Diskwriter Help")

        self.create_widgets()

        self.modify_window()

    def create_widgets(self):

        help_file = self.open_help_file()

        frame_help_text = Frame(self.top)

        message_help_file = Message( frame_help_text, text = help_file)

        message_help_file.pack()


        button_close = Button(frame_help_text, text = "Close", command = self.close_window )
        button_close.pack()

        frame_help_text.pack(padx=5, pady=5)

    def modify_window(self):
        self.top.withdraw()                                                 # un-draw window
        self.top.update_idletasks()                                         # Update "reqwidth" and "reqheight" from geometry manager
        x = (self.top.winfo_screenwidth() + view.root.winfo_reqwidth()) / 2 + 8      # Figures out location based on screen and window size
        y = (self.top.winfo_screenheight() - self.top.winfo_reqheight()) / 2    # "
        self.top.geometry("+%d+%d" % (x, y))                                # places the window at that loction
        self.top.deiconify()                                                # redraws window

    def close_window(self):
        self.top.destroy()


    def open_help_file(self):
        help_file = open('help_file.txt', 'r')
        return help_file.read()





if __name__ == '__main__':
    controller = Controller()
    view = View(root)
    root.mainloop()
