from vtk import *
from time import sleep
from threading import Thread, Lock
from struct import pack, unpack
import socket
import os, sys

box = [-1, -1, -1, 1, 1, 1]

lock = Lock()
lock.acquire()

args = sys.argv[1:]
while len(args) > 0:
  if args[0] == '-box':
    box = [float(i) for i in args[1:7]]
    args = args[7:]
  else:
    print("syntax")
    sys.exit(0)

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

cube = vtkCubeSource()
cube.SetBounds(box[0], box[1], box[2], box[3], box[4], box[5])
outline = vtkOutlineFilter()
outline.SetInputConnection(cube.GetOutputPort())
mapper = vtkPolyDataMapper()
mapper.SetInputConnection(outline.GetOutputPort())
actor = vtkActor()
actor.SetMapper(mapper)
ren.AddActor(actor)


def SktInterface():

    s = socket.socket()
    port = 1900
    s.bind(('', port))
    s.listen(5)

    print('ready on port', 1900)

    ready_map = {}

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

      if label == 'update':

        c.send('ok'.encode())
        c.close()

        lock.acquire()

        for label in ready_map:
          data = ready_map[label]

          if label in data_library:
            mapper = data_library[label]
          else:
            mapper = vtkDataSetMapper()
            actor = vtkActor()
            actor.SetMapper(mapper)
            ren.AddActor(actor)
            data_library[label] = mapper

          mapper.SetInputData(data)
          mapper.Modified()

        lock.release()

        ready_map = {}

      else:

        buf = b''
        while len(buf) < 4:
          buf = buf + c.recv(4 - len(buf))

        l = unpack('!i', buf)[0]

        buf = b''
        while len(buf) < l:
          buf = buf + c.recv(l - len(buf))

        c.send('ok'.encode())
        c.close()

        data = buf.decode()

        if label in data_library:
          print('updating', label)
        else:
          print('adding', label)

        rdr = vtkUnstructuredGridReader()
        rdr.SetInputString(data)
        rdr.ReadFromInputStringOn()
        rdr.Update()
        ready_map[label] = rdr.GetOutput()

t = Thread(target=SktInterface, args=())
t.start()

renWin.Render()
iren.Start()
lock.release()

