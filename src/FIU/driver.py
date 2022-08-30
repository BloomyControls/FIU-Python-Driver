from cmd import Cmd
from operator import mod
from time import sleep
from serial import rs485
import sys
from fiu_types import *

class FIU(object):
    """RS485 Driver class for the Bloomy Fault Insertion Unit
       Provides interface to connect with an FIU via USB Serial Comm Port
       and functionality mirroring the functions and capabilities of the 
       Bloomy FIU LabVIEW Driver"""
    
    def __init__(self, mod_ids: list[int], resource_name: str, port_settings: DefaultPortSettings) -> None:
        """Constructor for 
        """
        self.module_IDs = []
        #make sure all Box IDs are in the range required for RS-485 for the Fault Insertion Unit
        for id in mod_ids:
            if id in range(0, 8):
                mod_ids.append(id)
            else: raise IndexError("FIU Box IDs must be in range 0-7 for RS-485 communication")
        self.module_IDs.sort()

        #Initialize the state manager and set all channels on all modules to be in disconnected state
        self._state_mgr = StateManager(self.module_IDs)
        self._state_mgr.set_all_state(self.module_IDs, FIUState.DISCONNECTED)

        #Initialize port resource name and create an object for the pyserial RS485 serial subclass 
        self._sharedDMM = False
        self.resource = resource_name
        self._port_cfg = port_settings
        self.serial = rs485.RS485(self.resource)
        self.open_RS485()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, tb):
        self.close()
        if exc_type is not None:
            sys.tracebacklimit.print_exception(exc_type, exc_val, tb)
            return False
        else:
            return True

    def open_RS485(self) -> None:
        """Opens an RS-485 connection to the FIU."""
        #Set port settings for the interface class from custom dataclass with port settings 
        #according to FIU communication specification
        self.serial.baudrate = self._port_cfg.baud_rate
        self.serial.bytesize = self._port_cfg.byte_size
        self.serial.parity   = self._port_cfg.parity
        self.serial.stopbits = self._port_cfg.stop_bits
        #Configure rs485 mode with default settings
        self.serial.rs485_mode = rs485.RS485Settings
        #open the port connection to begin communication session
        self.serial.open()

    def close(self) -> None:
        """Closes a connection to the FIU."""
        #connect all channels before closing
        self.set_open_circuit_fault_all(False)
        self.serial.close()

    
    def configure(self, shared_dmm: bool) -> None:
        """Set whether the system is using a shared DMM across multiple FIUs."""
        self._sharedDMM = shared_dmm

    def set_open_circuit_fault(self, mod_id, channel, enable_disable: bool) ->None:
        """Enable (disconnect) or disable (connect) an open circuit fault at a specified channel."""
        if(self.__valid_module(mod_id) and self.__valid_channel(channel)):
            if enable_disable:
                #Disconnected state
                cmd_char = "D"
                new_state = FIUState.DISCONNECTED
            else:
                #Connected state
                cmd_char = "C"
                new_state = FIUState.CONNECTED
            #Check to see if the new open circuit state is a valid transition
            safe = self._state_mgr.check_shared_DMM_transition(new_state) if self._sharedDMM else self._state_mgr.check_transition(mod_id, channel, new_state)
            if(safe):
                #construct the SCPI command to write to the FIU
                cmd = f"{cmd_char}{mod_id}{channel:02d}"
                self.__write_cmd(cmd)
                #update the channel's state in the state manager
                self._state_mgr.set_channel_state(mod_id, channel, new_state)
            else:
                raise FIUException(5010)
        else:
            raise FIUException(5051)

    def set_open_circuit_fault_all(self, enable_disable: bool) -> None:
        """Enable (disconnect) or disable (connect) open circuit faults at all channels in the system."""
        if enable_disable:
            #Disconnected state
            cmd_char = "D"
            new_state = FIUState.DISCONNECTED
        else:
            #Connected state
            cmd_char = "C"
            new_state = FIUState.CONNECTED
        #set open circuit state for all channels on all modules
        for box in self.module_IDs:
            self.__write_cmd(f"{cmd_char}{box}99")
        #Update the state in StateManager
        self._state_mgr.set_all_state(self.module_IDs)


    def set_short_circuit_fault(self, mod_id, channel):
        """Sets a fault to ground at the specified channel. 
        (Only one channel in the system can be set to ground fault at a time.)"""
        if(self.__valid_module(mod_id) and self.__valid_channel(channel)):
            #Check to see if the fault state at given channel is a valid transition
            if self._sharedDMM:
                safe = self._state_mgr.check_shared_DMM_transition(FIUState.FAULT_TO_GND)  
            else:
                safe = self._state_mgr.check_transition(mod_id, channel, FIUState.FAULT_TO_GND)
            if(safe):
                #construct the SCPI command to write to the FIU
                cmd = f"F{mod_id}{channel:02d}"
                self.__write_cmd(cmd)
                #update the channel's state in the state manager
                self._state_mgr.set_channel_state(mod_id, channel, FIUState.FAULT_TO_GND)
            else:
                raise FIUException(5010)
        else:
            raise FIUException(5051)

    def set_voltage_measurement(self, mod_id, channel):
        """Sets the specified channel to voltage mode for DMM cell voltage measurement. 
        (Only one channel in the system can be set to measurement mode at a time.)"""
        if(self.__valid_module(mod_id) and self.__valid_channel(channel)):
            #Check to see if another channel is set to voltage measurement mode
            if self._sharedDMM:
                safe = self._state_mgr.check_shared_DMM_transition(FIUState.VOLT_MEASUREMENT)  
            else:
                safe = self._state_mgr.check_transition(mod_id, channel, FIUState.VOLT_MEASUREMENT)
            if(safe):
                #construct the SCPI command to write to the FIU
                cmd = f"V{mod_id}{channel:02d}"
                self.__write_cmd(cmd)
                #update the channel's state in the state manager
                self._state_mgr.set_channel_state(mod_id, channel, FIUState.VOLT_MEASUREMENT)
            else:
                raise FIUException(5010)
        else:
            raise FIUException(5051)

    def set_current_measurement(self, mod_id, channel):
        """Sets the specified channel to current mode for DMM bypass current measurement. 
        (Only one channel in the system can be set to measurement mode at a time.)"""
        if(self.__valid_module(mod_id) and self.__valid_channel(channel)):
            #Check to see if another channel is set to current measurement
            if self._sharedDMM:
                safe = self._state_mgr.check_shared_DMM_transition(FIUState.CURR_MEASUREMENT)  
            else:
                safe = self._state_mgr.check_transition(mod_id, channel, FIUState.CURR_MEASUREMENT)
            if(safe):
                #construct the SCPI command to write to the FIU
                cmd = f"I{mod_id}{channel:02d}"
                self.__write_cmd(cmd)
                #update the channel's state in the state manager
                self._state_mgr.set_channel_state(mod_id, channel, FIUState.CURR_MEASUREMENT)
            else:
                raise FIUException(5010)
        else:
            raise FIUException(5051)

    def relay_state(self, mod_id: int) -> list[str]:
        """Returns the state for every channel in the FIU system."""
        if(self.__valid_module(mod_id)):
            system_status = [] 
            status = self.__write_cmd(f"S{mod_id}")
            for i in range(24):
                stat = status[i]
                if   stat == 'C': system_status.add(FIUState.CONNECTED.name)
                elif stat == 'D': system_status.add(FIUState.DISCONNECTED.name)
                elif stat == 'V': system_status.add(FIUState.VOLT_MEASUREMENT.name)
                elif stat == 'I': system_status.add(FIUState.CURR_MEASUREMENT.name)
                elif stat == 'F': system_status.add(FIUState.FAULT_TO_GND.name)
                else:             system_status.add(FIUState.RESET.name)
            return system_status
        else:
            raise FIUException(5075)

    def relay_contact_cycle_count(self, mod_id: int, channel: int):
        """Returns the number of cycles the relays on the specified channel have experienced."""
        if(self.__valid_module(mod_id) and self.__valid_channel(channel)):
            cmd = f"N{mod_id}{channel:02d}"
            ret_data = self.__write_cmd(cmd)
            relay_counts = RelayCount(
                K1 = int(ret_data[0:7]),
                K2 = int(ret_data[8:15]),
                K3 = int(ret_data[16:23]),
                K4 = int(ret_data[24:31]),
                K5 = int(ret_data[32:])
            )
        else:
            raise FIUException(5075)

    def software_version(self, mod_id: int) -> str:
        """Returns the current version of the software running on the FIU."""
        #valid module check is disabled in labVIEW driver... so let's just send it
        return self.__write_cmd(f"H{mod_id}")
    
    def interlock_state(self, mod_id: int) -> bool:
        """Returns the state of the 24V interlock input on the FIU (Active or Inactive)."""
        if(self.__valid_module(mod_id)):
            int_state = self.__write_cmd(f"L{mod_id}")
            return False if int_state == '0' else '1'
        else:
            raise FIUException(5075)

    def interlock_override(self, mod_id: int, enable_disable: bool) -> None:
        """Sets the 24V interlock input on the FIU to active (enable) or inactive (disable)."""
        if(self.__valid_module(mod_id)):
            cmd = f"O{mod_id}{'1' if enable_disable else '0'}"
            self.__write_cmd(cmd)
        else:
            raise FIUException(5075)

    
    def __valid_module(self, mod_id: int) -> bool:
        """Ensures provided Module ID exists in the list of FIU Modules initialized on the system"""
        return True if mod_id in self.module_IDs else False 

    def __valid_channel(self, channel) -> bool:
        """Ensures entered channel number is within valid range of 1-24"""
        return True if (channel in range (1, 25)) else False

    def __add_CRC(self, msg: str) -> str:
        """Add checksum code and newline termination character to the message"""
        #CRC is calculated from the sum of the message's u8 byte array modulo
        encoded_msg_sum = sum(bytes(msg, 'utf-8'))
        #Take only the hex value characters from the hex string  
        CRC = hex(encoded_msg_sum % 256)[2:]
        #add end line constant for the termination character(s)
        return msg + CRC + '\r'

    def __write_cmd(self, msg: str) -> str:
        """Write a message out to the serial device and return the parsed return data"""
        #clear the input and output buffers on the port
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        #add checksum and termination to the message, then write command out to device 
        msg = self.__add_CRC(msg)
        self.serial.write(msg)
        #wait 100 ms for response
        sleep(0.0100)
        ret_msg = self.serial.read(self.serial.in_waiting)
        return self.__check_return_msg(msg, ret_msg)

    def __check_return_msg(self, sent_cmd: str, readbuff: str) -> str:
        """Parses the returned message buffer based on the return code"""
        return_msg = readbuff[0]
        if return_msg is '0':
            #Success - No Data
            return ""
        elif return_msg is '1':
            #Success - Data
            #Remove Return Code (1), CRC(2), and CR (1) characters
            return readbuff[1:1+(len(readbuff)-4)]
        elif return_msg is '2':
            #Error msg
            return FIUException(5003, readbuff, sent_cmd)
        elif return_msg is '3':
            #Error Data
            #Error returned when attempting to short multiple channels to the bus
            #Remove Return Code (1), CRC(2), and CR (1) characters
            return FIUException(5004, readbuff[1:1+(len(readbuff)-4)])
        else:
            #Invalid Response to CMD
            return FIUException(5002, sent_cmd, readbuff)
   