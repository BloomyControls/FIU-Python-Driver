from time import sleep
from serial import Serial
from .fiu_types import *

class CommInterface(object):
    """Abstract communication interface class for future comm protocol implementations"""
    def __init__(self, resource: str):
        self.resource = resource

    def open(self):
        pass

    def close(self):
        pass
    
class RS485(CommInterface):
    def __init__(self, port: str, port_settings: DefaultPortSettings = DefaultPortSettings()) -> None:
        self.resource = port
        self._port_cfg = port_settings

    def open(self) -> None:
        """Opens an RS-485 connection to the FIU."""
        #Set port settings for the interface class from custom dataclass with port settings 
        #according to FIU communication specification
        self.serial = Serial()
        self.serial.baudrate = self._port_cfg.baud_rate
        self.serial.bytesize = self._port_cfg.byte_size
        self.serial.parity   = self._port_cfg.parity
        self.serial.stopbits = self._port_cfg.stop_bits
        #Configure rs485 mode with default settings
        #self.serial.rs485_mode = rs485.RS485Settings
        #open the port connection to begin communication session
        self.serial.setPort(self.resource)
        self.serial.open()

    def close(self) -> None:
        """Closes a connection to the FIU."""
        #connect all channels before closing
        self.serial.close()
    
    
    def __add_CRC(self, msg: str) -> str:
        """Add checksum code and newline termination character to the message"""
        #CRC is calculated from the sum of the message's u8 byte array modulo
        encoded_msg_sum = sum(bytes(msg, 'utf-8'))
        #Take only the hex value characters from the hex string  
        CRC = hex(encoded_msg_sum % 256)[2:].upper()
        #add end line constant for the termination character(s)
        return msg + CRC + '\r'

    def write_cmd(self, msg: str) -> str:
        """Write a message out to the serial device and return the parsed return data"""
        #clear the input and output buffers on the port
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        #add checksum and termination to the message, then write command out to device 
        msg = self.__add_CRC(msg)
        self.serial.write(msg.encode('utf-8'))
        #wait 100 ms for response
        sleep(0.1)
        ret_msg = self.serial.read(self.serial.in_waiting).decode('utf-8')
        return self.__check_return_msg(msg, ret_msg)

    def __check_return_msg(self, sent_cmd: str, readbuff: str) -> str:
        """Parses the returned message buffer based on the return code"""
        return_msg = readbuff[0]
        if return_msg == '0':
            #Success - No Data
            return ""
        elif return_msg == '1':
            #Success - Data
            #Remove Return Code (1), CRC(2), and CR (1) characters
            return readbuff[1:1+(len(readbuff)-4)]
        elif return_msg == '2':
            #Error msg
            return FIUException(5003, [readbuff, sent_cmd])
        elif return_msg == '3':
            #Error Data
            #Error returned when attempting to short multiple channels to the bus
            #Remove Return Code (1), CRC(2), and CR (1) characters
            return FIUException(5004, readbuff[1:1+(len(readbuff)-4)])
        else:
            #Invalid Response to CMD
            return FIUException(5002, [sent_cmd, readbuff])