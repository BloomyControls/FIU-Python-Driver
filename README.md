# Bloomy Fault Insertion Unit Python Driver v1.0.0
This package enables RS485 communication to the Bloomy Fault Insertion Unit through a PC's serial ports. 

The Fault Insertion Unit (FIU) is designed to be used in conjunction with the BS1200 to generate open faults and short to ground faults. It also has switching that allows precisions current and voltage measurements to be taken using an external DMM. 
The FIU supports 24 BS1200 channels. Each of the 24 channels allow switching to a shared DMM bus for current readings, voltage readings, and fault to ground. Extreme care must be taken to avoid shorting channels on this bus. For systems with multiple FIUs, this bus may also be shared between them.
The Fault Insertion Unit (FIU) is configurable to communicate using RS-485 or CAN bus. 
In order to use the RS-485 protocol, the box must be set to 0-7. For use with CAN bus, the box must be set to 8-15. 
The FIU Python Driver currently supports RS-485 only. CAN interface support development is pending.

## Build and Installation
### Requirements
Requires Python version 3.7 or greater
Package is compatible with Windows and Unix platforms. 
Tested on Windows 10 build 19043 64-bit, using Python 3.10.5
Tested on Ubuntu 18.04 WSL 1, using Python 3.7.4, 3.7.14

### Installation
To begin installation the fiu driver package, open a command line terminal in the directory that the v1.0.0 wheel distribution release was saved. 
To install the package run the command: 

Windows:    ```pip install bloomy_fiu_driver-1.0.0-py3-none-any.whl```

Linux:      ```pip3 install bloomy_fiu_driver-1.0.0-py3-none-any.whl```

If providing a full path to the .whl file, the terminal may be opened in any directory.

### Building the Project
Alternative to installing from the official release, the driver package may be built from the source code using native python build tools.
Open the terminal in the top level folder of the repository, where pyproject.toml is located. 
Create a .whl binary distribution, and source tarball in the project's /dist/ directory with the command:

Windows:
```python -m build```

Linux:
```python3 -m build```
## Use Instructions
With the fiu driver package installed to the python environment, use one of the following import statements the access the driver:

import fiu
from fiu import FIU, RS485
from fiu import *

Create an FIU object by providing a list of FIU Box IDs (0-7) and the serial comm resource connecting the host to the FIU communication bus as arguments.
Establish an RS-485 connection on the provided com resource  by calling the FIU.connect() method.

This driver is designed to work using the with statement such that the connect and disconnect methods are called with the class's \_\_enter\_\_() and \_\_exit\_\_() 
respectively. 
For example, the following will establish a connection with a single Fault Insertion Unit with the Box ID 0d0 on the windows serial resource COM0, set all channels to a disconnected open circuit fault state, print all channel relay states as a list of strings, and close the connection as the with statement is exited.

```
from fiu import FIU

with FIU([0], "COM0") as f:
    f.set_open_circuit_fault_all([0], True)
    print(f.relay_state())
```
Upon calling the disconnect() method, all FIU channels will be set to a connected state before closing the serial communication session and freeing up comm resources. 

### Safe State Management
The FIU driver uses an internal State Manager to prevent setting a channel state that puts the unit under unsafe conditions. 
If an invalid channel state is set, such as attempting to set two channels on the same FIU to the fault to ground state, the 
driver will return a custom exception describing the error. 

### Shared DMM
When using multiple FIU modules with a single DMM, it is important to set “Shared DMM” to True in the configuration method. If there is only one FIU module or a separate DMM for each FIU, “Shared DMM” should remain False.
The modules themselves do not know of the states of other modules. Without the added driver protection, a user may unintentionally short multiple FIUs together. Bloomy’s LabVIEW drivers contain a state manager that keeps track of the states of all channels in every FIU module in the system. When set to “Shared DMM”, the drivers will ensure that, not only does each module have no more than one channel set to DMM measurement at a time, but also that the entire system has only one channel at a time.
### Measurement and Fault States
It is important to note that the FIU cannot be set to a fault and a measurement mode simultaneously. When a new state command is sent to the FIU, the previous state is cleared. For example, if channel 1 is set to open circuit fault and then a voltage measurement command is sent to the FIU for channel 1, the channel will clear the fault and then be set to voltage measurement. The channel will not return to the fault state after the measurement is complete, unless explicitly told to.

## Feature List
The FIU driver class provides the following public methods to interact with the Bloomy Fault Insertion Unit
| Driver Method Name         | Parameters                                                                                                                                                                        | Description                                                                                                                                                                                                                                                           |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| FIU                        | mod_ids (list[int]): of configured FIU Module ID(s)<br>comm_resource (str): Serial comm port resource name                                                                        | Constructor method for FIU driver object used to establish <br>session with the provided module IDs. <br>Valid IDs for RS-485 communication are 0x0-0x7<br>Serial resource names are enumerated with the format "COM#" on Windows,<br>and "ttyS#" on UNIX platforms.  |
| connect                    | N/A                                                                                                                                                                               | Instructs the driver's serial RS-485 interface to establish a connection<br>with the com resource                                                                                                                                                                     |
| disconnect                 | N/A                                                                                                                                                                               | Sets all channels on all FIU modules to CONNECTED state before instructing <br>the RS-485 serial interface to close the connection with the FIU                                                                                                                       |
| configure                  | shared_dmm (bool): value setting Shared DMM status                                                                                                                                | Set whether the system is using a shared DMM across multiple FIUs.                                                                                                                                                                                                    |
| set_open_circuit_fault     | mod_id (int): FIU module ID<br>channel (int): Channel to set open circuit state for (1-24)<br>enable_disable (bool): True to enable (DISCONNECTED) or False to disable (CONNECT)  | Enable (disconnect) or disable (connect) an open circuit fault at a specified channel.                                                                                                                                                                                |
| set_open_circuit_fault_all | mod_id (int): FIU module ID<br>enable_disable (bool): True to enable (DISCONNECTED) or False to disable (CONNECT)                                                                 | Enable (disconnect) or disable (connect) open circuit faults at all channels in the system.                                                                                                                                                                           |
| set_short_circuit_fault    | mod_id (int): FIU module ID<br>channel (int): Channel to set short circuit fault on (1-24)                                                                                        | Sets a fault to ground at the specified channel. (Only one channel in the system can be set to ground fault at a time.)                                                                                                                                               |
| set_voltage_measurement    | mod_id (int): FIU Module ID<br>channel (int): Channel to set DMM voltage measurement on (1-24)                                                                                    | Sets the specified channel to voltage mode for DMM cell voltage measurement. (Only one channel in the system can be set to measurement mode at a time.)                                                                                                               |
| set_current_measurement    | mod_id (int): FIU Module ID<br>channel (int): Channel to set DMM current measurement on (1-24)                                                                                    | Sets the specified channel to current mode for DMM bypass current measurement. (Only one channel in the system can be set to measurement mode at a time.)                                                                                                             |
| relay_state                | mod_id (int): FIU Module ID                                                                                                                                                       | Returns the state for every channel in the FIU system.                                                                                                                                                                                                                |
| software_version           | mod_id (int): FIU Module ID                                                                                                                                                       | Returns the current version of the software running on the FIU.                                                                                                                                                                                                       |
| interlock_state            | mod_id (int): FIU module ID                                                                                                                                                       | Returns the state of the 24V interlock input on the FIU (Active or Inactive).                                                                                                                                                                                         |
| interlock_override         | mod_id (int): FIU module ID<br>enable_disable (bool): True for interlock Active (enable) False for interlock Inactive (disable)                                                   | Sets the 24V interlock input on the FIU to active (enable) or inactive (disable).                                                                                                                                                                                     |