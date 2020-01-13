from device import Device
from preset import Preset
import json

banks = {}
preset = {}
device = Device()
device.sleeptime = 0.2
device.open()
f = open('fbanks.json', 'a')
device.state()
device.version()
device.sbs()
device.sync()

for i in range(98):
    device.select_preset_at(i, 'factory')
    cp = device.get_active_preset()
    preset.update({i: json.loads(cp)})
    banks.update({'Factory': preset})
    j = json.JSONEncoder()
    f.write(j.encode(banks))


f.close()

# for i in range(40, 41):
#     device.select_preset_at(i, 'user')
#     preset.update({i: json.loads(device.get_active_preset())})
#     banks.update({'User': preset})




