import tornado
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.template
import chatroom
import json

def DEBUG(*args,**kwargs):
    print(args, kwargs)

class MainHandler(tornado.web.RequestHandler):
    def initialize(self, rooms_manager):
        self.rooms_manager = rooms_manager

    def handle_message(self, message):
        if(self.callback):
            self.write("%s(%s);\n" % (self.callback, json.dumps(message)));
        elif(self.format == 'shell'):
            #self.write("<%s>: %s" % (m
            self.write(message + "\n")
        else:
            self.write(message)
        self.flush()

    @tornado.web.asynchronous
    def get(self, room_name):
        self.callback = self.get_argument('callback', default=None)
        self.format = self.get_argument('format', default=None)

        DEBUG("Looking for room")
        room = self.rooms_manager.find_room(room_name)
        DEBUG("GOT ROOM ", room)
        DEBUG("ADDING MEMBER")
        room.add_member(self)

    def post(self, room_name):
        room = self.rooms_manager.find_room(room_name)
        message = self.get_argument('message')
        room.send(message)


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, rooms_manager):
        DEBUG("SETTING UP ROOMS MANAGER ")
        #super.initialize(self)
        self.rooms_manager = rooms_manager

    def handle_message(self, message):
        self.write_message(message)

    def open(self, room_name):
        DEBUG("WebSocket opened room ", room_name)
        self.room_name = room_name
        self.room = self.rooms_manager.find_room(self.room_name)
        self.room.add_member(self)

    def on_message(self, message):
        self.room.send(message)

    def on_close(self):
        DEBUG("WebSocket closed")
        self.room.remove_member(self)


class PagesHandler(tornado.web.RequestHandler):
    def initialize(self, template_dir, rooms_manager):
        DEBUG("PagesHandler Loading")
        self.rooms_manager = rooms_manager
        self.loader = tornado.template.Loader(template_dir)
        self.pages = dict()
        for i in ['index.html', 'room.html']:
            DEBUG("Loading Template ", i)
            self.pages[i] = self.loader.load(i)

    def get(self, *args):
        DEBUG("ARGS IS ", *args)
        room=None
        if(len(args) == 1):
            page = args[0]
        elif(len(args) == 2):
            room = args[0]
            if(args[1] == '.html'):
                page = 'room.html'
            
        if(self.pages[page]):
            self.write(self.pages[page].generate(rooms_manager=self.rooms_manager, room=room))



amqp_url = 'amqp://guest:guest@localhost:5672/%2F'
rooms_manager = chatroom.RoomsManager(amqp_url)


application = tornado.web.Application([
    (r"/ws/(\w+)", WebSocketHandler, dict(rooms_manager=rooms_manager)),
    (r"/room/(\w+)", MainHandler, dict(rooms_manager=rooms_manager)),
    (r"/room", MainHandler, dict(rooms_manager=rooms_manager)),
    (r"/room/(\w+)(.html)", PagesHandler, dict(template_dir='./', rooms_manager=rooms_manager)),
    (r"/(\w+.html)?", PagesHandler, dict(template_dir='./', rooms_manager=rooms_manager)),
])

if __name__ == "__main__":
    application.listen(8888)
    DEBUG("Listening on port http://localhost:8888/")
    tornado.ioloop.IOLoop.instance().start()
