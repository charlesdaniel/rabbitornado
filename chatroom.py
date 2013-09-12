from pika import adapters
import pika


class RoomsManager(object):
    def __init__(self, amqp_url, options={}):
        self.amqp_url = amqp_url
        self.rooms = dict()
        self.options = options
        if(options.has_key('exchange')):
            self.exchange = options.exchange
        else:
            self.exchange = 'rabbitornado'

    def find_room(self, room_name):
        if(not self.rooms.has_key(room_name)):
            if((self.options.has_key('tornado')) and (self.options['tornado'] == True)):
                self.rooms[room_name] = TornadoChatRoom(self.amqp_url, self.exchange, room_name)
            else:
                self.rooms[room_name] = ChatRoom(self.amqp_url, self.exchange, room_name)
        return self.rooms[room_name]

    def get_list(self):
        l = list()
        for i in self.rooms:
            r = self.rooms[i]
            l.append([r.topic, len(r.members)])
        return l



def DEBUG(*args, **kwargs):
    print(args, kwargs)


class ChatRoom(object):
    connection = dict()
    channel = None

    def __init__(self, amqp_url, exchange, topic):
        self.amqp_url = amqp_url
        self.exchange = exchange
        self.topic = topic
        self.connection = None
        self.channel = None
        self.backbuffer = list()
        self.members = list()
        self.connect()

    def connect(self):
        #if(not ChatRoom.connection.has_key(self.amqp_url)):
            #print "CONNECTION DOESN'T EXIST CREATING FOR ROOM ", self.topic
            parameters = pika.URLParameters(self.amqp_url)
            self.connection = ChatRoom.connection[self.amqp_url] = pika.SelectConnection(parameters, self.on_connected)
        #else:
            #print "CONNECTION EXISTS CREATING FOR ROOM ", self.topic
            #if(self.connection == None):
                #self.connection = ChatRoom.connection[self.amqp_url]
            #self.on_connected(self.connection)

    def on_connected(self, connection):
        # Invoked when the connection is open
        print "connection open ", connection, "\n"
        self.channel = self.connection.channel(self.on_channel_open)

    def on_channel_open(self, new_channel):
        #self.channel = new_channel
        self.channel.exchange_declare(callback=self.exchange_declared, exchange=self.exchange, exchange_type="topic", durable=False, auto_delete=True)

    def exchange_declared(self, frame):
        self.channel.queue_declare(queue=self.topic, durable=False, exclusive=True, auto_delete=True, callback=self.on_queue_called)

    def on_queue_called(self, frame):
        self.channel.queue_bind(callback=self.on_queue_bound, exchange=self.exchange, queue=self.topic, routing_key=self.topic)

    def on_queue_bound(self, frame):
        self.channel.basic_consume(self.handle_delivery, queue=self.topic)
        while (len(self.backbuffer) > 0):
            msg = self.backbuffer.pop()
            self.send(msg)

    def handle_delivery(self, channel, method, header, body):
        for r in self.members:
            DEBUG("SENDING TO MEMBER ", r, " KEY ", method.routing_key, " BODY ", body)
            r.handle_message(method, header, body)
        self.channel.basic_ack(method.delivery_tag)

        DEBUG("GOT HANDLE DELIVERY ", channel, " METHOD ", method, " HEADER ", header, "\n")
        DEBUG(" BODY ", body)

    def start(self):
        self.connection.ioloop.start()

    def stop(self):
        self.connection.ioloop.stop()

    def add_member(self, member):
        DEBUG("ADD_MEMBER ", member)
        self.members.append(member)

    def remove_member(self, member):
        DEBUG("REMOVE_MEMBER ", member)
        self.members.remove(member)

    def send(self, message):
        if(self.channel):
            self.channel.basic_publish(exchange=self.exchange, routing_key=self.topic, body=message)
        else:
            DEBUG("CHANNEL NOT OPEN BACK BUFFERING: ", message)
            self.backbuffer.append(message)


class TornadoChatRoom(ChatRoom):
    connection = dict()

    def connect(self):
        #if(not TornadoChatRoom.connection.has_key(self.amqp_url)):
            #print "TORNADOCHATROOM NO CONNECTION EXISTS CREATING CONNECTION  "
            parameters = pika.URLParameters(self.amqp_url)
            self.connection = TornadoChatRoom.connection[self.amqp_url] = adapters.TornadoConnection(parameters, on_open_callback=self.on_connected)
        #else:
            #print "TORNADOCHATROOM CONNECTION EXISTS REUSING"
            #if(self.connection == None):
                #self.connection = TornadoChatRoom.connection[self.amqp_url]
            #self.on_connected(self.connection)


    def add_member(self, member):
        super(TornadoChatRoom, self).add_member(member)
        member.handle_message(None, None, "Hello, welcome to the %s room" % (self.topic))
        member.handle_message(None, None, "There are currently %d clients" % (len(self.members)))
        


if __name__ == "__main__":
    try:
        c = ChatRoom('amqp://guest:guest@localhost:5672/%2F', 'foobar')
        c.connect()
        # Loop so we can communicate with RabbitMQ
        c.connection.ioloop.start()
    except KeyboardInterrupt:
        # Gracefully close the connection
        c.connection.close()
        # Loop until we're fully closed, will stop on its own
        c.connection.ioloop.start()
