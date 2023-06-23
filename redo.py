import argparse
import socket
import subprocess
import os
import threading
import time
import tqdm

parser = argparse.ArgumentParser(description="Use -c for client or -s for server")
parser.add_argument('-c','--client', action="store_true", help="client mode")
parser.add_argument('-s','--server', action="store_true", help="server mode")
args = parser.parse_args()
config = vars(args)
SEPARATOR = "<SEPARATOR>"
BUFFER_SIZE = 4096 # send 4096 bytes each time step
SERVER_PORT = 19999

class render(threading.Thread):

    def render(self, filename):
        self.rendering = True
        fileroot = "".join(filename.split('.')[:-1])
        os.mkdir(fileroot)
        subprocess.run([variables['blender_path']+'blender', '-b', filename, '-o','//./' + fileroot + "/",'-E','CYCLES','-F','PNG','-a','--','--cycles-device','CUDA'])#'-f','1'])

    def run(self):
        pass

class commonality:
    def sendfile(self,s,filename):
        # get the file size
        filesize = os.path.getsize(filename)
        # send the filename and filesize
        s.send(f"{filename}{SEPARATOR}{filesize}".encode())
        # start sending the file
        progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "rb") as f:
            while True:
                # read the bytes from the file
                bytes_read = f.read(BUFFER_SIZE)
                if not bytes_read:
                    # file transmitting is done
                    break
                # we use sendall to assure transimission in 
                # busy networks
                s.sendall(bytes_read)
                # update the progress bar
                progress.update(len(bytes_read))
        # close the socket
        s.close()

    def receivefile(self,s):
        
        # enabling our server to accept connections
        # 5 here is the number of unaccepted connections that
        # the system will allow before refusing new connections
        s.listen(5)
        # print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
        # accept connection if there is any
        client_socket, address = s.accept() 
        # if below code is executed, that means the sender is connected
        print(f"[+] {address} is connected.")
        # receive the file infos
        # receive using client socket, not server socket
        received = client_socket.recv(BUFFER_SIZE).decode()
        filename, filesize = received.split(SEPARATOR)
        # remove absolute path if there is
        filename = os.path.basename(filename)
        # convert to integer
        filesize = int(filesize)
        # start receiving the file from the socket
        # and writing to the file stream
        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "wb") as f:
            while True:
                # read 1024 bytes from the socket (receive)
                bytes_read = client_socket.recv(BUFFER_SIZE)
                if not bytes_read:    
                    # nothing is received
                    # file transmitting is done
                    break
                # write to the file the bytes we just received
                f.write(bytes_read)
                # update the progress bar
                progress.update(len(bytes_read))

        # close the client socket
        client_socket.close()
        # close the server socket
        s.close()

class client(commonality):
    def clientmode(self):
        # the ip address or hostname of the server, the receiver
        host = "127.0.0.1"
        
        # the name of file we want to send, make sure it exists
        filename = "data.csv"
        # create the client socket
        s = socket.socket()
        print(f"[+] Connecting to {host}:{SERVER_PORT}")
        s.connect((host, SERVER_PORT))
        print("[+] Connected.") 
       
        self.sendfile(s,filename)

class server(commonality):
    def servermode(self):
        SERVER_HOST = "0.0.0.0"
        # create the server socket
        # TCP socket
        s = socket.socket()
        # bind the socket to our local address
        s.bind((SERVER_HOST, SERVER_PORT))
        self.receivefile(s)
        
if __name__ == "__main__":
    if config['client']:
        client().clientmode()
    elif config['server']:
        server().servermode()
    else:
        print("You didn't read the manual, did you? Use -c to run in client mode, and -s to run as a server")
