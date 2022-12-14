import sys
sys.path.append("src")
from fiu import FIU, RS485

if __name__ == "__main__":
    resource = sys.argv[1]
    mod = sys.argv[2]
    with FIU([0], resource) as fiu:
        print(f"FIU Module ID {fiu.resource} is running Software Version: {fiu.software_version(0)}")
        print(f"FIU Module ID {fiu.resource} Relay States:\n{fiu.relay_state(0)}")
        print(f"FIU Module ID {fiu.resource}: Setting Channel 1 to DISCONNECTED")
        fiu.set_open_circuit_fault(0, 1, True)
        print(f"FIU Module ID {fiu.resource} Relay States:\n{fiu.relay_state(0)}")

