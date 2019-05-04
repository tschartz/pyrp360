
cmd_state = 'U\x16\x00C\x00\x00\x00\x00["rp",0,"STATE"]\n'

cmd_version = '["rp",1,"VERSION"]\n' #'U\x18\x00C\x00\x01\x00\x00["rp",1,"VERSION"]\xD3\n'

cmd_sbs = '["sbs",2,"",1]\n'

cmd_sync = '["rp",3,"system/SYNC"]\n'

cmd_get_factory_preset_name = ['["rp",', ',"banks/factory/', '/name"]\n']

cmd_get_user_preset_name = ['["rp",', ',"banks/user/', '/name"]\n']

cmd_get_last_preset = '["rp",6,"system/LAST PRES"]\n'

cmd_get_preset0 = '["rc",', ',"preset"]\n'

cmd_get_preset1 = '\x55\x06\x00\x02\x00\x72\x00\x42\x44'

cmd_get_preset2 = '\x55\x06\x00\x02\x00\x73\x00\x42\x43'

cmd_set_preset_value = ['["sp",', ',"', '",', ']\n']

cmd_set_preset_dirty = ['["rp",', ',"system/PRESETDIRTY"]\n']

cmd_select_factory_preset_at = ['["mc",', ',"banks/factory/', '","preset"]\n'] # ["mc",x,"banks/factory/x","preset"] or ["mc",x,"banks/user/x","preset"]

cmd_select_user_preset_at = ['["mc",', ',"banks/user/', '","preset"]\n']

cmd_store_user_preset = ['["mc",', ',"preset","banks/user/', '"]\n']  # ["mc",x,"preset", "banks/user/x"]

cmd_store_factory_preset = ['["mc",', ',"preset","banks/factory/', '"]\n']

cmd_set_fx_model = ['["ssc",', ',"preset/fxc/', '",{"fx":{"name":"', '"}}]\n']  # change fx model e.g. : ["ssc",132,"preset/fxc/4",{"fx":{"name":"dist.FUZZLATR"}}]

cmd_send_preset = ['["ssc", ', ', "", {"preset":','}]'] # send preset to device ["ssc", 110, "", {json_preset...}]  followed by cmd_set_preset_dirty

cmd_set_preset_name = ['["sp",', ',"preset/name","', '"]\n']  # ["sp",108,"preset/name","blabla"]

