"""Run the ROS relay and student algorithm on the PC, without host ROS installs."""
import json
import os
from pathlib import Path
import platform
import subprocess
import threading
import uuid
from urllib.parse import urlparse


def evaluate_in_container(api,task,command,output,*,image,project=None,practice=False,
                          seed=0,alias='Participant',stop=None,notify=print,job_id=None):
    if not image or image.startswith('-'):raise ValueError('Choose a versioned client image.')
    stop=stop or threading.Event()
    project=Path(project or Path.cwd()).resolve()
    if not project.is_dir():raise ValueError('Project directory does not exist.')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    name='www-posim-client-'+uuid.uuid4().hex[:10]
    endpoint=urlparse(api.url);origin=endpoint._replace(path='',query='',fragment='').geturl()
    network=['--network','host'] if platform.system()=='Linux' else []
    # Docker Desktop forwards this special hostname to the PC loopback.
    if not network and endpoint.hostname in ('127.0.0.1','localhost'):
        endpoint=endpoint._replace(netloc='host.docker.internal'+(':'+str(endpoint.port) if endpoint.port else ''))
    payload=dict(server=endpoint.geturl(),origin=origin,cookie=api.cookie() or None,task=task,
        command=command,output='/results',practice=practice,seed=seed,alias=alias,job_id=job_id)
    process=subprocess.Popen(['docker','run','--rm','-i','--name',name,'--cpus','1','--memory','1g',
        *network,'--mount',f'type=bind,src={project},dst=/workspace',
        '--mount',f'type=bind,src={output},dst=/results','--workdir','/workspace',image],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    def output_lines():
        for line in process.stdout:notify(line.rstrip())
    threading.Thread(target=output_lines,daemon=True).start()
    try:
        process.stdin.write(json.dumps(payload));process.stdin.close()
        while process.poll() is None:
            if stop.wait(.25):
                subprocess.run(['docker','stop','--time','45',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=55)
                break
        code=process.wait(timeout=10)
        if code:raise RuntimeError('Local ROS client stopped. See the Evaluation log above.')
        result=json.loads((output/'result.json').read_text())
        return result
    except KeyboardInterrupt:
        subprocess.run(['docker','stop','--time','45',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=55)
        raise
    finally:
        if process.poll() is None:
            subprocess.run(['docker','stop','--time','45',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=55)
        if process.stdout:process.stdout.close()
