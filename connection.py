import serial
import serial.tools.list_ports
import time

def find_arduino_port():
    """Try to automatically find Arduino by checking all available ports"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        try:
            # Common Arduino vendor IDs
            if '2341' in port.hwid or '2A03' in port.hwid or '1A86' in port.hwid:
                return port.device
        except:
            continue
    return None

def test_arduino_connection(port_name, baud_rate=9600):
    """Test connection to Arduino and verify communication"""
    try:
        print(f"\nAttempting to connect to {port_name} at {baud_rate} baud...")
        
        # Open serial connection
        arduino = serial.Serial(port=port_name, baudrate=baud_rate, 
                              timeout=2, write_timeout=2)
        time.sleep(2)  # Wait for Arduino to reset
        
        print("Connection established. Testing communication...")
        
        # Send test message
        arduino.write(b'TEST\n')  # Send test command
        print("Sent test command to Arduino")
        
        # Wait for response
        start_time = time.time()
        while (time.time() - start_time) < 5:  # 5 second timeout
            if arduino.in_waiting:
                response = arduino.readline().decode().strip()
                if response:
                    print(f"Arduino response: {response}")
                    if response == "ACK":  # Common Arduino acknowledgment
                        print("Communication successful!")
                        arduino.close()
                        return True
                    break
            time.sleep(0.1)
        
        print("No valid response received")
        arduino.close()
        return False
        
    except serial.SerialException as e:
        print(f"Connection failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Try to automatically detect Arduino
    auto_port = find_arduino_port()
    port_to_test = auto_port if auto_port else 'COM4'  # Fallback to COM4
    
    print(f"Testing Arduino connection on port: {port_to_test}")
    
    if test_arduino_connection(port_to_test):
        print("\n✅ Arduino connection test PASSED")
    else:
        print("\n❌ Arduino connection test FAILED")
    
    print("\nAvailable ports:")
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"- {port.device}: {port.description} [HWID: {port.hwid if port.hwid else 'N/A'}]")