import PySimpleGUI as sg


class dbTableView():
    def __init__(self, table):  
        self.table = table
        self.name = table.name
        self.data = table.getdata()
        self.title = table.db.name + '.db - ' + table.name
        
    def get_layout(self):    
        headers = ['name', 'data']       
        data = self.data
        n = len(data)
        tab_layout = [[sg.Text(self.title)],[sg.Table(data, headings=headers, num_rows = n, 
                       expand_x=True,expand_y=True,justification='left', key='-TABLE-')],]
        return tab_layout             
    
    def show(self):       
        layout = self.get_layout()
        font = ('Mono', 15)
        window = sg.Window('dbTableView : ' + self.title, layout, size=(1000, 800), 
                             resizable=True, finalize=True, font=font)
        window.bind('<Configure>', "Configure")    
        self.window = window
        
        while True:
            event, values = window.read()
            if event == sg.WINDOW_CLOSED:
                break      
        window.close()  
        
class dbView():
    def __init__(self, db, table=None):  
        self.db = db
        if table == None:
            table = db.get('tables')[0]
        self.name = table
        self.table = db.get_table(self.name)        
        self.data = self.table.getdata()
        self.title = db.name + '-' + self.name
        
    def get_layout(self):    
        headers = self.table.getkeys()      
        data = self.data
        n = len(data)
        self.buttons = self.db.get('tables')
        buttons = []
        for s in self.buttons:
            buttons.append(sg.Button(s, font=('Mono', 12)))
        col1 = [buttons]
        col2 = [sg.Table(data, headings=headers, num_rows = n, 
                       expand_x=True,expand_y=True,justification='left', key='-TABLE-')]
        layout = [[col1, col2]]
        return layout             
        
    def select_table(self, name):
        self.table = self.db.get_table(name)        
        self.data = self.table.getdata()
        self.title = self.db.name + '-' + name
        self.window.set_title(self.title)
        self.window[name].set_focus()
        data = self.data
        n = len(data)
        self.window['-TABLE-'].update(values=data, num_rows=n)
    
    def show(self):       
        layout = self.get_layout()
        font = ('Mono', 15)
        window = sg.Window(self.title, layout, size=(1000, 800), 
                             resizable=True, finalize=True, font=font)
        window.bind('<Configure>', "Configure")    
        self.window = window        
        
        while True:
            event, values = window.read()
            if event == sg.WINDOW_CLOSED:
                break      
            if event in self.buttons:
                self.select_table(event)                
        window.close()  
        

if __name__ == '__main__':   
    import DB
    db = DB.open('code')
    dbView(db).show()
    

