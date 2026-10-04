"""Build the local launcher/evaluation app, not a native ROS/Gazebo engine.

Run desktop builds on their target OS. Artifacts are not signed or uploaded.
The Docker client/engine remain independently versioned, cached images.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from www_posim_autonomy import __version__

def run(*args):subprocess.run(args,cwd=ROOT,check=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('target',choices=['wheel','desktop','deb'])
    p.add_argument('--output',type=Path,default=ROOT/'dist')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    if a.target=='wheel':
        run(sys.executable,'-m','build','--wheel','--outdir',str(out))
    elif a.target=='desktop':
        run(sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir',
            '--name','www-posim','--paths',str(ROOT),'--distpath',str(out),
            '--workpath',str(ROOT/'build/desktop'),'--specpath',str(ROOT/'build'),
            '--collect-data','www_posim_autonomy','--exclude-module','rclpy',
            '--exclude-module','numpy','--exclude-module','scipy',
            str(ROOT/'packaging/desktop_entry.py'))
        executable=out/'www-posim'/('www-posim.exe' if os.name=='nt' else 'www-posim')
        run(str(executable),'--version')
        if platform.system()=='Darwin':
            # Build a normal Finder-launchable app using the same verified entry.
            run(sys.executable,'-m','PyInstaller','--noconfirm','--windowed',
                '--name','WWW-POSIM-Evaluation','--paths',str(ROOT),'--distpath',str(out),
                '--workpath',str(ROOT/'build/app'),'--specpath',str(ROOT/'build'),
                '--collect-data','www_posim_autonomy','--exclude-module','rclpy',
                '--exclude-module','numpy','--exclude-module','scipy',
                str(ROOT/'packaging/desktop_entry.py'))
    else:
        if not shutil.which('dpkg-deb'):p.error('Build .deb on Debian/Ubuntu, with dpkg-deb installed.')
        tree=ROOT/'build/deb';shutil.rmtree(tree,ignore_errors=True)
        (tree/'DEBIAN').mkdir(parents=True)
        code=tree/'usr/lib/www-posim/www_posim_autonomy';shutil.copytree(ROOT/'www_posim_autonomy',code,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        (tree/'usr/bin').mkdir(parents=True)
        launcher=tree/'usr/bin/www-posim'
        launcher.write_text('#!/bin/sh\nexport PYTHONPATH=/usr/lib/www-posim${PYTHONPATH:+:$PYTHONPATH}\nexec /usr/bin/python3 -m www_posim_autonomy.entry "$@"\n');launcher.chmod(0o755)
        (tree/'DEBIAN/control').write_text(f'Package: www-posim-client\nVersion: {__version__}\nArchitecture: all\nMaintainer: IOES-Lab <info.ioes.lab@gmail.com>\nDepends: python3 (>= 3.10), python3-tk, python3-websocket, python3-yaml, python3-numpy, python3-scipy\nSection: education\nPriority: optional\nDescription: WWW-POSIM local launcher and server evaluation client\n Runs participant code locally and controls separately installed simulator images.\n Does not install a native ROS, Gazebo or POSIM engine.\n')
        (tree/'usr/share/applications').mkdir(parents=True)
        (tree/'usr/share/applications/www-posim.desktop').write_text('[Desktop Entry]\nName=WWW-POSIM Evaluation\nExec=www-posim evaluation\nType=Application\nCategories=Education;Science;\nTerminal=false\n')
        run('dpkg-deb','--root-owner-group','--build',str(tree),str(out/f'www-posim-client_{__version__}_all.deb'))
    artifacts=[]
    if a.target=='desktop':
        for path in [out/'www-posim',out/'WWW-POSIM-Evaluation.app']:
            if not path.is_dir():continue
            destination=out/f'{path.name}-{__version__}-{platform.system().lower()}-{platform.machine()}.tar.gz'
            with tarfile.open(destination,'w:gz') as archive:archive.add(path,arcname=path.name)
            artifacts.append(destination)
    elif a.target=='wheel':artifacts=list(out.glob(f'www_posim_autonomy-{__version__}-*.whl'))
    else:artifacts=[out/f'www-posim-client_{__version__}_all.deb']
    prior=out/'installer-manifest.json'
    saved=json.loads(prior.read_text()).get('files',[]) if prior.exists() else []
    saved=[f for f in saved if (out/f['name']).exists() and f['name'] not in {p.name for p in artifacts} and f.get('build_os')]
    manifest=dict(version=__version__,build_os=platform.system(),architecture=platform.machine(),
        contains_native_simulator=False,developer_signed=False,published=False,
        files=saved+[dict(name=f.name,bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
            build_os=platform.system(),architecture='all' if a.target in ('wheel','deb') else platform.machine()) for f in artifacts])
    (out/'installer-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
