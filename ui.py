import os
import tkinter as tk
from tkinter import ttk
import re

class LabelEntry():
    def __init__(self, master, text='', cmd=None, label=None, **kw):
        self.master = master
        if label != None:
            label = tk.Label(master, text=label, bg='#232323', fg='white', font=(14))
            label.pack(side='left', padx=5)
        self.entry = tk.Entry(master, **kw)    
        self.entry.pack(side='left', fill='x', expand=True, padx=5)
            
    def add_button(self, *data):
        text, action = data
        btn = add_button(self.master, text, action)
        btn.pack(side='left', padx=5)
        return btn
        
    def get(self):
        return self.entry.get()
        
    def set(self, text):
        entry = self.entry
        n = len(entry.get())
        entry.delete(0, n)
        entry.insert(0, text)       
        
         
def add_entry(frame, label=None, button=None, **kw):                      
    entry = LabelEntry(frame, label=label, **kw)
    if button != None:
        entry.add_button(button)   
    return entry

        
class Text(tk.Text):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)    
        self.limit = 1000
                 
    def clear_all(self):
        self.tag_delete(self.tag_names())
        self.delete('1.0', 'end')         
        
    def delete_text_before_paste(self):        
        p = self.tag_ranges('sel')
        if p == () or p == None:
            return
        a, b = p                
        self.tag_add('paste', str(a) + '-1c', str(b) + '+1c')
        self.delete(a, b)
        
    def on_key_v(self, event):   
        self.delete_text_before_paste()  
        self.update_tag()  
        
    def set_text(self, text):
        self.clear_all()
        self.text = text
        self.insert('insert', text)         
        self.linecount = text.count('\n')   
        self.update_tag()  
           
    def get_text(self, tag=None):
        if tag != None:
            p = self.tag_ranges(tag)
            if p == ():
                return ''
            idx1, idx2 = p
            return self.get(idx1, idx2)
        return self.get('1.0', 'end -1c')            
        
    def puts(self, *lst, end='\n'):
        text = ''
        for s in lst:
            text += str(s) + ' '
        if len(text) > self.limit:
            text = text[0:self.limit]    
        self.insert('end', text + end)
        
    def puts_tag(self, text, tag=None, head='', end='\n'):
        self.insert('end', head)        
        idx1 = self.index('end')
        if len(text) > 1024:
            text = text[0:1023]   
        self.insert('end', text)        
        idx2 = self.index('end')
        if tag != None:
            self.tag_add(tag, idx1, idx2)
        self.insert('end', end)     
        
class TextObj(Text):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.init_all()        
        self.vars = {}
        self.text = None       
        self.msg = self
        self.config(foreground='#121')
        self.config(background='#f5f5f3')    
        self.tag_config('bold', font=('bold'), background='#ddd')       
        keys = 'from|import|def|class|if|else|elif|for|in|then|dict|list|continue|return'
        keys += '|None|True|False|while|break|pass|with|as|try|except|not|or|and|do|const|local'
        self.keywords = keys.split('|')
        self.init_config()        
        self.init_pattern()         
        #self.add_scrollbar(self.master)   
        self.place(x=0, y=0, relwidth=1, relheight=1)   
        

    def init_all(self):
        self.vars = {}
        self.font = ('Mono', 10) 
        self.limit = 32768
        self.text = None       
        self.pattern = None
        self.config(foreground='#121')
        self.config(background='#f5f5f3')    
        self.tag_config('bold', font=('bold'), background='#ddd')  
        self.tag_config('find', font=('bold'), foreground='#111', background='yellow')
          
        self.click_time = 0
        self.filename = None
  
        for key in ['<F6>', '<Tab>', '<Control-period>']:
            self.bind(key, self.on_add_tab)
        for key in ['<F2>', '<Shift-Tab>', '<Control-comma>']:
            self.bind(key, self.on_remove_tab)  
        self.bind('<Control-v>', self.on_key_v)      
        
    def select_lines(self):
        p = self.tag_ranges('sel') 
        if p == ():
            self.tag_add('sel', 'insert linestart', 'insert lineend')
        else:
            self.tag_add('sel', 'sel.first linestart', 'sel.first lineend')
                
    def edit_selected_text(self, edit_action):
        if self.tag_ranges('sel') == ():
            idx1 = self.index('insert')
            idx2 = self.index(idx1 + ' lineend')
        else:
            idx1 = self.index('sel.first linestart')
            idx2 = self.index('sel.last lineend')  
        text = edit_action(self.get(idx1, idx2))        
        self.replace(idx1, idx2, text)   
        n = text.count('\n')
        i = self.get_line_index(idx1) 
        a = str(i) + '.0'
        b = str(i+n) + '.end'
        self.tag_add('sel', a, b) 
        self.update_add([i, i+n])
        
    def remove_one_tab(self, text):     
        lst = []
        for s in text.splitlines():
            s = s[:4].strip() + s[4:]
            lst.append(s)
        return '\n'.join(lst)
    
    def add_one_tab(self, text):
        lst = []
        for s in text.splitlines():
            lst.append('    ' + s)
        return '\n'.join(lst)   
        
    def on_add_tab(self, event=None):
        self.select_lines()
        self.edit_selected_text(self.add_one_tab) 
        
    def on_remove_tab(self, event=None):
        self.select_lines()
        self.edit_selected_text(self.remove_one_tab) 

    def init_config(self):    
        monofont = ('Mono', 10)     
        self.font = monofont  
        self.color = '#121'
        self.config(font=monofont)
        #self.config(padx=5)
        self.config(foreground=self.color)
        self.config(background='#f5f5f3')        
        self.config(undo=99)          
        self.config(exportselection=True)
        self.vars = {}

        bold = ('bold')
        self.tag_config('key', font=bold, foreground='#338')
        self.tag_config('class', font=bold, foreground='#338')
        self.tag_config('classname', font=bold, foreground='#383')
        self.tag_config('str1', foreground='#a73')
        self.tag_config('str2', font=bold, foreground='#a73')
        self.tag_config('int', font=bold, foreground='#383')
        self.tag_config('op',  foreground='gray')
        self.tag_config('self',  foreground='#333')
        self.tag_config('comments',  foreground='#789')
        self.tag_config('selected',  background='lightgray')
        self.tag_config('find', font=bold, foreground='#111', background='#a5a5a3')
        self.key_tagnames = ['key', 'class', 'classname', 'str1', 'str2', 
                             'int', 'op', 'self', 'comments', 'find']
        
    def init_dark_config(self):
        monofont = ('Mono', 10)
        self.color = '#d8dee9'
        self.config(font=monofont)
        #self.config(padx=5)
        self.config(foreground='#d8dee9')
        self.config(background='#323c44')        
        self.config(undo=99)          
        self.config(exportselection=True)
        self.config(insertbackground="#f0a050")
        self.config(selectbackground="#000", selectforeground="#000")
        self.tag_config('insert', background="#343434")
        self.tag_config('sel', background ='#202327',  foreground='#777777')
        self.tag_config('find', foreground='black', background='#999')
        self.tag_config('Q3', foreground='#99c794')
        
        self.vars = {}
        bold = (monofont[0], monofont[1], 'bold')
        self.tag_config('key', foreground='#c695c6')
        self.tag_config('class', foreground='#9695d6')
        self.tag_config('classname', foreground='#f9ae58')
        self.tag_config('str1', foreground='#99c794')
        self.tag_config('str2', foreground='#99c794')
        self.tag_config('int',  foreground='#f9ae58')
        self.tag_config('op',  foreground='#5fb4b4')
        self.tag_config('self',  foreground='#e37373')
        self.tag_config('comments',  foreground='#a6acb9')
        self.tag_config('selected',  background='#f9ae58')
        self.tag_config('find',  background='yellow')

        self.key_tagnames = ['key', 'class', 'classname', 'str1', 'str2', 'int', 'op', 'self', 'comments'
                           'h1', 'h2', 'h3', 'hide'] 
        
    def add_linebar(self, frame):
        self.linebar = TextLinebar(frame)
        self.linebar.pack(side='left', fill='y', expand=False) 
        self.pos = self.dlineinfo('@0,0')
        self.configure(yscrollcommand=self.on_scroll)   
        
    def init_pattern(self):
        keys = 'from|import|def|class|if|else|elif|for|in|then|dict|list|continue|return'
        keys += '|None|True|False|while|break|pass|with|as|try|except|not|or|and|do|const|local'
        p0 = '(?P<class>class)\s+(?P<classname>\w+)'
        p1 = '|(?P<str1>\'[^\'\n]*\')|(?P<str2>\"[^\"\n]*\")'        
        p2 = '|(?<![\w])(?P<int>\d+)|(?P<op>[\=\+\-\*\/\(\)\.\%])|(?P<self>self)'       
        p3 = '|(?<![\w])(?P<key>%s)(?![\w])' % keys     
        p4 = '|(?P<comments>#.*)'     
        self.pattern = re.compile(p0 + p1 + p2 + p3 + p4)          

    def split_tokens(self, text):    
        lst = [] 
        for m in re.finditer(self.pattern, text):
            i, j = m.start(), m.end()            
            for tag, s in m.groupdict().items():
                if s != None:                           
                    lst.append((s, text.find(s, i), tag))  
        return lst
                    
    def remove_tags(self, idx1, idx2):        
        for s in self.key_tagnames:
            self.tag_remove(s, idx1, idx2)

    def add_tag_list(self, i, lst):
        head = str(i) + '.'
        for p in lst:        
            s, j, tag = p
            idx1 = head + str(j)
            idx2 = head + str(j+len(s))
            self.tag_add(tag, idx1, idx2)
        
    def tag_line(self, i, text):
        self.remove_tags('%d.0'%i, '%d.end'%i)      
        s = text.strip()
        if s == '':
            return
        elif s[0] == '#':      
            lst = [(text, 0, 'comments')]  
        else:            
            lst = self.split_tokens(text)
        if lst != []:
            self.add_tag_list(i, lst)
        return lst
        
    def tag_key(self, key, tag='bold', text=None):
        start = '1.0'
        pend = '+%dc' % len(key)
        if text == None:
            text = self.get_text()
        for s in re.findall(key, text):                    
            pos = self.search(key, start)  
            self.tag_add(tag, pos, pos + pend)
            start = pos + pend
        self.tag_raise(tag)    
        
    def update_tag(self, key=None):   
        if self.pattern == None:
            return            
        i = 1    
        text = self.get_text()
        for line in text.splitlines():           
            self.tag_line(i, line)       
            i += 1
        if key != None:
            self.tag_key(key, 'find', text=text)
        self.pre_text = text         
    
    def set_text(self, text):
        self.clear_all()
        self.text = text
        self.insert('insert', text)         
        self.linecount = text.count('\n')   
        self.update_tag()        
        
    def select_line(self, idx):
        i, j = self.get_pos(idx)
        idx1 = self.get_idx(i, 0)
        idx2 = self.get_idx(i, 'e')
        self.tag_add('sel', idx1, idx2)
        self.see(idx)          
        
class MsgBox(Text):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        pass
        
    def update_tag(self):
        pass
        
    def flush(self, text=''):
        return
        
    def write(self, text):
        if text.strip() == '':
            return
        self.insert('insert', str(text))

class ScrollBar():
    def __init__(self, target):
        self.base = target
        scrollbar = ttk.Scrollbar(target, command=target.yview, cursor='arrow')
        scrollbar.place(relx=0.987, w=16, rely=0, relheight=1)
        self.scrollbar =  scrollbar
        target.config(yscrollcommand = self.on_scroll)
        target.bind('<Button-4>', self.on_scrollup)
        target.bind('<Button-5>', self.on_scrolldown)  
        
    def on_scrollup(self, event):  
        x, y = self.base.winfo_pointerxy()
        if self.base.winfo_containing(x, y):
           self.base.yview_scroll(-1, 'units')
    
    def on_scrolldown(self, event):
        x, y = self.base.winfo_pointerxy()
        if self.base.winfo_containing(x, y):
            self.base.yview_scroll(1, 'units')        
        
    def on_scroll(self, arg0, arg1):
        self.scrollbar.set(arg0, arg1) 



class CodePanel(tk.Text):
    def __init__(self, master, **kw):
        super().__init__(master, cursor='arrow', **kw)
        self.style = 'h'
        self.relief = 'flat'
        self.master = master
        self.config(background = "#d9d9d9")
        self.config(state= "disabled", font=('Mono', 10))
        self.widgets = []
        
    def add(self, widget):
        self.widgets.append(widget)
        self.window_create('end', window=widget)
            
    def add_scrollbar(self):
        self.scrollbar = ScrollBar(self)        

    def reset(self):        
        self.delete('1.0', 'end')
        for widget in self.widgets:
            widget.destroy()
        self.widgets = []

def set_icon(app, icon):
    if icon == None:
        icon = '/home/athena/data/icon/dev.png'
    try:    
        icon = os.path.realpath(icon)
        root = app.winfo_toplevel()
        root.tk.call('wm', 'iconphoto', root._w, tk.PhotoImage(file=icon))  
    except:
        print('load icon', icon, 'fail')

def App(title='A frame', size=(800, 600), icon=None):    
    root = tk.Tk()
    root.title(title)
    root.tk.setvar('root', root)
    appname = title.replace(' ', '')
    root.tk.setvar('appname', appname)
    w, h = size
    root.size = size
    root.geometry('%dx%d'%(w, h)) 
    set_icon(root, icon)
    root.tk.setvar('app', root)
    return root

