import socket
import tqdm
import os
import threading
import time
import subprocess
import argparse

parser = argparse.ArgumentParser(description="Use -c for client or -s for server")
parser.add_argument('-c','--client', action="store_true", help="client mode")
parser.add_argument('-s','--server', action="store_true", help="server mode")
args = parser.parse_args()
config = vars(args)
variables = {}
variables['SEPARATOR'] = '<SEPARATOR>'
variables['BUFFER_SIZE'] = '4096'
variables['port'] = '19999'

class render(threading.Thread):
    def __init__(self, s):
        threading.Thread.__init__(self)
        self.s = s
        self.rendering = False
    
    def is_rendering(self):
        return self.rendering
    
    def render(self, filename):
        self.rendering = True
        fileroot = "".join(filename.split('.')[:-1])
        os.mkdir(fileroot)
        subprocess.run([variables['blender_path']+'blender', '-b', filename, '-o','//./' + fileroot + "/",'-E','CYCLES','-F','PNG','-a','--','--cycles-device','CUDA+CPU'])#'-f','1'])
 
        # helper function to execute the threads
    def run(self):

        client_socket, address = self.s.accept()

        print(f"[+] {address} is connected")

        received = client_socket.recv(variables['BUFFER_SIZE']).decode()
        filename, filesize = received.split(variables['SEPARATOR'])
        variables['filename'] = filename = os.path.basename(filename)

        filesize = int(filesize)

        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "wb") as f:
            while True:
                bytes_read = client_socket.recv(variables['BUFFER_SIZE'])
                if not bytes_read:
                    break
                f.write(bytes_read)
                progress.update(len(bytes_read))
        client_socket.close()

        self.render(filename)

        if not variables['backup_file']:
            os.remove(filename)
        
def server():
    f = open('.server.config')

    variables['host'] = "0.0.0.0"
    for line in f.readlines():
        if ':' not in line:
            print('Error:')
            print(line)
            continue
        var, val = line.split(':')

        variables[''.join(var.split())] = ''.join(val.split())

    for variable in ['BUFFER_SIZE','port']:
        variables[variable] = int(variables[variable])
    receivefiles()

def client():
    f = open('.client.config')

    variables['host'] = '192.168.1.101'
    variables['filename'] = 'data.thing'
    for line in f.readlines():
        if ':' not in line:
            print('Error:')
            print(line)
            continue
        var, val = line.split(':')

        variables[''.join(var.split())] = ''.join(val.split())

    f.close()
    for variable in ['BUFFER_SIZE','port']:
        variables[variable] = int(variables[variable])
    sendfile()

def receivefiles():
    SERVER_HOST = variables['host']
    SERVER_PORT = int(variables['port'])

    s = socket.socket()
    s.bind((SERVER_HOST,SERVER_PORT))
    while True:
        s.listen(5)
        print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
        thread = render(s)
        thread.start()
        while not thread.is_rendering():
            time.sleep(.001)
    s.close()

def sendfile():
    SEPARATOR = variables['SEPARATOR']
    BUFFER_SIZE = variables['BUFFER_SIZE']
    host = variables['host']
    port = variables['port']
    filename = variables['filename']

    filesize = os.path.getsize(filename)
    s = socket.socket()
    print(f"[+] Connecting to {host}:{port}")
    s.connect((host,port))
    print("[+] Connected.")

    s.send(f'{filename}{SEPARATOR}{filesize}'.encode())

    progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True,unit_divisor=1024)
    with open(filename,"rb") as f:
        while True:
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                break
            s.sendall(bytes_read)
            progress.update(len(bytes_read))

    s.close()

if __name__ == "__main__":
    if config['client']:
        client()
    elif config['server']:
        server()
    else:
        print("You didn't read the manual, did you, doofus? Use -c to run in client mode, and -s to run as a server")
