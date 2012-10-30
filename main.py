# -*- codeing: utf-8 -*-
from gi.repository import Gtk
from gi.repository import GdkPixbuf
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


class SlavaFinder:

    def __init__(self):

        self.builder = Gtk.Builder()
        self.builder.add_from_file("layout.glade")

        self.createTreeview()
        self.createTreeviewFiles()
        self.default_image = self.builder.get_object("PreviewImage")
        self.window = self.builder.get_object("WindowMain")

        self.builder.connect_signals(self)

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

    def on_WindowMain_destroy(self, widget, data=None):
        Gtk.main_quit()

    def on_TreeviewSelection_changed(self, selection, data=None):
        model, treeiter = selection.get_selected()
        if treeiter is None:
            return
        self.current_folder, self.current_path = model[treeiter]
        self.update_current_files()

    def on_Treeview_row_expanded(self, treeview, treeiter, path, date=None):
        if not self.temp:
            self.add_folders(treeview.get_model(), treeiter)
            self.temp = True
            treeview.expand_row(path, False)
            self.temp = False

    def on_TreeviewFilesSelection_changed(self, selection,  data=None):
        model, treeiter = selection.get_selected()
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


def main():

    application = SlavaFinder()
    application.window.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
