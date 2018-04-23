import http.server
import local_settings  # Mak sure you .gitignore this one ;)
import socketserver
import subprocess
import sys

PORT = 8080
IRSEND = '/usr/bin/irsend'
SSH = '/usr/bin/ssh'
#IRSEND = '/bin/echo'
AC_REMOTE = 'daikin-arc452a4'
TV_SERVER = 'bonobo'  # Must be a defined ssh alias.
TV_REMOTE = 'Samsung'

def eprint(*args, **kwargs):
  '''Print to stderr.'''
  print(*args, file=sys.stderr, **kwargs)
  sys.stderr.flush()

class IftttHandler(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
    body = ''
    try:
      self.automate()
      body = 'ok'
    except Exception as e:
      self.send_response(502, message='server error')
      body = str(e)
    self.send_header('Content-type', 'text/plain')
    self.end_headers()
    self.wfile.write(body.encode())
   
  def automate(self):
    '''Responds to paths like /<secret_key>/<device>/<cmd>
       where secret_key must match the constant KEY defined in local_settings.
    '''
    _, key, device, cmd = self.path.split('/', 3)
    if key != local_settings.KEY:
      self.send_response(403, message="forbidden")
      return

    if device == 'ac':
      eprint('calling:', IRSEND, 'SEND_ONCE', AC_REMOTE, cmd)
      subprocess.check_call([IRSEND, 'SEND_ONCE', AC_REMOTE, cmd])
      eprint('call done')
      self.send_response(200, message='ok')
    elif device == 'tv':
      eprint('calling: ', SSH, TV_SERVER, IRSEND, 'SEND_ONCE', TV_REMOTE, cmd)
      subprocess.check_call([SSH, TV_SERVER, IRSEND, 'SEND_ONCE',
                             TV_REMOTE, cmd])
      eprint('call done')
    else:
      eprint('unknown device')
      self.send_response(404, message='not found')
    return


bind = ('', PORT)
httpd = http.server.HTTPServer(bind, IftttHandler) 
eprint('serving at port', PORT)
httpd.serve_forever()


