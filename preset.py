import json
import files


class Preset:

    cfg = None

    def __init__(self):
        # load presets config
        if self.cfg is None:
            with open('presets.json', 'r') as f:
                self.cfg = json.load(f)
                f.close()
        self.name = 'default'
        self.data = None
        self.rp360p = None
        self.wah = None
        self.cmpr = None
        self.dist = None
        self.amp = None
        self.vol = None
        self.eq = None
        self.gate = None
        self.mod = None
        self.dly = None
        self.rvb = None
        self.fxc = {}
        self.dirty = False

    def load_from_file(self, file):
        with open(file, 'r') as f:
            self.data = json.load(f)
        f.close()
        self.load_fx_chain()

    def load_from_device(self, data):
        self.get_data(data)
        self.load_fx_chain()

    def save_to_file(self, file):
        j = json.JSONEncoder()
        with open(file, 'w') as f:
            f.write(j.encode(self.data))
        f.close()

    def get_data(self, data):
        self.data = None
        self.data = json.loads(data)

    def save_to_device(self, name):
        pass

    def get_names(self):
        names = {}
        for i in self.fxc:
            if 'fx' in self.fxc.get(i).keys():
                name = self.fxc.get(i).get('fx').get('name')
            else:
                name = self.fxc.get(i).get('name')
            names.update({i: name})
        return names

    def set_name(self, name):
        self.name = name

    def dumps(self):
        return json.dumps(self.data)

    def load_fx_chain(self):
        """
        loads json preset from memory (self.data), assigns each fx and add them to fx chain
        """
        self.name = self.data.get('preset').get('name')
        print('@@', self.data)
        for i in range(10):
            fx = self.data.get('preset').get('fxc').get(str(i))
            if not fx:
                break
            if fx.get('fx') is None: # volume and equalizer have no fx key
                name = fx.get('name')
            else:
                name = fx.get('fx').get('name')
            if 'wah' in name:
                self.wah = fx
                self.fxc.update({i: self.wah})
            elif "cmpr" in name:
                self.cmpr = fx
                self.fxc.update({i: self.cmpr})
            elif 'dist' in name:
                self.dist = fx
                self.fxc.update({i: self.dist})
            elif 'amp' in name:
                self.amp = fx
                self.fxc.update({i: self.amp})
            elif 'eq' in name:
                self.eq = fx
                self.fxc.update({i: self.eq})
            elif 'gate' in name:
                self.gate = fx
                self.fxc.update({i: self.gate})
            elif 'vol' in name:
                self.vol = fx
                self.fxc.update({i: self.vol})
            elif 'mod' in name:
                self.mod = fx
                self.fxc.update({i: self.mod})
            elif 'dly' in name:
                self.dly = fx
                self.fxc.update({i: self.dly})
            elif 'rvb' in name:
                self.rvb = fx
                self.fxc.update({i: self.rvb})

    def update_fx(self, index, fx):
        """
        replace an effect by a new one from the same type with default values
        :param index: position in the fx chain,
        :param fx: name of the new fx
        :return: None
        """
        if fx == self.fxc.get(index):
            return
        else:
            self.fxc.pop(index)
            data = self.cfg.get(fx)
            level1 = {}
            level2 = {}
            level1.update({'ENABLE': 1})
            for k, v in data.items():
                if v.get('TYPE') != 'list':
                    minv = v.get('MIN')
                    maxv = v.get('MAX')
                    value = int((maxv - minv) / 2)
                    level2.update({k: value})
                elif v.get('TYPE') == 'list':  # if list, get first value of the list
                    value = v.get('0')
                    level2.update({k: value})

            level2.update({'name': fx})
            level1.update({'fx': level2})
            self.fxc.update({index: level1})

    def delete_fx(self, index):
        '''
        removes from the fx chain fx whose position is index
        :param index: position in the fx chain
        :return:
        '''
        removed = self.fxc["preset"]["fx"].pop(str(index))
        self.fxc = removed
