"""Small installed Evaluation window: save setup once, then Practice/Evaluate."""
import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox
from .connect import API
from .evaluate import evaluate

TASKS=('surface_station','surface_gates','surface_slalom','underwater_gate','underwater_path','underwater_return')


def main():
    window=tk.Tk();window.title('WWW-POSIM · Evaluation');window.geometry('720x860')
    window.minsize(660,800)
    root=Path.home()/'.www-posim';root.mkdir(parents=True,exist_ok=True)
    settings=root/'evaluation-settings.json'
    try:saved=json.loads(settings.read_text())
    except (OSError,ValueError):saved={}
    frame=ttk.Frame(window,padding=20);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='WWW-POSIM · Run your autonomy code',font=('',19,'bold')).pack(anchor='w')
    ttk.Label(frame,text='Your PC runs the algorithm. Official Gazebo and scoring run on the server.\nPractice uses your running, licensed local simulator.',wraplength=660).pack(anchor='w',pady=(8,15))
    values={}
    defaults={'server':'https://YOUR-SERVER/api','local':'http://127.0.0.1:3300/api','email':'','alias':'Participant','task':TASKS[0],
              'command':json.dumps(['python3','-m','www_posim_autonomy.buoy_avoidance']),'output':str(root/'evaluations'),
              'client_image':'wwos-autonomy-client:0.2.2','project':str(Path.cwd())}
    for key,label in [('server','Official server API'),('local','Local simulator API'),('email','Email'),('alias','Public alias'),('task','Task'),('command','Local command (JSON argument list)'),('project','Code directory'),('client_image','Local ROS client image (blank for native ROS2 Python)'),('output','Results folder')]:
        ttk.Label(frame,text=label).pack(anchor='w')
        var=tk.StringVar(value=saved.get(key,defaults[key]));values[key]=var
        field=ttk.Combobox(frame,textvariable=var,values=TASKS,state='readonly') if key=='task' else ttk.Entry(frame,textvariable=var)
        field.pack(fill='x',pady=(2,8))
    password=tk.StringVar()
    ttk.Label(frame,text='Password (this run only; never saved)').pack(anchor='w')
    ttk.Entry(frame,textvariable=password,show='●').pack(fill='x',pady=(2,10))
    status=tk.StringVar(value='Ready. Start the local simulator first for practice.')
    ttk.Label(frame,textvariable=status,wraplength=660).pack(anchor='w',pady=8)
    messages=queue.Queue();cancel=threading.Event();worker=None;closing=False
    buttons=ttk.Frame(frame);buttons.pack(fill='x',pady=8)
    def start(practice):
        nonlocal worker
        if worker and worker.is_alive():return
        try:
            data={k:v.get().strip() for k,v in values.items()};command=json.loads(data['command'])
            if not isinstance(command,list) or not command or any(not isinstance(x,str) or not x for x in command):raise ValueError('Command must be a JSON list, e.g. ["python3","my_controller.py"].')
            settings.write_text(json.dumps(data,indent=2));settings.chmod(0o600)
        except Exception as error:messagebox.showerror('Setup',str(error));return
        secret=password.get();password.set('');cancel.clear()
        run_root=Path(data['output'])/(__import__('datetime').datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+data['task'])
        def run():
            try:
                api=API(data['local'] if practice else data['server'])
                if api.call('/auth/me')['enabled']:
                    api.call('/auth/login',dict(username=data['email'],password=secret))
                options=dict(practice=practice,alias=data['alias'],stop=cancel,notify=lambda text:messages.put(('status',text)))
                if data['client_image']:
                    from .client_container import evaluate_in_container
                    result=evaluate_in_container(api,data['task'],command,run_root,image=data['client_image'],project=data['project'],**options)
                else:
                    import os
                    previous=Path.cwd()
                    try:
                        os.chdir(data['project'])
                        result=evaluate(api,data['task'],command,run_root,**options)
                    finally:os.chdir(previous)
                messages.put(('done','Saved '+str(run_root/'result.json')+' · '+str(result['result']['report']['score'])))
            except Exception as error:messages.put(('error',str(error)))
        worker=threading.Thread(target=run,daemon=False);worker.start()
        practice_button.configure(state='disabled');official_button.configure(state='disabled');cancel_button.configure(state='normal')
        status.set('Connecting…')
    practice_button=ttk.Button(buttons,text='Practice locally',command=lambda:start(True));practice_button.pack(side='left',padx=(0,12))
    official_button=ttk.Button(buttons,text='Evaluate on server',command=lambda:start(False));official_button.pack(side='left')
    cancel_button=ttk.Button(buttons,text='Cancel',command=cancel.set,state='disabled');cancel_button.pack(side='right')
    ttk.Label(frame,text='Command runs locally without a shell. Cookies and passwords never enter arguments or result files.\nLocal exports are practice evidence; only server-observed runs enter the official leaderboard.',wraplength=660).pack(anchor='w',pady=12)
    def poll():
        try:
            while True:
                kind,text=messages.get_nowait();status.set(text)
                if kind in ('done','error'):
                    practice_button.configure(state='normal');official_button.configure(state='normal');cancel_button.configure(state='disabled')
        except queue.Empty:pass
        if closing and (not worker or not worker.is_alive()):window.destroy();return
        window.after(150,poll)
    def close():
        nonlocal closing
        closing=True;cancel.set();status.set('Stopping your algorithm and releasing your server slot…')
        if not worker or not worker.is_alive():window.destroy()
    window.protocol('WM_DELETE_WINDOW',close);poll();window.mainloop()

if __name__=='__main__':main()
