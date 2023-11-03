# coding: utf-8

import serial
import serial.tools.list_ports
from commands import *
from files import Configuration
import logging
from time import sleep


class Device:

    def __init__(self):
        self.connected = False
        self.ser = None
        self.port = None
        self.baudrate = 115200
        self.timeout = 0.0
        self.read_buffer = 4096
        self.response = ''
        self.loaded = False
        self.banks = {}
        self.command_id = 0
        self.active_preset = None
        self.stop_reading = False

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.NOTSET)
        self.logger.disabled = not Configuration().get('debug')

    def detect_device(self):
        ports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(ports):
            if "RP360" in desc:
                logging.info("Found connected device : {}: {} [{}]".format(port, desc, hwid))
                Configuration().write('device', port)
                return True
        return False

    def open(self):
        self.port = Configuration().get('device')
        try:
            self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        except serial.SerialException as e:
            logging.critical(e.strerror)
            return False
        else:
            self.connected = True
            self.ser.flushInput()
            self.ser.flushOutput()
            return True

    def close(self):
        if self.connected:
            self.ser.flushInput()
            self.ser.flushOutput()
            logging.info('Port %s closed.', self.port)
            self.ser.close()
            self.connected = False

    def _write(self, command):
        self.ser.write(command.encode())
        logging.info('Sending: %s', command)
        self.command_id += 1
        sleep(0.5)

    def _read(self, read_type='default'):
        if read_type == 'default':
            self.stop_reading = False
        if not self.stop_reading:
            self.response = self.ser.read(self.ser.in_waiting)
            sleep(.2)
            self.ser.flushInput()
            if b'nack' in self.response:
                logging.error("NACK - Command failed : '%s'", self.response)
                return b''
            else:
                logging.info('Received: %s', self.response)
                if read_type == 'preset' and (']'.encode() in self.response):
                    self.stop_reading = True
                return self.response
        return b''

    def state(self):
        self._write(cmd_state)
        self.response = self._read()
        if self.response is None:
            logging.error('Device is not ready. Please reconnect your device and try again...')

    def version(self):
        self._write(cmd_version)
        self.response = self._read()

    def sbs(self):
        self._write(cmd_sbs)
        self.response = self._read()

    def sync(self):
        self._write(cmd_sync)
        self.response = self._read()

    def get_preset_name_at_index(self, index, bank_type='factory'):
        """
        get the name of the preset at position index from the factory or user bank
        :param index: (int) position of the preset in the bank
        :param bank_type: (str) factory or user
        :return: (str) preset name
        """
        if bank_type == 'factory':
            self._write(cmd_get_factory_preset_name[0] + str(self.command_id) + cmd_get_factory_preset_name[1]+str(index)
                        + cmd_get_factory_preset_name[2])
        elif bank_type == 'user':
            self._write(cmd_get_user_preset_name[0] + str(self.command_id) + cmd_get_user_preset_name[1] + str(index) +
                        cmd_get_user_preset_name[2])
        self.response = self._read()
        decoded = self.response.decode(encoding='ISO-8859-1', errors='ignore')
        rep = decoded[decoded.find('['):decoded.rfind(']')]
        s = rep.split(',')
        preset_name = s[3].strip('"')
        return preset_name

    def get_banks(self):
        if not self.loaded:
            self.banks.update({'F': {}})
            self.banks.update({'U': {}})
            for i in range(99):  # factory bank
                self.banks.get('F').update({i+1: self.get_preset_name_at_index(i, 'factory')})
            for i in range(99):  # user bank
                self.banks.get('U').update({i+1: self.get_preset_name_at_index(i, 'user')})
            self.loaded = True
        return self.banks

    def get_active_preset(self):
        self._write(cmd_get_preset0[0] + str(self.command_id) + cmd_get_preset0[1])
        str1 = self._read(read_type='preset')
        self._write('\x55\x06\x00\x02\x00\x72\x00\x42\x44')
        str2 = self._read(read_type='preset')
        self._write('\x55\x06\x00\x02\x00\x73\x00\x42\x43')
        str3 = self._read(read_type='preset')
        start_byte = 10
        if str3 != b'' and str3[1] != 0:
            start_byte = 8
        self.active_preset = str1[10:len(str1) - 1] + str2[10:len(str2) - 1] + str3[start_byte:len(str3) - 1]
        self.active_preset = self.active_preset[self.active_preset.find('{'.encode()):self.active_preset.rfind(']'.encode()):]
        logging.info('Current preset: %s', self.active_preset)
        return self.active_preset

    def select_preset_at(self, index, bank_type):
        if bank_type == 'factory':
            self._write(cmd_select_factory_preset_at[0] + str(self.command_id) + cmd_select_factory_preset_at[1] + str(index) + cmd_select_factory_preset_at[2])
        elif bank_type == 'user':
            self._write(cmd_select_user_preset_at[0] + str(self.command_id) + cmd_select_user_preset_at[1] + str(index) + cmd_select_user_preset_at[2])
        else:
            return
        sleep(self.timeout)
        self.response = self._read()

    def set_preset_dirty(self):
        self._write(cmd_set_preset_dirty[0] + str(self.command_id) + cmd_set_preset_dirty[1])
        self.response = self._read()

    def store_preset(self, index, bank_type):
        if bank_type == 'factory':
            self._write(cmd_store_factory_preset[0] + str(self.command_id) + cmd_store_factory_preset[1] + str(index) + cmd_store_factory_preset[2])
        elif bank_type == 'user':
            self._write(cmd_store_user_preset[0] + str(self.command_id) + cmd_store_user_preset[1] + str(index) +
                        cmd_store_user_preset[2])
        else:
            return
        self.response = self._read()

    def set_fx_value(self, fx_path, value):
        """
        Assign a value to an effect property
        :param fx_path: (string) path to fx in a filepath format, e.g. fxc/2/fx/ATTACK or ENABLE
        :param value: (int) value to set for the fx
        """
        self._write(cmd_set_preset_value[0] + str(self.command_id) + cmd_set_preset_value[1] + fx_path +
                    cmd_set_preset_value[2] + str(value) + cmd_set_preset_value[3])
        self._read()

    def set_fx_model(self, fx_name, chain_position):
        """
        change fx model to this fx_name at this position in chain
        :param fx_name: name of the new fx (str)
        :param chain_position: position in the chain (int)
        """
        self._write(cmd_set_fx_model[0] + str(self.command_id) + cmd_set_fx_model[1] + str(chain_position) + cmd_set_fx_model[2] + fx_name + cmd_set_fx_model[3])
        self._read()

    def set_preset_name(self, name):
        self._write(cmd_set_preset_name[0] + str(self.command_id) + cmd_set_preset_name[1] + name + cmd_set_preset_name[2])

    def send_preset(self, preset):
        '''
        Imports loaded preset to the device
        :param preset:
        :return:
        '''
        cmd = cmd_send_preset[0] + str(self.command_id) + cmd_send_preset[1] + preset.dumps() + cmd_send_preset[2]
        cmd = self._format_command(cmd)
        self._write(cmd)
        self.response = self._read()
        #self.set_preset_dirty()
        self.active_preset = preset


    def _format_command(self, text):
        '''
        Formats command : removing spaces then splitting in chunks of 249 chars.
        Only used for sending a preset to device with 'ssc'.
        :param text: command
        :return:
        '''
        quote = False
        temp, cmd = '', ''
        for i in range(0, len(text)):
            if text[i] == '"' and quote is False:
                quote=True
                temp = temp + text[i]
            elif text[i] == '"' and quote is True:
                quote = False
                temp = temp + text[i]
            elif text[i] != ' ' and quote is True:
                temp = temp + text[i]
            elif quote is False and text[i] != ' ':
                temp = temp + text[i]
            elif quote is True and text[i] == ' ':
                temp = temp + text[i]
        for i in range(0, len(temp), 249):  # command needs to be split in chunks of 249 chars
            cmd = cmd + temp[i:i + 249] + '\n'
        return cmd
