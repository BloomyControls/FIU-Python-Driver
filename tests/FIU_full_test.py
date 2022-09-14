import sys
from fiu import FIU

def print_states(rel_states: list) -> None:
    
    for i in range(0, 12):
        space = "" if("MEASUREMENT" in rel_states[i]) else "\t"
        print(f"Channel {i+1}:\t{rel_states[i]}\t{space}Channel {i+13}:\t{rel_states[i+12]}")

if __name__ == "__main__":
    resource = sys.argv[1]
    mod = 0
    end = True
    with FIU([mod], resource) as fiu:
        print_states(fiu.relay_state(mod))
        while end:
            o = int(input(f"""
            Enter an action status:
            1  : Set Open Circuit Fault
            2  : Set Open Circuit Fault (All Channels)
            3  : Connect Channel
            4  : Connect All Channels
            5  : Set Short Circuit Fault
            6  : Set Voltage Measurement
            7  : Set Current Measurement
            8  : Get Relay States (no action)
            9  : Software Version
            10 : Get Interlock State
            11 : Interlock Override
            12 : Configure Shared DMM
            Enter any other character(s) to close the connection with FIU: Mod IDs {fiu.module_IDs} on port {fiu.resource}
            Action: """))
            
            if o == 1:
                channel = -1
                while((channel < 1 or channel > 25)):
                    channel = int(input("Set Channel to DISCONNECT (1-25): "))
                fiu.set_open_circuit_fault(mod, channel, True)
            elif o == 2:
                fiu.set_open_circuit_fault_all(True)
            elif o == 3:
                channel = -1
                while((channel < 1 or channel > 25)):
                    channel = int(input("Set Channel to CONNECT (1-25): "))
                fiu.set_channel_connected(mod, channel)
            elif o == 4:
                fiu.connect_channels_all()
            elif o == 5:
                channel = -1
                while((channel < 1 or channel > 25)):
                    channel = int(input("Set Short Circuit Fault on Channel (1-25): "))
                fiu.set_short_circuit_fault(mod, channel)
            elif o == 6:
                channel = -1
                while((channel < 1 or channel > 25)):
                    channel = int(input("Set Voltage Measurement on Channel (1-25): "))
                fiu.set_voltage_measurement(mod, channel)
            elif o == 7:
                channel = -1
                while((channel < 1 or channel > 25)):
                    channel = int(input("Set Current Measurement on Channel (1-25): "))
                fiu.set_current_measurement(mod, channel)
            elif o == 8:
                pass
            elif o == 9:
                print(f"FIU: {mod} on {resource} is running software version: {fiu.software_version(mod)}")
            elif o == 10:
                print("Interlock Active" if fiu.interlock_state(mod) else "Interlock Inactive")
            elif o == 11:
                state = -1
                while((state < 1 or state > 2)):
                    state = int(input("Enter 1 to set active, 2 to set inactive: "))
                fiu.interlock_override(mod, True if state==1 else False)
            # elif o == 12: 
            #     state = -1
            #     while((state < 0 or state > 1)):
            #         state = int(input("Enter 0 to set Shared DMM status inactive, 1 to set active: "))
            #         fiu.configure(state == 1)            
            else:
                end = False
            if(end):
                print_states(fiu.relay_state(mod))

            