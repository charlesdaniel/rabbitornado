from pika import adapters
import pika

class RoomsManager(object):
    def __init__(self, amqp_url):
        self.amqp_url = amqp_url
        self.rooms = dict()

    def find_room(self, room_name):
        if(not self.rooms.has_key(room_name)):
            self.rooms[room_name] = ChatRoom(self.amqp_url, room_name)
        return self.rooms[room_name]

    def get_list(self):
        l = list()
        for i in self.rooms:
            r = self.rooms[i]
            l.append([r.topic, len(r.members)])
        return l


class ChatRoom(object):
    def __init__(self, amqp_url, topic):
        self.amqp_url = amqp_url
        self.topic = topic
        self.channel = None
        self.backbuffer = list()
        self.members = list()
        self.connect()

    def connect(self):
        #parameters = pika.ConnectionParameters()
        parameters = pika.URLParameters(self.amqp_url)
        #self.connection = pika.SelectConnection(parameters, self.on_connected)
        self.connection = adapters.TornadoConnection(parameters, on_open_callback=self.on_connected)
        print self.connection

    def add_member(self, member):
        print "ADD_MEMBER ", member
        member.handle_message("Hello, welcome to the %s room" % (self.topic))
        member.handle_message("There are currently %d clients" % (len(self.members)))
        self.members.append(member)

    def remove_member(self, member):
        print "REMOVE_MEMBER ", member
        self.members.remove(member)

    def on_connected(self, connection):
        # Invoked when the connection is open
        print "connection open ", connection, "\n"
        self.connection.channel(self.on_channel_open)

    def on_channel_open(self, new_channel):
        self.channel = new_channel
        self.channel.queue_declare(queue=self.topic, durable=False, exclusive=True, auto_delete=True, callback=self.on_queue_called)

    def on_queue_called(self, frame):
        self.channel.basic_consume(self.handle_delivery, queue=self.topic)
        while (len(self.backbuffer) > 0):
            msg = self.backbuffer.pop()
            self.send(msg)

    def handle_delivery(self, channel, method, header, body):
        for r in self.members:
            print "SENDING TO MEMBER ", r, " BODY ", body
            r.handle_message(body)
        self.channel.basic_ack(method.delivery_tag)

        print "GOT HANDLE DELIVERY ", channel, " METHOD ", method, " HEADER ", header, "\n"
        print " BODY ", body

    def send(self, message):
        if(self.channel):
            self.channel.basic_publish(exchange='', routing_key=self.topic, body=message)
        else:
            print "BACK BUFFERING ", message
            self.backbuffer.append(message)



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
