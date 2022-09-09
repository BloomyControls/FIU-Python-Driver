# Bloomy Fault Insertion Unit Python Driver
This package enables RS485 communication to the Bloomy Fault Insertion Unit through a PC's serial ports. 

The Fault Insertion Unit (FIU) is designed to be used in conjunction with the BS1200 to generate open faults and short to ground faults. It also has switching that allows precisions current and voltage measurements to be taken using an external DMM. 
The FIU supports 24 BS1200 channels. Each of the 24 channels allow switching to a shared DMM bus for current readings, voltage readings, and fault to ground. Extreme care must be taken to avoid shorting channels on this bus. For systems with multiple FIUs, this bus may also be shared between them.
The Fault Insertion Unit (FIU) is configurable to communicate using RS-485 or CAN bus. In order to use the RS-485 protocol, the box must be set to 0-7. For use with CAN bus, the box must be set to 8-15. 
The FIU Python Driver currently supports RS-485 only. CAN interface support development is pending.

# Installation
To install, open a command line in the dist directory and use the command 'pip install FIU_driver-1.0.0-py3-none-any.whl'
Package is compatible with Windows and Unix platforms
Requires Python version 3.7 or greater

## use instructions
With the fiu driver package installed to the python environment, import the driver package in the script file:

import fiu

## feature list
#TODO COPY THE FIU DRIVER TEXT