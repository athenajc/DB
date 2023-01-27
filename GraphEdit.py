import os
import re
import sys
import tkinter as tk
from tkinter import ttk
import aui
from aui import App, twoframe, add_textobj, add_msg, TreeView
from aui import ImageObj, Text
from fileio import get_path, realpath, fread, fwrite
from graphviz import Source

class Canvas(tk.Canvas):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.filename = None
        self.imageobj = None
        
    def open(self, filename):            
        self.filename = filename  
        self.imageobj = ImageObj(filename)
        self.update_tkimage()   
        
    def update_tkimage(self):
        self.delete('imageobj')
        self.tkimage = self.imageobj.get_tkimage()      
        self.create_image(0,0, image=self.tkimage, anchor='nw', tag='imageobj') 
        
class Editor(Text):
    def __init__(self, master, **kw):       
        super().__init__(master, **kw)
        self.init_dark_config()
        self.tag_config('find', foreground='black', background='#999')

def set_layout(master):
    frame1 = twoframe(master, style='top', sep=0.2)   # menubar, mainframe
    frame2 = twoframe(frame1.bottom, style='h', sep=0.2)  #LR tree -> top bottom
    frame3 = twoframe(frame2.right, style='v', sep=0.7)   #editor + msg
    frame4 = twoframe(frame3.top, style='h', sep=0.4)
    msg = add_msg(frame3.bottom)
    master.msg = msg
    sys.stdout = msg         
    return frame1, frame2, frame3, frame4, msg  
    
    
def dctview(dct=None):
    app = App('TreeView Editor', size=(1200, 900)) 
    frame1, frame2, frame3, frame4, msg = set_layout(app)
    
    editor = Editor(frame4.left)
    editor.open('/home/athena/tmp/Digraph.gv')
    canvas = Canvas(frame4.right)
    canvas.pack(fill='both', expand=True)
    #canvas.open('/home/athena/tmp/Source.gv.svg')
    tree = TreeView(frame2.left)
    tree.enable_edit()
    
    def save_text():
        text = editor.get_text()
        fwrite(editor.filename, text)
        msg.puts('save', editor.filename, 'ok')
        
    def update_graph():
        text = editor.get_text()
        fwrite(editor.filename, text)
        dot = Source(editor.get_text())        
        fn = dot.render(format='svg')        
        canvas.open(fn)
        
        
    update_graph()
    if dct == None:
        dct = {'a':123, 'b':['ab', 'cd', 'ef', {1:'test', 2:'pratice', 3:'operation'}]}
    tree.add_dct('', dct)
          
    buttons = [('Reset', tree.clear), 
               ('New', lambda event=None: tree.add_dct('', dct)),  
               ('Add', tree.new_node),  
               ('Save', save_text),  
                ('Update Graph', update_graph)              
               ]
    for cmd, act in buttons:
        app.add_button(frame1.top, cmd, act, side='left')
    app.mainloop() 

    
if __name__ == '__main__':       
     dctview()



