## pyMagStripe - a python Magnetic Card Reader/Writer Program.
## v 0.1
## Sean Colyer < sean @ colyer . name >
## Copyright 2010 Sean Colyer.
##This program is free software; you can redistribute it and/or
##modify it under the terms of the GNU General Public License
##as published by the Free Software Foundation; either version 2
##of the License, or (at your option) any later version.
##
##This program is distributed in the hope that it will be useful,
##but WITHOUT ANY WARRANTY; without even the implied warranty of
##MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##GNU General Public License for more details.
##
##You should have received a copy of the GNU General Public License
##along with this program; if not, write to the Free Software
##Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
##
## Outline:
## pyMagStripe.py -- provides the methods to interact with the serial magnetic card reader/writer
## pyMagStripGui.py  -- provides a wxPython front end

import os, wx, pyMagStripe
import wx.grid

class pyMagStripePanel(wx.Panel):
    def __init__ (self,parent):
        self.frame = parent
        self.port = 1
        self.file = "output.txt"
        self.pyMagStripe = pyMagStripe.pyMagStripe()
        wx.Panel.__init__(self,parent)

        self.frame.Bind(wx.EVT_CLOSE, self.onClose)

        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer (wx.HORIZONTAL)
        hbox2 = wx.BoxSizer (wx.HORIZONTAL)
        hbox3 = wx.BoxSizer (wx.HORIZONTAL)
        hbox4 = wx.BoxSizer (wx.HORIZONTAL)
        gridSizer = wx.GridSizer(2,3)

        self.fileButton = wx.Button(self, label="Select output file")
        hbox1.Add(self.fileButton,0)
        self.Bind(wx.EVT_BUTTON, self.onFileButton, self.fileButton)

        self.scan = wx.Button(self, label="Scan COM Ports")
        hbox1.Add(self.scan,0)
        self.Bind(wx.EVT_BUTTON, self.onScan, self.scan)

        self.serialOptions = wx.ComboBox(self,choices=['COM1','COM2','COM3','COM4','COM5','COM6','COM7','COM8','COM9'], style = wx.CB_DROPDOWN)
        hbox1.Add(self.serialOptions)
        self.Bind(wx.EVT_COMBOBOX, self.onSerialSelect, self.serialOptions)
                
        self.connect = wx.Button(self, label="Connect to Reader")
        hbox2.Add(self.connect,0)
        self.Bind(wx.EVT_BUTTON, self.onConnectClick, self.connect)

        self.readButton = wx.Button(self, label="Read")
        hbox2.Add(self.readButton,0)
        self.Bind(wx.EVT_BUTTON, self.onReadClick, self.readButton)

        self.copyButton = wx.Button(self, label="Copy")
        hbox3.Add(self.copyButton,0)
        self.Bind(wx.EVT_BUTTON, self.onCopyClick, self.copyButton)

        self.eraseButton = wx.Button(self, label="Erase")
        hbox3.Add(self.eraseButton,0)
        self.Bind(wx.EVT_BUTTON, self.onEraseClick, self.eraseButton)

        self.resultGrid = wx.grid.Grid(self)
        self.resultGrid.CreateGrid(10,3)
        self.resultGrid.SetColLabelValue(0, "Track 1")
        self.resultGrid.SetColLabelValue(1, "Track 2")
        self.resultGrid.SetColSize(1,200)
        self.resultGrid.SetColLabelValue(2, "Track 3")
        self.resultGrid.EnableDragColSize(True)
        hbox4.Add(self.resultGrid,1)

        vbox.Add(hbox1 , 1)
        vbox.Add(hbox2 , 1)
        vbox.Add(hbox3 , 1)
        vbox.Add(hbox4 , 4)

        self.SetSizer(vbox)

    def onFileButton(self, event):
        self.fileWindow = wx.FileDialog(self, message="Select an output file", defaultDir= os.getcwd(), defaultFile='output.txt',style=wx.OPEN|wx.CHANGE_DIR)
        if self.fileWindow.ShowModal() == wx.ID_OK:
            self.file = self.fileWindow.GetPath()
    def onClose(self,event):
        self.pyMagStripe.closeSerial()
        self.frame.Destroy()

    def onScan(self, event):
        self.frame.statusBar.SetStatusText("Scanning...")
        self.frame.statusBar.Refresh()
        self.port = self.pyMagStripe.scan()[-1][1]
        self.serialOptions.SetValue(self.port)
        self.frame.statusBar.SetStatusText("")
        self.frame.statusBar.Refresh()

    def onSerialSelect(self,event):
        self.port = self.serialOptions.GetValue()

    def onConnectClick(self, event):
        if self.pyMagStripe.connect(self.port,10):
            self.frame.statusBar.SetStatusText("Connected to " + self.port)
            self.frame.statusBar.Refresh()
        else:
            self.frame.statusBar.SetStatusText("Error Connecting to " + self.port)
            self.frame.statusBar.Refresh()
            self.pyMagStripe.closeSerial()
            
    def onReadClick(self,event):
        self.frame.statusBar.SetStatusText("Waiting to read. Swipe a card.")
        self.frame.statusBar.Refresh()
        self.track1, self.track2, self.track3 = self.pyMagStripe.read()
        if self.track1 != -1:
            self.resultGrid.InsertRows(pos = 0, numRows = 1)
            self.resultGrid.SetCellValue(0,0,self.track1)
            self.resultGrid.SetCellValue(0,1,self.track2)
            self.resultGrid.SetCellValue(0,2,self.track3)
            self.resultGrid.DeleteRows(pos = 10, numRows = 1)
            self.pyMagStripe.writeToFile(self.file,self.track1 + " " + self.track2 + " " + self.track3)
            self.frame.statusBar.SetStatusText("")
            self.frame.statusBar.Refresh()
        else:
            self.frame.statusBar.SetStatusText("Error reading. Disconnected from reader.")
            self.frame.statusBar.Refresh()
        return self.track1
            
    def onCopyClick(self,event):
        self.onReadClick(wx.EVT_BUTTON)
        if self.track1 != -1:
            self.frame.statusBar.SetStatusText("Waiting to write. Swipe a card.")
            self.frame.statusBar.Refresh()
            self.pyMagStripe.write(self.track1, self.track2, self.track3)
            self.frame.statusBar.SetStatusText("")
            self.frame.statusBar.Refresh()
        
    def onEraseClick(self,event):
        self.frame.statusBar.SetStatusText("Waiting to erase. Swipe a card.")
        self.frame.statusBar.Refresh()
        status = self.pyMagStripe.erase()
        if status == 0:
            self.frame.statusBar.SetStatusText("")
            self.frame.statusBar.Refresh()
        else:
            self.frame.statusBar.SetStatusText("Error while erasing.")
            self.frame.statusBar.Refresh()
    def onBox(self,event):
        return

class pyMagStripeFrame(wx.Frame):
    def __init__(self, parent, title, size):
        wx.Frame.__init__(self,parent,title=title,size=size)
        self.statusBar = self.CreateStatusBar()

        fileMenu = wx.Menu()
        menuAbout = fileMenu.Append(wx.ID_ABOUT, "&About", "About")
        menuExit = fileMenu.Append(wx.ID_EXIT , "&Exit" , "Exit")
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        self.SetMenuBar(menuBar)

        self.Bind(wx.EVT_MENU , self.onAbout, menuAbout)
        self.Bind(wx.EVT_MENU , self.onExit, menuExit)

    def onAbout (self, e):
        message = wx.MessageDialog(self,"pyMagStripe version 0.1","pyMagStripe", wx.OK)
        message.ShowModal()
        message.Destroy()
    def onExit (self, e):
        self.Close(True)
try:
    app = wx.App(False)
    frame = pyMagStripeFrame(None,"pyMagStripe",(500,600))
    panel = pyMagStripePanel(frame)
    frame.Show()
    app.MainLoop()
finally:
    del app
