import http.server
import local_settings  # Make sure you .gitignore this one ;)
import os
import socketserver
import subprocess
import sys
import time

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

  def success(self):
    eprint('call done')
    self.send_response(200, message='ok')

  def forbidden(self):
    eprint('forbidden')
    self.send_response(403, message="forbidden")
  
  def notFound(self):
    eprint('unknown device')
    self.send_response(404, message='not found')
   
  def automate(self):
    '''Responds to paths like /<secret_key>/<device>/<cmd>
       where secret_key must match the constant KEY defined in local_settings.
    '''
    _, key, device, cmd = self.path.split('/', 3)
    if key != local_settings.KEY:
      return self.forbidden()
    if device == 'ac':
      eprint('calling:', IRSEND, 'SEND_ONCE', AC_REMOTE, cmd)
      subprocess.check_call([IRSEND, 'SEND_ONCE', AC_REMOTE, cmd])
      return self.success()
    elif device == 'tv':
      eprint('calling: ', SSH, TV_SERVER, IRSEND, 'SEND_ONCE', TV_REMOTE, cmd)
      subprocess.check_call([SSH, TV_SERVER, IRSEND, 'SEND_ONCE',
                             TV_REMOTE, cmd])
      return self.success()
    elif device == 'healthz':
      return self.success()
    elif device == 'wait':
      time.sleep(int(cmd))
      return self.success()
    elif device == 'quit' and cmd == 'quit':
      self.success()
      eprint('exiting on user request')
      os._exit(0)
    return self.notFound()


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
  pass


bind = ('', PORT)
httpd = ThreadingHTTPServer(bind, IftttHandler) 
eprint('serving at port', PORT)
httpd.serve_forever()


