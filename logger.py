import json
import time
import chatroom
import MySQLdb
import tornado

amqp_url = 'amqp://guest:guest@localhost:5672/%2F'
rm = chatroom.RoomsManager(amqp_url)

class DB(object):
    def __init__(self):
        self.db_conn=None
        self.db_connect()
        
    def db_connect(self):
        import MySQLdb
        try:
            if(self.db_conn == None):
                self.db_conn = MySQLdb.connect('localhost', 'rabbitornado', 'rabbitornado', 'rabbitornado')
                self.db_conn.autocommit(True)
                self.write_cur = self.db_conn.cursor()
        except MySQLdb.Error, e:
            print "MySQLdb.Error %d: %s" % (e.args[0], e.args[1])
            
        return self.db_conn
    
    def log_chat(self, m_ts, m_to, m_from, m_content_type, m_topic, m_log):
        try:
            print "IN LOG CHAT"
            #self.cur.execute('insert into chat_logs (`ts`, `to`, `from`, `content_type`, `topic`, `message`) values (%s, %s, %s, %s, %s, %s)', (int(m_ts), m_to, m_from, m_content_type, m_topic, m_log))
            self.write_cur.execute('insert into chat_logs (`to`, `from`, `content_type`, `topic`, `message`) values (%s, %s, %s, %s, %s)', (m_to, m_from, m_content_type, m_topic, m_log))

        except Exception as f:
            print "Exxxxception ", f
        except MySQLdb.Error as e:
            print "MySQLdb.Error %d: %s" % (e.args[0], e.args[1])
            
    def get_logs(self, ts_start, ts_stop, m_topic):
        wheres = []
        vals = []
        if(ts_start != None):
            wheres.append('`ts`>=%d')
            vals.append(ts_start)
        if(ts_stop != None):
            wheres.push('`ts`<=%d')
            vals.append(ts_stop)
        if(m_topic != None):
            where.push('`topic`=%s')
            vals.append(m_topic)
            
        cur = self.db_conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("select * from chat_logs where " + ' and '.join(wheres), vals)
        rows = cur.fetchall()
        return rows


class LoggerService(object):
    db = DB()
    
    def handle_message(self, method, header, body):
        data = None
        #try:
        if True:
            data = json.loads(body)
            print "DATA IS ", data
            print "HEADRES IS ", header
            print "METHOD IS ", method
            
            m_ts = header.headers['X-Server-TS'] if(header.headers.has_key('X-Server-TS') != None) else long(time.time())
            m_to = data['to'] if(data['to'] != None) else None
            m_from = data['from'] if(data['from'] != None) else None
            m_content_type = header.headers['Content-Type'] if(header.headers['Content-Type'] != None) else None
            m_topic = method.routing_key
            
            print "TRYING TO LOG ", m_ts, " to ", m_to, " from ", m_from, " content_type ", m_content_type, " topic ", m_topic, " Body ", body
            
            if(method.routing_key == 'service.chat_logs'):
                self.process_command(method, header, data)
            else:
                LoggerService.db.log_chat(m_ts, m_to, m_from, m_content_type, m_topic, body)
        #except Exception as e:
        #    print "EXCEPTION ", e

        print "GOT DATA ", data
        
	def process_comand(self, method, header, data):
		print "PROCESSING REQUEST ", data
        

        
all_rooms = rm.find_room('room.#')
all_rooms.add_member(LoggerService())

cmd_room = rm.find_room('service.chat_logs')
cmd_room.add_member(LoggerService())

rm.start()