import tornado
from tornado.websocket import WebSocketHandler
import requests

API_USER_INFO = 'http://asdtdev.mooo.com/api/user/info'

class WSHandler(WebSocketHandler):

  logged_in = False

  def open(self):
    print('new connection')
    self.write_message("Hello World")
    
  def on_message(self, message):
    print('message received {}'.format(message) )

    if self.logged_in == False:
      response = requests.get(API_USER_INFO, headers={'Authorization': message})
      print("response.status_code", response.status_code)
      self.logged_in == True

  def on_close(self):
    print('connection closed')

application = tornado.web.Application([
  (r'/api', WSHandler),
])
 
 
if __name__ == "__main__":
  # Starting WS Server
  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(8081)
  tornado.ioloop.IOLoop.instance().start()
 