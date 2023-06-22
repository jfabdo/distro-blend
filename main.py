import socket
import tqdm
import os
import threading
import time
import subprocess

f = open('.server.config')

variables = {}
variables['SEPARATOR'] = '<SEPARATOR>'
variables['BUFFER_SIZE'] = '4096'
variables['host'] = "0.0.0.0"
variables['port'] = '19999'
for line in f.readlines():
    if ':' not in line:
        print('Error:')
        print(line)
        continue
    var, val = line.split(':')

    variables[''.join(var.split())] = ''.join(val.split())

SERVER_HOST = variables['host']
SERVER_PORT = int(variables['port'])

BUFFER_SIZE = int(variables['BUFFER_SIZE'])
SEPARATOR = variables['SEPARATOR']
BACKUP = bool(variables['backup_file'])
blender_path = variables['blender_path']

class render(threading.Thread):
    def __init__(self, s):
        threading.Thread.__init__(self)
        self.s = s
        self.rendering = False
    
    def is_rendering(self):
        return self.rendering
    
    def render(self, filename):
        self.rendering = True
        subprocess.run(blender_path, "-b", filename)
 
        # helper function to execute the threads
    def run(self):

        client_socket, address = self.s.accept()

        print(f"[+] {address} is connected")

        received = client_socket.recv(BUFFER_SIZE).decode()
        filename, filesize = received.split(SEPARATOR)
        filename = os.path.basename(filename)
        filesize = int(filesize)

        progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "wb") as f:
            while True:
                bytes_read = client_socket.recv(BUFFER_SIZE)
                if not bytes_read:
                    break
                f.write(bytes_read)
                progress.update(len(bytes_read))
        client_socket.close()

        self.render(filename)

        if not BACKUP:
            os.remove(filename)
        
def firststep():
    s = socket.socket()
    s.bind((SERVER_HOST,SERVER_PORT))
    while True:
        s.listen(5)
        print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
        thread = render(s)
        thread.start()
        # while not thread.is_rendering():
        #     time.sleep(.001)
    s.close()

def main():
    firststep()

if __name__ == "__main__":
    main()

    