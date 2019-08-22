from vtk import *
from time import sleep
from threading import Thread, Lock
from struct import pack, unpack
import socket
import os, sys

data_library = {}

class vtkTimerCallback():
   def __init__(self, r, w):
       self.ren = r
       self.rwin = w

   def execute(self,obj,event):
       lock.release()
       sleep(0.1)
       lock.acquire()
       self.ren.ResetCamera()
       self.rwin.Render()

ren = vtkRenderer()
renWin = vtkRenderWindow()
renWin.AddRenderer(ren)
renWin.SetSize(512, 512)

iren = vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)
iren.Initialize()
         
cb = vtkTimerCallback(ren, iren)
iren.AddObserver('TimerEvent', cb.execute)
iren.CreateRepeatingTimer(1000);

lock = Lock()

def SktInterface():

    s = socket.socket()
    port = 1900
    s.bind(('', port))
    s.listen(5)

    print('ready on port', 1900)

    while True:
      c, addr = s.accept()
      print('connection accepted')

      buf = b''
      while len(buf) < 4:
        buf = buf + c.recv(4 - len(buf))

      l = unpack('!i', buf)[0]

      buf = b''
      while len(buf) < l:
        buf = buf + c.recv(l - len(buf))

      label = buf.decode()

      buf = b''
      while len(buf) < 4:
        buf = buf + c.recv(4 - len(buf))

      l = unpack('!i', buf)[0]

      buf = b''
      while len(buf) < l:
        buf = buf + c.recv(l - len(buf))

      c.send('ok'.encode())
      data = buf.decode()
      c.close()

      if label in data_library:
        print('updating', label)
      else:
        print('adding', label)

      lock.acquire()

      if label in data_library:
        rdr = data_library[label]
        rdr.SetInputString(data)
        rdr.Modified()
      else:
        rdr = vtkUnstructuredGridReader()
        rdr.SetInputString(data)
        rdr.ReadFromInputStringOn()
        mapper = vtkDataSetMapper()
        mapper.SetInputConnection(rdr.GetOutputPort())
        actor = vtkActor()
        actor.SetMapper(mapper)
        ren.AddActor(actor)
        data_library[label] = rdr

      lock.release()


t = Thread(target=SktInterface, args=())
t.start()

lock.acquire()
renWin.Render()
iren.Start()
lock.release()
