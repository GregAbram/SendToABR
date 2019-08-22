import socket
from struct import pack, unpack

def update_unity(caller, *args):
  try:
    s = socket.socket()
    s.connect(('localhost', 1900))
  except:
    print 'unable to connect to server'
  else:
    print 'connected'
    update = 'update'.encode()
    s.send(pack('!i', len(update)))
    s.send(update)
    ack = s.recv(2).decode()
    print('got ack: ', ack)
    s.close()

uu = event_num = GetActiveView().AddObserver('EndEvent', update_unity, 1.0)


