
import gi
import logging
from device import Device
from preset import Preset
from fxbox import FxBox
from files import Configuration
import threading
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


#TODO autoconnect
#TODO save imported preset
#TODO load factory prests from local drive
#TODO reposition fx in the chain
#TODO implementing stompbox mode
#TODO implementing LFO assignment


class MessageHandler(logging.Handler):
    def __init__(self, parent_widget):
        self.parent_widget = parent_widget
        logging.Handler.__init__(self)
        formatter = logging.Formatter('pyrp360 %(levelname)-2s %(message)s')
        self.setFormatter(formatter)

    def dialog(self, message):
        dialog = Gtk.Dialog("Message", self.parent_widget, 0, (Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.set_default_size(150, 100)
        label = Gtk.Label(message)
        box = dialog.get_content_area()
        box.add(label)
        dialog.show_all()
        return dialog

    def handle(self, record):
        print(record.getMessage())
        # critical
        if record.levelname == 'CRITICAL':
            dialog = self.dialog(record.getMessage())
            rep = dialog.run()
            if rep == Gtk.ResponseType.OK:
                dialog.destroy()
                Gtk.main_quit()
        # error
        elif record.levelname == 'ERROR' and 'NACK' in record.getMessage():
            dialog = self.dialog(record.getMessage())
            rep = dialog.run()
            if rep == Gtk.ResponseType.OK:
                dialog.destroy()


class RP360:

    def __init__(self):
        self.device = Device()
        self.preset = None
        self.config = Configuration()
        self.thread = threading.Thread(target=self.load_banks)

        self.builder = Gtk.Builder()
        self.builder.add_from_file("pyrp360.glade")
        self.rp_mainwindow = self.builder.get_object("rp.mainwindow")
        self.rp_mainwindow.maximize()

        # get gtk objects
        self.rp_treeview = self.builder.get_object('rp.treeview')
        self.rp_model = self.builder.get_object('rp.model')
        self.rp_treeview.set_model(self.rp_model)
        self.rp_preset_selection = self.builder.get_object('rp.preset.selection')
        self.rp_label_active_preset = self.builder.get_object('rp.activepreset.label')
        self.rp_paned = self.builder.get_object('rp.paned')
        self.flowbox = self.builder.get_object('rp.flowbox')
        self.button_load = self.builder.get_object('rp.preset.button.import')
        self.button_save = self.builder.get_object('rp.preset.button.save')
        self.button_connect = self.builder.get_object('rp.button.connect')
        self.button_save_to_disk = self.builder.get_object('rp.button.preferences')
        self.button_export = self.builder.get_object('rp.preset.button.export')
        self.pref_ok = self.builder.get_object('rp.pref.ok')
        self.pref_cancel = self.builder.get_object('rp.pref.cancel')
        self.pref_edit1 = self.builder.get_object('rp.pref.edit1')
        self.pref_switch1 = self.builder.get_object('rp.pref.switch1')
        self.pref_debug = self.builder.get_object('rp.pref.debug')
        self.pref_win = self.builder.get_object('rp.win.preferences')
        self.progress_win = self.builder.get_object('rp.win.progress')
        self.progress_bar = self.builder.get_object('rp.win.progress.bar')
        self.about_win = self.builder.get_object('rp.win.about')

        # init message handler
        self.msg_handler = MessageHandler(self.rp_mainwindow)
        self.device.logger.addHandler(self.msg_handler)

        # signals
        handlers = {
            "onMainDestroy": self.on_destroy_main,
            "onPresetChanged": self.on_preset_changed,
            "onProgressBarDestroy": self.populate_banks_list,
            'onButtonLoadPreset': self.on_button_import_preset,
            'onButtonConnect': self.on_button_connect,
            "onButtonSavePreset": self.on_button_save_preset,
            'on_rp_button_preferences_clicked': self.on_button_preferences_clicked,
            'on_pref_ok_clicked': self.on_pref_ok_clicked,
            'on_pref_cancel_clicked': self.on_pref_cancel_clicked,
            'on_about_clicked': self.on_about_clicked,
            'on_preset_name_edit': self.on_preset_rename,
            'on_preset_button_export_clicked': self.on_preset_button_export_clicked

        }
        self.builder.connect_signals(handlers)

        #config initial state
        self.rp_paned.set_position(180)
        self.button_load.set_sensitive(False)
        self.button_save.set_sensitive(False)
        self.button_connect.set_sensitive(False)
        self.button_export.set_sensitive(False)
        self.rp_mainwindow.show_all()
        self.progress_win.hide()
        self.pref_win.hide()

        if self.device.detect_device():
            self.button_connect.set_sensitive(True)
        # TODO autoconnect

    def on_destroy_main(self, args):
        if self.device is not None:
            self.device.close()
        Gtk.main_quit()

    def on_button_preferences_clicked(self, *data):
        self.pref_switch1.set_state(self.config.get('autoconnect'))
        self.pref_edit1.set_text(self.config.get('device'))
        self.pref_debug.set_state(self.config.get('debug'))
        self.pref_win.show()

    def on_pref_ok_clicked(self, *data):
        self.config.write("device", self.pref_edit1.get_text())
        self.config.write("autoconnect", self.pref_switch1.get_state())
        self.config.write('debug', self.pref_debug.get_state())
        self.button_connect.set_sensitive( not self.device.connected)
        self.pref_win.hide()

    def on_preset_button_export_clicked(self, *data):
        dialog = Gtk.FileChooserDialog("Please choose a file", self.rp_mainwindow,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        gtkfilter = Gtk.FileFilter()
        gtkfilter.add_pattern('*.rp360p')
        gtkfilter.set_name('*.rp360p')
        dialog.add_filter(gtkfilter)
        dialog.set_filename(self.preset.name+'.rp360p')
        response = dialog.run()
        dialog.set_filename(self.preset.name + '.rp360p')
        if response == Gtk.ResponseType.OK:
            if self.preset:
                filename = dialog.get_filename()
                if '.rp360p' not in filename:
                    filename = filename + '.rp360p'
                self.preset.save_to_file(filename)
        dialog.destroy()

    def on_pref_cancel_clicked(self, *data):
        self.pref_win.hide()

    def on_about_clicked(self, *data):
        self.about_win.show()

    def on_preset_rename(self, *data):
        self.rp_model, iter = self.rp_preset_selection.get_selected()
        self.rp_model.set_value(iter, 2, data[2])
        self.preset.set_name(data[2])
        self.device.set_preset_name(self.preset.name)
        self.rp_label_active_preset.set_text('Preset : [' + self.preset.name + '] *')

    def on_preset_changed(self, args):
        self.rp_model, self.rp_treeview = self.rp_preset_selection.get_selected()
        self.rp_label_active_preset.set_text(' Preset: [' + self.rp_model[self.rp_treeview][2] + '] ')
        self.preset = None
        self.preset = Preset()
        sel = self.get_selected_preset_index()
        bank_type = 'factory' if sel[0] == 'F' else 'user'
        self.device.select_preset_at(sel[1], bank_type)
        data = self.device.get_active_preset()
        self.preset.load_from_device(data)
        self.build_fxc()
        #self.device.set_preset_dirty()
        self.rp_label_active_preset.set_text('Preset : [' + self.preset.name + '] *')

    def on_button_import_preset(self, args):
        dialog = Gtk.FileChooserDialog("Please choose a file", self.rp_mainwindow , Gtk.FileChooserAction.OPEN, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        gtkfilter = Gtk.FileFilter()
        gtkfilter.add_pattern('*.rp360p')
        gtkfilter.set_name('*.rp360p')
        dialog.add_filter(gtkfilter)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.preset = None
            self.preset = Preset()
            self.preset.load_from_file(dialog.get_filename())
            self.device.send_preset(self.preset)
            self.build_fxc()
            self.rp_model, iter = self.rp_preset_selection.get_selected()
            self.rp_model.set_value(iter, 2, self.preset.name)
            self.rp_label_active_preset.set_text('Preset : [' + self.preset.name + '] *')
        dialog.destroy()

    def on_button_connect(self, args):
        self.progress_win.show()
        self.preset = None
        self.button_save.set_sensitive(False)
        self.button_load.set_sensitive(False)
        self.button_connect.set_sensitive(False)
        if self.device.open():
            self.thread.start()
            self.build_fxc()

    def on_button_save_preset(self, args):
        if self.device.connected:
            sel = self.get_selected_preset_index()
            bank_type = 'factory' if sel[0] == 'F' else 'user'
            self.device.store_preset(sel[1], bank_type)
            self.device.set_preset_name(self.preset.name)
            self.rp_label_active_preset.set_text('Preset : [' + self.preset.name + '] ')

    def on_parameter_changed(self, *args):
        self.device.set_fx_value(args[1], args[2])

    def on_fx_changed(self, *args):
        # destroy previous FxBox
        self.flowbox.get_child_at_index(args[1]).destroy()
        self.preset.update_fx(args[1], args[2])
        fx = self.preset.fxc.get(args[1])
        fxbox = FxBox(fx, args[1])
        fxbox.connect('parameter-changed', self.on_parameter_changed)
        fxbox.connect('fx-changed', self.on_fx_changed)
        self.flowbox.insert(fxbox.get_widget(), args[1])
        self.device.set_fx_model(fx.get('fx').get('name'), args[1])

    def build_fxc(self):
        # empty flow box first
        for c in self.flowbox.get_children():
            c.destroy()

        for i in range(10):
            fx = self.preset.fxc.get(i)
            #TODO: if fx is none, create empty fxbox with add button
            if fx is not None:
                fxbox = FxBox(fx, i)
                fxbox.connect('parameter-changed', self.on_parameter_changed)
                fxbox.connect('fx-changed', self.on_fx_changed)
                self.flowbox.insert(fxbox.get_widget(), -1)
        self.rp_label_active_preset.set_text('Preset : [' + self.preset.name + ']    ')

    def progress(self, i):
        self.progress_bar.set_fraction(i/100.0)
        self.progress_bar.set_text('loading presets : ' + str(i) + '%')
        if i >= 100:
            self.progress_win.hide()
            self.rp_label_active_preset.set_text('Preset : [' + self.preset.name + ']  ')
            for i in self.rp_model:
                if self.preset.name in i[2]:
                    self.rp_preset_selection.select_path(i[1] - 1)
                    break
            self.button_save.set_sensitive(True)
            self.button_load.set_sensitive(True)
            self.button_export.set_sensitive(True)
        return False

    def load_banks(self):
        GLib.idle_add(self.progress, 0)
        self.device.state()
        GLib.idle_add(self.progress, 16)
        self.device.version()
        GLib.idle_add(self.progress, 32)
        self.device.sbs()
        GLib.idle_add(self.progress, 48)
        self.device.sync()
        GLib.idle_add(self.progress, 64)
        banks_list = self.device.get_banks()
        self.populate_banks_list(banks_list)
        GLib.idle_add(self.progress, 80)
        self.preset = None
        self.preset = Preset()
        self.preset.load_from_device(self.device.get_active_preset())
        GLib.idle_add(self.progress, 100)
        return True

    def populate_banks_list(self, banks):
        for i in range(99):
            self.rp_model.insert(i, ['F', i+1, banks.get('F').get(i+1)])
        for i in range(99):
            self.rp_model.insert(i, ['U', i+1, banks.get('U').get(i+1)])

    def get_selected_preset_index(self):
        '''
        get the index of the selected preset
        :return: tuple(bank_type, index)
        '''
        self.rp_model, self.rp_treeview = self.rp_preset_selection.get_selected()
        p = self.rp_model[self.rp_treeview]
        return [p[0], p[1]-1]


if __name__ == '__main__':
    rp360 = RP360()
    Gtk.main()


