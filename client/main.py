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
    variables[var] = val
    print(var + " = " + val)

