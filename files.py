import pathlib
import json


def get_temp_file_path():
    path = pathlib.Path.home().as_posix() + '/.cache/pyrp360'
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    return path + '/tmp_current_preset.rp360p'


class Configuration:
    def __init__(self):
        self.file_path = 'config.json' #pathlib.Path.home().as_posix() + '/.config/pyrp360/config.json'
        self.data = None
        with open(self.file_path, 'r') as f:
            self.data = json.load(f)
        f.close()

    def write(self, key, value):
        self.data.update({key: value})
        j = json.JSONEncoder()
        with open(self.file_path, 'w') as f:
            f.write(j.encode(self.data))
        f.close()

    def get(self, key):
        return self.data.get(key)


