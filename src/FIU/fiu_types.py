from dataclasses import dataclass
import serial
from enum import IntEnum

class FIUException(BaseException):
    def __init__(self, code: int, *args):
        self.code = code
        if code ==   5002: 
            self.message = f"FIU Module\nInvalid Response to cmd {args[0]}\n{'Device Not Found' if args[1] is None else args[1]}"
        elif code == 5003: 
            self.message = f"{args[0]}\nSource CMD: {args[1]}"
        elif code == 5004: 
            self.message = args[0]
        elif code == 5010: 
            self.message = f"Unable to set channel {args[0]} state to {args[1]}. There is another channel currently using the DMM or Fault in this module."
        elif code == 5051: 
            self.message = "The channel input is out of range"
        elif code == 5075: 
            self.message = "Module input is out of range."
        else: self.message = args[0]
    def __str__(self):
        return f"FIU Module Error\nCode: {self.code}\nDetails: {self.message}"


@dataclass
class DefaultPortSettings:
    """Data class containing the default configuration used 
    for RS485 communication with the Fault Insertion Unit"""
    baud_rate: int = 115200
    byte_size: int = 8
    parity: serial.PARITY_NONE = 'N'
    stop_bits: serial.STOPBITS_ONE = 1

@dataclass
class RelayCount:
    K1 : int = 0
    K2 : int = 0
    K3 : int = 0
    K4 : int = 0
    K5 : int = 0

class FIUState(IntEnum):
    RESET = 0
    CONNECTED = 1
    DISCONNECTED = 2
    VOLT_MEASUREMENT = 3
    CURR_MEASUREMENT = 4
    FAULT_TO_GND = 5


class StateManager(object):
    """Class used to manage safe state transition between channel fault states.
    An error will occur when trying to transition to an unsafe state, before ever reaching the FIU. 
    This prevents unintentional damage to the system."""
    def __init__(self, box_ids: list):
        self._boxIDs = box_ids
        self.registry = dict()

    def __get_all_state(self) -> list:
        """Private accessor to return the channel fault state list for all initialized Module IDs"""
        all_states = list[list[FIUState]]
        for id in self._boxIDs: 
            all_states.add(self.registry["%d" % id])
        return all_states    
    
    def __get_channel_state(self, module: int, channel: int) -> FIUState:
        """Private accessor for the fault state of a specific channel on the provided Module"""
        states = self.registry["%d" % module]
        chan_state = states[channel-1]
        return chan_state

    def __get_module_state(self, module: int) -> list:
        """Private accessor for the fault states of the provided Module"""
        return self.registry["%d" % module]
        

    def set_module_state(self, module: int, state: FIUState) -> None:
        """Set the the fault state for all channels in the designated module, creating/replacing 
        the registry entry for the module ID"""
        new_states = [state]*24
        self.registry["%d" % module] = new_states
    
    def set_channel_state(self, module: int, channel: int, state: FIUState) -> None:
        """Set the fault state for a specific channel in the provided module's registry entry,
        replacing the registry value with the updated list of channel fault states"""
        key = "%d" % module
        mod_states = self.registry[key]
        mod_states[channel-1] = state
        self.registry[key] = mod_states

    def set_all_state(self, all_modules: list, state: FIUState) -> None:
        """Set all channel states for a given list of FIU Module IDs"""
        for mod in all_modules:
            self.set_module_state(mod, state)
        
    def check_transition(self, mod_id: int, channel: int, next_state: FIUState) -> bool:
        """Validates that transitioning a channel to next_state will result in safe conditions for 
        the designated FIU module"""
        chan = channel - 1
        module_states = self.__get_module_state(mod_id)
        if(FIUState.VOLT_MEASUREMENT <= next_state <= FIUState.FAULT_TO_GND):
            check = []
            i = 0
            for state in module_states:
                if(i is not chan):
                    check.append(state in range(FIUState.VOLT_MEASUREMENT, FIUState.FAULT_TO_GND + 1))
            if any(check):
                return False
            else:
                return True
        else:
            return True
    
    def check_shared_DMM_transition(self, next_state: FIUState) -> bool:
        """Validates transition to the next state is valid when the FIU is in shared DMM mode"""
        all_mod_states = self.__get_all_state()
        if(FIUState.VOLT_MEASUREMENT <= next_state <= FIUState.FAULT_TO_GND):
            check = []
            for mod in all_mod_states:
                for state in mod:
                    check.append(state in range(FIUState.VOLT_MEASUREMENT, FIUState.FAULT_TO_GND + 1))
            #
            if any(check): 
                return False
            else:
                return True
        else:
            return True