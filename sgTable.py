import PySimpleGUI as sg
from aui.layout import dict_table
import FileDB
    
data = {
  "Name":['a', 'b', 'c'],
  "calories": [420, 380, 390],
  "duration": [50, 40, 45]
}        

layout = dict_table(data)
    
window = sg.Window('Title', layout, resizable=True, finalize=True)
window.bind('<Configure>', "Configure")


while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED:
        break
    elif event == 'Configure':
        if window.TKroot.state() == 'zoomed':
            status.update(value='Window zoomed and maximized !')
        else:
            status.update(value='Window normal')

window.close()




