import sys
sys.path.append("src")
from FIU import FIU, RS485

def print_states(rel_states: list) -> None:
    for i in range(0, 12):
        print(f"Channel {i+1}:\t{rel_states[i]}\tChannel {i+13}:\t{rel_states[i+12]}")

if __name__ == "__main__":
    resource = sys.argv[1]
    mod = 0
    test_inf = RS485(resource)
    end = True
    with FIU([mod], test_inf) as fiu:
        print_states(fiu.relay_state(mod))
        while end:
            o = int(input(f"""
            Enter an action status:
            1 : Set Open Circuit Fault
            2 : Set Open Circuit Fault (All Channels)
            3 : Set Short Circuit Fault
            4 : Set Voltage Measurement
            5 : Set Current Measurement
            6 : Get Relay States (no action)
            7 : Software Version
            8 : Get Interlock State
            9 : Interlock Override
            Enter 0 or other number to close the connection with FIU: Mod IDs {fiu.module_IDs} on port {fiu.resource}
            Action: """))
            
            if o == 1:
                channel = -1
                state = -1
                while((channel < 1 or channel > 25) and (state < 1 or state > 2)):
                    channel = int(input("Set Channel (1-25): "))
                    state   = int(input("Enter 1 to Disconnect, 2 to Connect: "))
                fiu.set_open_circuit_fault(mod, channel, True if(state == 1) else False)
            elif o == 2:
                state = -1
                while((state < 1 or state > 2)):
                    state = int(input("Enter 1 to Disconnect All, 2 to Connect All: "))
                fiu.set_open_circuit_fault_all(True if(state == 1) else False)
            elif o ==3:
                channel = -1
                while((channel < 1 or channel > 25)):
                    channel = int(input("Set Short Circuit Fault on Channel (1-25): "))
                fiu.set_short_circuit_fault(mod, channel)
            elif o ==4:
                channel = -1
                while((channel < 1 or channel > 25)):
                    channel = int(input("Set Voltage Measurement on Channel (1-25): "))
                fiu.set_voltage_measurement(mod, channel)
            elif o ==5:
                channel = -1
                while((channel < 1 or channel > 25)):
                    channel = int(input("Set Current Measurement on Channel (1-25): "))
                fiu.set_current_measurement(mod, channel)
            elif o ==6:
                pass
            elif o ==7:
                print(f"FIU: {mod} on {resource} is running software version: {fiu.software_version(mod)}")
            elif o ==8:
                print("Interlock Active" if fiu.interlock_state(mod) else "Interlock Inactive")
            elif o ==9:
                state = -1
                while((state < 1 or state > 2)):
                    state = int(input("Enter 1 to set active, 2 to set inactive: "))
                fiu.interlock_override(mod, True if state==1 else False)
            else:
                end = False
            print_states(fiu.relay_state(mod))

            