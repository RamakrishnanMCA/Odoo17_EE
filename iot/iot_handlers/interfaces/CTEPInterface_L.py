# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ctypes
import subprocess
import logging

from odoo.addons.hw_drivers.interface import Interface
from odoo.modules.module import get_resource_path
from odoo.addons.hw_drivers.iot_handlers.lib.ctypes_terminal_driver import import_ctypes_library, create_ctypes_string_buffer


_logger = logging.getLogger(__name__)

if not get_resource_path("hw_drivers", "iot_handlers", "lib", "ctep", "libeasyctep.so"):
    # Load library
    load_library = get_resource_path("hw_drivers", "iot_handlers", "lib", "load_worldline_library.sh")

    try:
        subprocess.check_call(["sudo", "sh", load_library])
    except subprocess.CalledProcessError as e:
        _logger.error('A error encountered : %s ', e.output)

easyCTEP = import_ctypes_library('ctep', 'libeasyctep.so')

# CTEPManager* createCTEPManager(void);
easyCTEP.createCTEPManager.restype = ctypes.c_void_p
# int connectedTerminal(CTEPManager* manager, char* terminal_id, std::shared_ptr<ect::CTEPTerminal> terminal)
easyCTEP.connectedTerminal.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]

class CTEPInterface(Interface):
    _loop_delay = 10
    connection_type = 'ctep'

    def __init__(self):
        super(CTEPInterface, self).__init__()
        self.manager = easyCTEP.createCTEPManager()

    def get_devices(self):
        devices = {}
        terminal_id = create_ctypes_string_buffer()
        device = ctypes.c_void_p()
        if easyCTEP.connectedTerminal(self.manager, terminal_id, ctypes.byref(device)):
            devices[terminal_id.value.decode('utf-8')] = device
        return devices
