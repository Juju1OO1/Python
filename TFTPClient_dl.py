import os
import struct
import socket

#Main function
def main():
    
    # g_server_ip = input("Please key in the IP to download(If your server is local, key in 127.0.0.1)：")
    g_server_ip = "127.0.0.1"
    # g_downloadFileName = input("Please key in the file's name(ex: Test.txt)：")
    g_downloadFileName =  "bigfile.txt"
    print("Download From"+g_server_ip, "File"+g_downloadFileName)
    
    # Packing
    # struct.pack(fmt, v1, v2, ...): Encapsulate data into strings according to the given format(fmt) 
    # !: Indicates that we want to use network character order parsing because our data is received from the network. 
    #    When transmitting on the network, it is the network character order. 
    # H: The following H indicates the id of an unsigned short.
    # unsign short:16bits
    # s: char[]
    # b: signed char
    # There can be one number before each format, indicating the number
    sendDataFirst = struct.pack('!H%dsb5sb'%len(g_downloadFileName), 1, g_downloadFileName.encode('ascii'), 0, 'octet'.encode('ascii'), 0)
    
    # Create a UDP socket
    # AF_INET: Let two hosts transmit data through the network. AF_INET uses the IPv4 protocol.
    # SOCK_DGRAM: The datagram is provided one by one, and the corresponding protocol is UDP.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Send download file request data to specified service
    # 69: port number
    s.sendto(sendDataFirst, (g_server_ip, 6969)) #First send, connect to tftp server
    
    # Indicates that the data can be downloaded, if it is false then delete the file
    downloadFlag = True
    # Indicates the serial number of the received file
    fileNum = 0 
    
    # Open file in binary format
    f = open(g_downloadFileName, 'wb')
    
    while True:
        # Receive response data sent back by the server
        recvData, serverInfo = s.recvfrom(1024)
        #print(responseData)

        # Unpacking
        packetOpt = struct.unpack("!H", recvData[:2])  #Opcode
        packetNum = struct.unpack("!H", recvData[2:4]) #Block number
        
        #print(packetOpt, packetNum)
        
        # Received packet
        if packetOpt[0] == 3: #Opcode is a tuple(3,), and 3 means DATA
            # Calculate the serial number of this file, which is the last received +1
            fileNum += 1
            
            # Whether the packet number is equal to the previous time
            if fileNum == packetNum[0]:
                f.write(recvData[4:]) #Write into file

            # Organize ACK packets
            ackData = struct.pack("!HH", 4, packetNum[0])
            s.sendto(ackData, serverInfo)
            
        # Error response
        elif packetOpt[0] == 5: # 5 means error happen
            print("Sorry, there is no this file!")
            downloadFlag = False # Delete the file
            break

        else:
            print(packetOpt[0])
            break
            
        # The reception is completed and the program is exited
        if len(recvData) < 516:
            downloadFlag = True
            print("%s File download completed!"%g_downloadFileName)
            break
            
    if downloadFlag == True:
        f.close()
    else:
        #If there is no downloaded file, delete the file you just created.
        f.close()
        os.remove(g_downloadFileName) 

        # Call the main function
if __name__ == '__main__':
    main()