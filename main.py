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
variables['client_host'] = '192.168.1.101'
variables['filename'] = 'data.thing'
variables['server_host'] = '0.0.0.0'

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
        variables["fileroot"] = fileroot
        os.mkdir(fileroot)
        subprocess.run([variables['blender_path']+'blender', '-b', filename, '-o','//./' + fileroot + "/",'-E','CYCLES','-F','PNG','-a','--','--cycles-device','CUDA'])#'-f','1'])
 
        # helper function to execute the threads
    def run(self):

        client_socket, address = self.s.accept()

        print(f"[+] {address} is connected")

        self.receive(client_socket)
        filename = variables['filename']

        self.render(filename)
        fileroot = variables['fileroot']
        with os.scandir(fileroot) as entries:
            for entry in entries:
                if not entry.is_dir():
                    client.sendresult(f'{fileroot}/{filename}',client_socket)
                if not variables['backup_file']:
                    os.remove(f'{fileroot}/{entry}')

        client_socket.close()
        if not variables['backup_file']:
            os.remove(fileroot)
    
    def receive(self,client_socket):
        received = client_socket.recv(variables['BUFFER_SIZE']).decode()
        filename, filesize = received.split(variables['SEPARATOR'])
        filesize = int(filesize)

        variables['filename'] = filename = os.path.basename(filename)
        # variables['filesize'] = filesize

        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "wb") as f:
            while True:
                bytes_read = client_socket.recv(variables['BUFFER_SIZE'])
                if not bytes_read:
                    break
                f.write(bytes_read)
                progress.update(len(bytes_read))

class general:
    def readvars(configname):
        f = open(configname)
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

class server(general):
    def __init__(self):
        self.readvars('.server.config')
        
    def run(self):
        self.receivefiles()
    
    def receivefiles(self):
        SERVER_HOST = variables['server_host']
        SERVER_PORT = int(variables['port'])

        s = socket.socket()
        s.bind((SERVER_HOST,SERVER_PORT))
        variables['s'] = s
        while True:
            s.listen(5)
            print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
            thread = render(s)
            thread.start()
            while not thread.is_rendering():
                time.sleep(.001)
        s.close()

class client(general):
    def __init__(self):
        
        self.readvars('.client.config')
    
    def opensocket(self):
        return socket.socket()

    def send(self,filename,s):
        
        print("[+] Connected.")
        SEPARATOR = variables['SEPARATOR']
        filesize = os.path.getsize(filename)
        s.send(f'{filename}{SEPARATOR}{filesize}'.encode())

        progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True,unit_divisor=1024)
        with open(filename,"rb") as f:
            while True:
                bytes_read = f.read(variables['BUFFER_SIZE'])
                if not bytes_read:
                    break
                s.sendall(bytes_read)
                progress.update(len(bytes_read))
        

    def sendblend(self):
        s = self.opensocket()
        s.connect((variables['client_host'],variables['port']))
        print(f"[+] Connecting to {variables['client_host']}:{variables['port']}")
        self.send(variables['filename'],s)
        render().receive(s)
        # s.close()
        
    def sendresult(self,filename,s):
        self.send(filename,s)
        # s.close()

if __name__ == "__main__":
    if config['client']:
        client()
    elif config['server']:
        server()
    else:
        print("You didn't read the manual, did you? Use -c to run in client mode, and -s to run as a server")
