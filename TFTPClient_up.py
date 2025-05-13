import socket
import struct
import os

class TFTPClient:
    def __init__(self, server_ip, server_port=6969, block_size=512):
        """
        Initialize TFTP client
        :param server_ip: IP address of TFTP server
        :param server_port: Port of TFTP server (default 69)
        :param block_size: Size of data blocks to send (default 512 bytes)
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.block_size = block_size
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(5)  # 5 second timeout

    def _create_wrq_packet(self, filename, mode='octet'):
        """
        Create Write Request (WRQ) packet
        :param filename: Name of file to upload
        :param mode: Transfer mode (default 'octet')
        :return: WRQ packet
        """
        opcode = 2  # WRQ opcode
        packet = struct.pack('!H', opcode)
        packet += filename.encode('ascii') + b'\x00'
        packet += mode.encode('ascii') + b'\x00'
        return packet

    def _create_data_packet(self, block_number, data):
        """
        Create Data packet
        :param block_number: Block number
        :param data: Data to send
        :return: Data packet
        """
        opcode = 3  # Data opcode
        packet = struct.pack('!HH', opcode, block_number)
        packet += data
        return packet

    def upload_file(self, filename, local_path):
        """
        Upload file to TFTP server
        :param filename: Remote filename
        :param local_path: Local file path to upload
        """
        # Open the file to upload
        with open(local_path, 'rb') as file:
            # Send Write Request (WRQ)
            wrq_packet = self._create_wrq_packet(filename)
            
            # Use initial server port for WRQ
            self.sock.sendto(wrq_packet, (self.server_ip, self.server_port))

            # Wait for initial ACK (block 0)
            try:
                ack_data, server_address = self.sock.recvfrom(1024)
            except socket.timeout:
                print("Timeout waiting for initial ACK")
                return False

            # Verify initial ACK packet
            if len(ack_data) < 4:
                print("Invalid initial ACK packet")
                return False

            # Unpack the ACK packet
            ack_opcode, ack_block = struct.unpack('!HH', ack_data[:4])
            
            # Verify ACK opcode and block number
            if ack_opcode != 4 or ack_block != 0:
                print("Unexpected initial ACK")
                return False

            # Start sending data blocks
            block_number = 1
            while True:
                # Read a block of data
                data = file.read(self.block_size)
                
                # If no more data, send last block (possibly empty)
                is_last_block = len(data) < self.block_size

                # Create and send data packet
                # Use the server_address from the ACK packet, which includes the new port
                data_packet = self._create_data_packet(block_number, data)
                self.sock.sendto(data_packet, server_address)

                # Wait for ACK
                try:
                    ack_data, _ = self.sock.recvfrom(1024)
                    print(f"Received ACK: {ack_data}")
                except socket.timeout:
                    print(f"Timeout waiting for ACK of block {block_number}")
                    return False

                # Verify ACK packet
                if len(ack_data) < 4:
                    print("Invalid ACK packet")
                    return False

                ack_opcode, ack_block = struct.unpack('!HH', ack_data[:4])
                
                # Check ACK
                if ack_opcode != 4 or ack_block != block_number:
                    print(f"Unexpected ACK for block {block_number}")
                    return False

                # Increment block number
                block_number += 1

                # Exit if last block was sent and acknowledged
                if is_last_block:
                    break

            print(f"Successfully uploaded {filename}")
            return True

def main():
    # Example usage
    try:
        # Create TFTP client
        tftp_client = TFTPClient('127.0.0.1')  # Use loopback for local testing
        
        # Upload a file
        success = tftp_client.upload_file('bigfile.txt', 'bigfile.txt')
        
        if not success:
            print("File upload failed")
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
