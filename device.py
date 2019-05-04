# coding: utf-8

import serial
import serial.tools.list_ports
from commands import *
from files import Configuration
import logging
from time import sleep
import string
import re


class Device:

    def __init__(self):
        self.connected = False
        self.ser = None
        self.port = None
        self.baudrate = 115200
        self.timeout = 0.5
        self.read_buffer = 4096
        self.response = ''
        self.loaded = False
        self.banks = {}
        self.command_id = 0
        self.active_preset = None
        self.stop_reading = False
        self.sleeptime = 0.2

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
        self.logger.critical("No device detected in ", ports)
        return False

    def open(self):
        self.port = Configuration().get('device')
        try:
            self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
        except serial.SerialException:
            logging.critical('Port %s could not be opened.', self.port)
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

    def _query(self, command):
        self.ser.write(command.encode())
        logging.info('Sending: %s', command)
        self.command_id += 1
        sleep(self.sleeptime)

    def _read(self):
        self.read_buffer = self.ser.in_waiting - 1
        resp = self.ser.read(self.read_buffer)
        self.ser.flushInput()
        resp = resp[self._find_header_end(resp):]
        logging.info('Received: %s', resp)
        decoded = resp.decode('utf-8', 'ignore')
        decoded = decoded[decoded.rfind('['):]
        utf8 = decoded
        if 'nack' in utf8:
            logging.error("NACK - Command failed : '%s'", resp)
            self.ser.flushInput()
            return None
        self.ser.flushInput()
        return utf8

    def state(self):
        self._query(cmd_state)
        self.response = self._read()
        if self.response is None:
            logging.error('Device is not ready. Please reset your device and try again...')

    def version(self):
        self._query(cmd_version)
        self.response = self._read()

    def sbs(self):
        self._query(cmd_sbs)
        self.response = self._read()

    def sync(self):
        self._query(cmd_sync)
        self.response = self._read()

    def get_preset_name_at_index(self, index, bank_type='factory'):
        """
        get the name of the preset at position index from the factory or user bank
        :param index: (int) position of the preset in the bank
        :param bank_type: (str) factory or user
        :return: (str) preset name
        """
        if bank_type == 'factory':
            self._query(cmd_get_factory_preset_name[0] + str(self.command_id) + cmd_get_factory_preset_name[1]+str(index)
                        + cmd_get_factory_preset_name[2])
        elif bank_type == 'user':
            self._query(cmd_get_user_preset_name[0] + str(self.command_id) + cmd_get_user_preset_name[1] + str(index) +
                        cmd_get_user_preset_name[2])
        self.response = self._read()
        rep = self.response[self.response.rfind('['):self.response.rfind(']')]
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
        self._query(cmd_get_preset0[0] + str(self.command_id) + cmd_get_preset0[1])
        part1 = self._read_active_preset_part1()
        self._query(cmd_get_preset1)
        part2 = self._read_active_preset_part2()
        part3 = ''
        if not self.stop_reading:
            self._query(cmd_get_preset2)
            part3 = self._read_active_preset_part3()
        preset = part1 + part2 + part3
        preset = self._remove_preset_header(preset)
        self._json_validate(preset)
        logging.info('Current preset: %s', preset)
        self.active_preset = preset
        return self.active_preset

    def select_preset_at(self, index, bank_type):
        if bank_type == 'factory':
            self._query(cmd_select_factory_preset_at[0] + str(self.command_id) + cmd_select_factory_preset_at[1] + str(index) + cmd_select_factory_preset_at[2])
        elif bank_type == 'user':
            self._query(cmd_select_user_preset_at[0] + str(self.command_id) + cmd_select_user_preset_at[1] + str(index) + cmd_select_user_preset_at[2])
        else:
            return
        sleep(self.timeout)
        self.response = self._read()

    def set_preset_dirty(self):
        self._query(cmd_set_preset_dirty[0] + str(self.command_id) + cmd_set_preset_dirty[1])
        self.response = self._read()

    def store_preset(self, index, bank_type):
        if bank_type == 'factory':
            self._query(cmd_store_factory_preset[0] + str(self.command_id) + cmd_store_factory_preset[1] + str(index) + cmd_store_factory_preset[2])
        elif bank_type == 'user':
            self._query(cmd_store_user_preset[0] + str(self.command_id) + cmd_store_user_preset[1] + str(index) +
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
        self._query(cmd_set_preset_value[0] + str(self.command_id) + cmd_set_preset_value[1] + fx_path +
                    cmd_set_preset_value[2] + str(value) + cmd_set_preset_value[3])
        self._read()

    def set_fx_model(self, fx_name, chain_position):
        """
        change fx model to this fx_name at this position in chain
        :param fx_name: name of the new fx (str)
        :param chain_position: position in the chain (int)
        """
        self._query(cmd_set_fx_model[0] + str(self.command_id) + cmd_set_fx_model[1] + str(chain_position) + cmd_set_fx_model[2] + fx_name + cmd_set_fx_model[3])
        self._read()

    def set_preset_name(self, name):
        self._query(cmd_set_preset_name[0] + str(self.command_id) + cmd_set_preset_name[1] + name + cmd_set_preset_name[2])

    def send_preset(self, preset):
        '''
        Imports loaded preset to the device
        :param preset:
        :return:
        '''
        cmd = cmd_send_preset[0] + str(self.command_id) + cmd_send_preset[1] + preset.dumps() + cmd_send_preset[2]
        cmd = self._format_command(cmd)
        self._query(cmd)
        self.response = self._read()
        #self.set_preset_dirty()
        self.active_preset = preset

    def _read_active_preset_part1(self):
        sleep(self.sleeptime)
        s = self.ser.read(self.ser.in_waiting - 1)
        self.ser.flushInput()
        d = s.decode('utf-8', 'ignore')
        a1 = d[d.rfind('['):]
        a1 = a1[a1.find('{'):]
        a1 = ''.join(x if x in string.printable else '' for x in a1)
        self.response = s
        logging.info('Received: %s', s)
        return a1

    def _read_active_preset_part2(self):
        sleep(self.sleeptime)
        s = self.ser.read(self.ser.in_waiting - 1)
        self.ser.flushInput()
        s = s[self._find_header_end(s):]
        a2 = s.decode('utf-8', 'ignore')
        a2 = ''.join(x if x in string.printable else '' for x in a2)
        if a2[len(a2) - 1] == ']':
            a2 = a2[:len(a2) - 1]
            self.stop_reading = True
        logging.info('Received: %s', s)
        return a2

    def _read_active_preset_part3(self):
        sleep(self.sleeptime)
        s = self.ser.read(self.ser.in_waiting - 1)
        self.ser.flushInput()
        s = s[self._find_header_end(s):]
        a3 = s.decode('utf-8', 'ignore')
        a3 = ''.join(x if x in string.printable else '' for x in a3)
        if a3[len(a3) - 1] == ']':
            a3 = a3[:len(a3) - 1]
        logging.info('Received: %s', s)
        return a3

    def _find_header_end(self, buffer):
        for i in range(0, len(buffer) - 1):
            if buffer[i] == 0 and buffer[i + 1] == 0:
                return i + 2
        return 0

    def _remove_preset_header(self, text):
        idx = text.find(':')
        t = text[idx + 1:len(text) - 1]
        return t

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

    def _json_validate(self, text):
        pattern = re.compile('\{.*\:\{.*\:.*\}\}')
        if pattern.match(text) is None:
            logging.error('*** Error in preset data format.')
            return False
        else:
            return True
