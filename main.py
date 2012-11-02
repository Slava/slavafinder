# -*- codeing: utf-8 -*-
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GdkPixbuf  # for preview images load
from gi.repository import Gio       # monitor file changes
import os                           # for files manipulation
import mimetypes                    # to guess file type
import time                         # to format time stamp


# get human readable file size (copy-pasted from stackoverflow.com)
def sizeof_fmt(num):
    for x in ['bytes', 'KiB', 'MiB', 'GiB']:
        if num < 1024.0:
            return "%3.1f%s" % (num, x)
        num /= 1024.0
    return "%3.1f%s" % (num, 'TB')


class Dialog(Gtk.Dialog):

    def __init__(self, parent, title, message):
        Gtk.Dialog.__init__(self, title, parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                            Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(150, 100)

        label = Gtk.Label(message)

        box = self.get_content_area()
        box.add(label)
        self.show_all()


class SlavaFinder(object):

    def __init__(self):

        self.builder = Gtk.Builder()
        self.builder.add_from_file("layout.glade")

        self.createTreeview()
        self.createTreeviewFiles()
        self.createContextMenu()

        self.default_image = self.builder.get_object("PreviewImage")
        self.window = self.builder.get_object("WindowMain")
        self.current_file = None

        self.builder.connect_signals(self)
        self.init_monitor()

    def init_monitor(self):
        # define folder monitor
        self.monitor = Gio.file_new_for_path(self.current_path).monitor_directory(0, None)
        self.monitor.connect("changed", self.directory_changed)

    def directory_changed(self, monitor, file1, file2, evt_type):
        self.update_current_files()

    def createTreeviewFiles(self):
        self.treeviewfiles = self.builder.get_object("TreeviewFiles")
        # absolute path to file and filename
        self.FilesTreeStorage = Gtk.TreeStore(str, str)

        # add all current files
        self.update_current_files()
        self.treeviewfiles.set_model(self.FilesTreeStorage)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Files in folder:", renderer, text=0)
        self.treeviewfiles.append_column(column)

        # make it editable and renameable
        renderer.set_property("editable", True)
        renderer.connect("edited", self.on_file_renamed)

    def createTreeview(self):
        self.treeview = self.builder.get_object("Treeview")
        # absolute path to folder and folder name
        self.FoldersTreeStorage = Gtk.TreeStore(str, str)

        # firstly add HOME
        dir = os.path.abspath(os.environ['HOME'])
        home = self.FoldersTreeStorage.append(None, ['Home', dir])

        # set current path & folder name
        self.current_path = dir
        self.current_folder = home

        # add other stuff
        self.add_folders(self.FoldersTreeStorage, home)

        self.treeview.set_model(self.FoldersTreeStorage)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Your folders:", renderer, text=0)
        self.treeview.append_column(column)

        # I will use it to break recursion! False by default
        self.temp = False

    def createContextMenu(self):
        self.context_menu = Gtk.Menu()

        # add "move to trash" button
        move_to_trash_button = Gtk.MenuItem("Move to trash")
        move_to_trash_button.connect("button_press_event", self.move_current_file_to_trash)
        self.context_menu.append(move_to_trash_button)

        # add "delete file" button
        delete_file_button = Gtk.MenuItem("Delete file")
        delete_file_button.connect("button_press_event", self.delete_current_file)
        self.context_menu.append(delete_file_button)

    def on_WindowMain_destroy(self, widget, data=None):
        Gtk.main_quit()

    def on_TreeviewSelection_changed(self, selection, data=None):
        self.current_file = None
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return

        self.current_folder, self.current_path = model[treeiter]
        self.update_current_files()

        # reinit monitoring files
        self.init_monitor()

    def on_Treeview_row_expanded(self, treeview, treeiter, path, date=None):
        if not self.temp:
            self.add_folders(treeview.get_model(), treeiter)
            self.temp = True
            treeview.expand_row(path, False)
            self.temp = False

    def on_TreeviewFilesSelection_changed(self, selection,  data=None):
        self.current_file = None

        # update current file, path, etc
        self.update_selection(selection)

        model, treeiter = selection.get_selected()

        # if nothing is selected, just return
        if treeiter is None:
            return

        # ok, get filename and filepath
        filename, filepath = model[treeiter]
        filetype = mimetypes.guess_type(filepath, False)

        # ok set all known information
        self.builder.get_object("FileNameCaption").set_text(filename)

        if filetype[0]:
            self.builder.get_object("FileTypeCaption").set_text(filetype[0])
        else:
            self.builder.get_object("FileTypeCaption").set_text("unknown type")

        self.builder.get_object("CreationDateLabel").set_text(time.ctime(os.stat(filepath).st_ctime))

        self.builder.get_object("SizeLabel").set_text(sizeof_fmt(os.path.getsize(filepath)))

        # if type is image, lets try show it in preview
        if filetype[0] and 'image' in filetype[0]:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filepath, 400, 400)
            self.builder.get_object("PreviewImage").set_from_pixbuf(pixbuf)
        else:
            # it will put just 'no image' icon
            self.builder.get_object("PreviewImage").set_from_file(filepath)

    def on_TreeviewFiles_row_activated(self, treeview, path, view_column, user_data=None):
        treeiter = treeview.get_model().get_iter(path)
        filename, filepath = treeview.get_model()[treeiter]
        import subprocess
        import os
        import sys
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', filepath))
        elif os.name == 'nt':
            os.startfile(filepath)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', filepath))

    def on_TreeviewFiles_button_release_event(self, treeview, event, user_data=None):
        if event.type == Gdk.EventType.BUTTON_RELEASE and event.button == 3 and self.current_file is not None:
            self.context_menu.popup(None, None, None, None, event.button, event.time)
            self.context_menu.show_all()

    def on_file_renamed(self, widget, path, text):
        # you know, we can not rename to empty string
        if text == "":
            return

        file_to_change = self.FilesTreeStorage[path]
        gio_current_file = Gio.file_new_for_path(file_to_change[1])

        # if we want to rename file to same name
        if file_to_change[0] == text:
            return

        try:
            Gio.File.set_display_name(gio_current_file, text, None)
        except Exception as message:
            print message
            return

        self.update_current_files()

    def update_selection(self, selection):
        model, treeiter = selection.get_selected()

        # update current selection
        self.current_file = treeiter

    def add_folders(self, model, treeiter):
        # remove its subtree
        self.remove_all_children(model, treeiter)

        # and add all children
        dir = model[treeiter][1]
        for folder in sorted(os.listdir(dir)):
            child_path = dir + '/' + folder
            if os.path.isdir(child_path) and folder[0] != '.':
                child = model.append(treeiter, [folder, child_path])
                # add temp pair to make it look like it has something
                # meaningfull, when we need, we will expand it
                if any(os.path.isdir(child_path + '/' + fld) and fld[0] != '.' for fld in os.listdir(child_path)):
                    model.append(child, ['temp', 'temp'])

    def update_current_files(self):
        self.remove_all_children(self.FilesTreeStorage, None)

        # add all non hiden files in current dir
        for fl in sorted(os.listdir(self.current_path)):
            fl_path = self.current_path + '/' + fl
            if os.path.isfile(fl_path) and fl[0] != '.':
                self.FilesTreeStorage.append(None, [fl, fl_path])

    def remove_all_children(self, model, treeiter):
        child = model.iter_children(treeiter)
        while child is not None:
            model.remove(child)
            child = model.iter_children(treeiter)

    def move_current_file_to_trash(self, menuitem, user_data=None):
        giofile = Gio.file_new_for_path(self.FilesTreeStorage[self.current_file][1])
        Gio.File.trash(giofile, None)

    def delete_current_file(self, menuitem, user_data=None):
        file_for_deletion = self.FilesTreeStorage[self.current_file]
        giofile = Gio.file_new_for_path(file_for_deletion[1])

        # user should confirm he wants to delete this file
        dialog = Dialog(self.window, "Delete file " + file_for_deletion[0] + "?", "Are you sure you want to delete file " + file_for_deletion[0] + "? You will not be able to restore it!")
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            Gio.File.delete(giofile, None)
        dialog.destroy()


def main():

    application = SlavaFinder()
    application.window.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
