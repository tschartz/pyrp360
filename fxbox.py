import json
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject


class FxBox(GObject.Object):

    cfg = None
    fx_path = 'preset/fxc/'
    __gsignals__ = {
        'parameter-changed': (GObject.SIGNAL_RUN_LAST, None, (str, str,)),
        'fx-changed': (GObject.SIGNAL_RUN_LAST, None, (int, str,))
    }

    def __init__(self, fx_params, index):
        super().__init__()
        self.index = index
        self.params = fx_params
        self.frame = Gtk.Frame()
        # load presets config
        if self.cfg is None:
            with open('presets.json', 'r') as f:
                self.cfg = json.load(f)
                f.close()

        # grid container for fx params
        self.grid = Gtk.Grid()
        self.grid.set_border_width(6)
        self.grid.set_column_spacing(6)
        self.grid.set_row_spacing(6)
        self.frame.add(self.grid)
        # enable switch
        enable = self.params.get("ENABLE")
        self.switch = Gtk.Switch()
        self.grid.attach(self.switch, 0, 0, 1, 1)
        if enable == 1 or enable is None:  # volume has no 'enable'
            self.switch.set_active(True)
        else:
            self.switch.set_active(False)
        self.switch.connect("notify::active", self.on_parameter_changed, 'ENABLE')
        # set fx and model names
        if 'fx' in self.params.keys():  # volume & eq have no 'fx' key
            self.fx_id = self.params.get('fx').get("name")
        else:
            self.fx_id = self.params.get('name')
        self.fx_type = self.fx_id.split('.')[0]
        self.frame.set_label('< ' + str(index) + ' - ' + self.fx_type + ' >')
        # combobox for fx model
        self.model = Gtk.ComboBoxText()
        for i in self.cfg.keys():  # get fx values
            if self.fx_type in i:
                self.model.append(i, i)
            if self.fx_id in i:
                self.model.set_active_id(i)
        self.model.connect('changed', self.on_fx_changed)
        self.grid.attach_next_to(self.model, self.switch, Gtk.PositionType.RIGHT, 2, 1)
        # build parameters widgets
        self.build_params()
        self.frame.show_all()

    def get_widget(self):
        return self.frame

    def get_fx_type(self):
        return self.fx_type

    def build_params(self):
        # read fx params properties
        data = self.cfg.get(self.fx_id)
        # get parameters descriptions
        param_list = []
        for k, v in data.items():
            param_list.append({k: v})
        row = 2
        for i in param_list:
            for k, v in i.items():
                label = Gtk.Label(k)  # name of the param.
                label.set_justify(Gtk.Justification.LEFT)
                self.grid.attach(label, 0, row, 1, 1)
                if v.get('TYPE') == 'list':  # if list then create a ComboBox
                    size = v.get('SIZE')
                    comboboxtext = Gtk.ComboBoxText.new()
                    index = 0
                    for x in range(0, size):
                        comboboxtext.append(str(x), v.get(str(x)))
                        if 'fx' in self.params.keys():
                            index = self.params.get('fx').get(k)
                        else:
                            index = self.params.get(k)
                    comboboxtext.set_active_id(str(index))
                    comboboxtext.connect('changed', self.on_parameter_changed, k)
                    self.grid.attach(comboboxtext, 1, row, 1, 1)

                else:  # else create a GtkScale
                    type = v.get('TYPE')
                    unit = v.get('UNIT')
                    minv = v.get('MIN')
                    maxv = v.get('MAX')
                    scale = Gtk.Scale().new_with_range(Gtk.Orientation.HORIZONTAL, minv, maxv, 1)
                    scale.set_value_pos(Gtk.PositionType.LEFT)
                    if type == 'float':
                        scale.set_digits(1)
                    if 'fx' in self.params.keys():
                        value = self.params.get('fx').get(k)
                    else:
                        value = self.params.get(k)
                    print(self.params, k)
                    scale.set_value(value)
                    scale.connect('value-changed', self.on_parameter_changed, k)
                    self.grid.attach(scale, 1, row, 1, 1)

                    # set param unit
                    if unit != '':
                        label.set_text(label.get_text() + ' (' + unit + ')')
            row = row + 1
        return row

    def on_parameter_changed(self, *data):
        path = ''
        value = ''
        if type(data[0]) == Gtk.Switch:
            if data[0].get_state():
                value = '1'
            else:
                value = '0'
            path = self.fx_path + str(self.index) + '/' + data[2]
        elif type(data[0]) == Gtk.ComboBoxText:
            value = str(int(data[0].get_active_id()))
            path = self.fx_path + str(self.index) + '/' + data[1]

        elif type(data[0]) == Gtk.Scale:
            value = str(int(data[0].get_value()))
            path = self.fx_path + str(self.index) + '/' + data[1]
        else:
            return
        self.emit('parameter-changed', str(path), str(value))

    def on_fx_changed(self, *data):
        self.emit('fx-changed', self.index, str(self.model.get_active_id()))

