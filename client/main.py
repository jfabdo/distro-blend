import socket
import tqdm
import os

f = open('client/.client.config')

variables = {}
variables['SEPARATOR'] = '<SEPARATOR>'
variables['BUFFER_SIZE'] = '4096'
variables['host'] = '192.168.1.101'
variables['port'] = '19999'
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