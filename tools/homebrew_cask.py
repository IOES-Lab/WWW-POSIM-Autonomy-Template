"""Render a checksum-pinned Cask for a built Mac application archive.

Use --url after publishing the identical archive to a release. With no URL,
the Cask installs the local build only; it is not a public distribution claim.
"""
import argparse
import hashlib
from pathlib import Path
from urllib.parse import urlparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from www_posim_autonomy import __version__

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--url')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();archive=a.archive.resolve()
    if not archive.is_file() or 'darwin' not in archive.name:p.error('Choose a built Darwin app archive.')
    url=a.url or archive.as_uri()
    if a.url and urlparse(url).scheme!='https':p.error('Published downloads require HTTPS.')
    if any(c in url for c in ('"','\n','\r','#','\\')):p.error('Unsupported URL characters.')
    sha=hashlib.sha256(archive.read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(f'''cask "www-posim" do
  version "{__version__}"
  sha256 "{sha}"
  url "{url}"
  name "WWW-POSIM Evaluation"
  desc "Local ROS algorithm and server Gazebo evaluation client"
  homepage "https://github.com/IOES-Lab/WWW-POSIM-Autonomy-Template"
  app "WWW-POSIM-Evaluation.app"
end
''')
    print('Wrote checksum-pinned '+str(a.output)+(' (local build only)' if not a.url else ''))

if __name__=='__main__':main()
