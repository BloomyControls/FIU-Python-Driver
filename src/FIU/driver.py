from .fiu_types import *
from .interfaces import *

class FIU(object):
    """RS485 Driver class for the Bloomy Fault Insertion Unit
       Provides interface to connect with an FIU via USB Serial Comm Port
       and functionality mirroring the functions and capabilities of the 
       Bloomy FIU LabVIEW Driver"""
    
    def __init__(self, mod_ids: list, comm_resource: str) -> None:
        """Constructor for 
        """
        self.module_IDs = []
        #make sure all Box IDs are in the range required for RS-485 for the Fault Insertion Unit
        for id in mod_ids:
            if id in range(0, 8):
                self.module_IDs.append(id)
            else: raise IndexError(f"Invalid Module ID: {id}\nFIU Module IDs must be in range 0-7 for RS-485 communication")
        self.module_IDs.sort()

        #Initialize the state manager and set all channels on all modules to be in disconnected state
        self.__state_mgr = StateManager(self.module_IDs)
        self.__state_mgr.set_all_state(self.module_IDs, FIUState.CONNECTED)

        #Initialize port resource name and create an object for the pyserial RS485 serial subclass 
        self._sharedDMM = False
        self.resource = comm_resource
        self.interface = RS485(comm_resource, DefaultPortSettings())


    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback): 
        self.disconnect()
        print(f"Closed connection with FIU on {self.resource}. All channel relays have been reconnected")
        if exc_type is not None:
            print("\nExecution type:", exc_type)
            print("\nExecution value:", exc_value)
            print("\nTraceback:", traceback)
    
    def connect(self) -> None:
        self.interface.open()
        print(f"Connection to Fault Insertion Unit Module IDs: {self.module_IDs} established on port {self.resource}")
    
    def disconnect(self) -> None:
        self.set_open_circuit_fault_all(False)
        self.interface.close()
        print(f"Connection with FIU Module IDs {self.module_IDs} on {self.resource} has been successfully closed")

    def configure(self, shared_dmm: bool) -> None:
        """Set whether the system is using a shared DMM across multiple FIUs."""
        self._sharedDMM = shared_dmm

    def set_open_circuit_fault(self, mod_id: int, channel: int, enable_disable: bool = True) -> None:
        """Enable (True = disconnect) or disable (False = connect) an open circuit fault at a specified channel."""
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
            if(self.__check_transition(new_state, mod_id, channel)):
                #construct the SCPI command to write to the FIU
                cmd = f"{cmd_char}{mod_id}{channel:02d}"
                self.interface.write_cmd(cmd)
                #update the channel's state in the state manager
                self.__state_mgr.set_channel_state(mod_id, channel, new_state)
            else:
                raise FIUException(5010)
        else:
            raise FIUException(5051)


    def set_open_circuit_fault_all(self, enable_disable: bool = True) -> None:
        """Enable (True = disconnect) or disable (False = connect) open circuit faults at all channels in the system."""
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
            cmd = f"{cmd_char}{box}99"
            self.interface.write_cmd(cmd)
        #Update the state in StateManager
        self.__state_mgr.set_all_state(self.module_IDs, new_state)

    def set_channel_connected(self, mod_id: int, channel: int) -> None:
        """Dedicated method to set open circuit fault state of the provided channel to CONNECTED"""
        if(self.__valid_module(mod_id) and self.__valid_channel(channel)):
                cmd = f"C{mod_id}{channel:02d}"
                self.interface.write_cmd(cmd)
                self.__state_mgr.set_channel_state(mod_id, channel, FIUState.CONNECTED)

    def connect_channels_all(self) -> None:
            """Dedicated method to set all channels on every FIU on serial bus to CONNECTED state"""
            for box in self.module_IDs:
                cmd = f"C{box}99"
                self.interface.write_cmd(cmd)
            self.__state_mgr.set_all_state(self.module_IDs, FIUState.CONNECTED)

    def set_short_circuit_fault(self, mod_id, channel):
        """Sets a fault to ground at the specified channel. 
        (Only one channel in the system can be set to ground fault at a time.)"""
        if(self.__valid_module(mod_id) and self.__valid_channel(channel)):
            #Check to see if the fault state at given channel is a valid transition
            if(self.__check_transition(FIUState.FAULT_TO_GND, mod_id, channel)):
                #construct the SCPI command to write to the FIU
                cmd = f"F{mod_id}{channel:02d}"
                self.interface.write_cmd(cmd)
                #update the channel's state in the state manager
                self.__state_mgr.set_channel_state(mod_id, channel, FIUState.FAULT_TO_GND)
            else:
                raise FIUException(5010, channel, FIUState.FAULT_TO_GND.name)
        else:
            raise FIUException(5051)

    def set_voltage_measurement(self, mod_id, channel):
        """Sets the specified channel to voltage mode for DMM cell voltage measurement. 
        (Only one channel in the system can be set to measurement mode at a time.)"""
        if(self.__valid_module(mod_id) and self.__valid_channel(channel)):
            #Check to see if another channel is set to voltage measurement mode
            if(self.__check_transition(FIUState.VOLT_MEASUREMENT, mod_id, channel)):
                #construct the SCPI command to write to the FIU
                cmd = f"V{mod_id}{channel:02d}"
                self.interface.write_cmd(cmd)
                #update the channel's state in the state manager
                self.__state_mgr.set_channel_state(mod_id, channel, FIUState.VOLT_MEASUREMENT)
            else:
                raise FIUException(5010, channel, FIUState.VOLT_MEASUREMENT.name)
        else:
            raise FIUException(5051)

    def set_current_measurement(self, mod_id, channel):
        """Sets the specified channel to current mode for DMM bypass current measurement. 
        (Only one channel in the system can be set to measurement mode at a time.)"""
        if(self.__valid_module(mod_id) and self.__valid_channel(channel)):
            #Check to see if another channel is set to current measurement
            if(self.__check_transition(FIUState.CURR_MEASUREMENT, mod_id, channel)):
                #construct the SCPI command to write to the FIU
                cmd = f"I{mod_id}{channel:02d}"
                self.interface.write_cmd(cmd)
                #update the channel's state in the state manager
                self.__state_mgr.set_channel_state(mod_id, channel, FIUState.CURR_MEASUREMENT)
            else:
                raise FIUException(5010, channel, FIUState.CURR_MEASUREMENT.name)
        else:
            raise FIUException(5051)

    def relay_state(self, mod_id: int) -> list:
        """Returns the state for every channel in the FIU system."""
        if(self.__valid_module(mod_id)):
            system_status = [] 
            status = self.interface.write_cmd(f"S{mod_id}")
            for i in range(24):
                stat = status[i]
                if   stat == 'C': system_status.append(FIUState.CONNECTED.name)
                elif stat == 'D': system_status.append(FIUState.DISCONNECTED.name)
                elif stat == 'V': system_status.append(FIUState.VOLT_MEASUREMENT.name)
                elif stat == 'I': system_status.append(FIUState.CURR_MEASUREMENT.name)
                elif stat == 'F': system_status.append(FIUState.FAULT_TO_GND.name)
                else:             system_status.append(FIUState.RESET.name)
            return system_status
        else:
            raise FIUException(5075)

    # Deprecated from LabVIEW Driver
    # def relay_contact_cycle_count(self, mod_id: int, channel: int):
    #     """Returns the number of cycles the relays on the specified channel have experienced."""
    #     if(self.__valid_module(mod_id) and self.__valid_channel(channel)):
    #         cmd = f"N{mod_id}{channel:02d}"
    #         ret_data = self.interface.write_cmd(cmd)
    #         relay_counts = RelayCount(
    #             K1 = int(ret_data[0:7]),
    #             K2 = int(ret_data[8:15]),
    #             K3 = int(ret_data[16:23]),
    #             K4 = int(ret_data[24:31]),
    #             K5 = int(ret_data[32:])
    #         )
    #         return relay_counts
    #     else:
    #         raise FIUException(5075)

    def software_version(self, mod_id: int) -> str:
        """Returns the current version of the software running on the FIU."""
        #valid module check is disabled in labVIEW driver... so let's just send it
        return self.interface.write_cmd(f"H{mod_id}")
    
    def interlock_state(self, mod_id: int) -> bool:
        """Returns the state of the 24V interlock input on the FIU (Active or Inactive)."""
        if(self.__valid_module(mod_id)):
            int_state = self.interface.write_cmd(f"L{mod_id}")
            return False if int_state == '0' else '1'
        else:
            raise FIUException(5075)

    def interlock_override(self, mod_id: int, enable_disable: bool) -> None:
        """Sets the 24V interlock input on the FIU to active (enable) or inactive (disable)."""
        if(self.__valid_module(mod_id)):
            cmd = f"O{mod_id}{'1' if enable_disable else '0'}"
            self.interface.write_cmd(cmd)
        else:
            raise FIUException(5075)

    def __valid_module(self, mod_id: int) -> bool:
        """Ensures provided Module ID exists in the list of FIU Modules initialized on the system"""
        return True if mod_id in self.module_IDs else False 

    def __valid_channel(self, channel) -> bool:
        """Ensures entered channel number is within valid range of 1-24"""
        return True if (channel in range (1, 25)) else False

    def __check_transition(self, new_state, mod_id, channel) -> bool:
        """Asks the state manager to check if it is safe to transition to the new state, given the configuration of the FIU Bus"""
        if self._sharedDMM:
            return self.__state_mgr.check_shared_DMM_transition(new_state) 
        else: 
            return self.__state_mgr.check_transition(mod_id, channel, new_state)