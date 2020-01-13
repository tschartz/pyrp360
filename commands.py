### system commands

cmd_state = 'U\x16\x00C\x00\x00\x00\x00["rp",0,"STATE"]'

cmd_version = '["rp",1,"VERSION"]' #'U\x18\x00C\x00\x01\x00\x00["rp",1,"VERSION"]\xD3'

cmd_sbs = '["sbs",2,"",1]'

cmd_sync = '["rp",3,"system/SYNC"]'

### preset commands

cmd_get_factory_preset_name = ['["rp",', ',"banks/factory/', '/name"]']

cmd_get_user_preset_name = ['["rp",', ',"banks/user/', '/name"]']

cmd_get_last_preset = '["rp",6,"system/LAST PRES"]'

cmd_get_preset0 = '["rc",', ',"preset"]'

cmd_get_preset1 = '\x55\x06\x00\x02\x00\x72\x00\x42\x44'

cmd_get_preset2 = '\x55\x06\x00\x02\x00\x73\x00\x42\x43'

cmd_set_preset_value = ['["sp",', ',"', '",', ']']

cmd_set_preset_dirty = ['["rp",', ',"system/PRESETDIRTY"]']

cmd_select_factory_preset_at = ['["mc",', ',"banks/factory/', '","preset"]'] # ["mc",x,"banks/factory/x","preset"] or ["mc",x,"banks/user/x","preset"]

cmd_select_user_preset_at = ['["mc",', ',"banks/user/', '","preset"]']

cmd_store_user_preset = ['["mc",', ',"preset","banks/user/', '"]']  # ["mc",x,"preset", "banks/user/x"]

cmd_store_factory_preset = ['["mc",', ',"preset","banks/factory/', '"]']

cmd_send_preset = ['["ssc", ', ', "", {"preset":','}]'] # send preset to device ["ssc", 110, "", {json_preset...}]  followed by cmd_set_preset_dirty

cmd_set_preset_name = ['["sp",', ',"preset/name","', '"]']  # ["sp",108,"preset/name","blabla"]

### fx commands

cmd_set_fx_model = ['["ssc",', ',"preset/fxc/', '",{"fx":{"name":"', '"}}]']  # change fx model e.g. : ["ssc",132,"preset/fxc/4",{"fx":{"name":"dist.FUZZLATR"}}]

cmd_delete_fx = ['["dc",', ', "preset/fxc/', '"]'] # ["dc", 102, "preset/fxc/2"] delete fx #2 from fx chain

cmd_reorder_fx = ['["shc",', ',"preset/fxc",', ']'] #  ["shc", 103, "preset/fxc", [3, 0, 1, 2, 4, 5, 6]] : reposition fx #3 to pos # 0

