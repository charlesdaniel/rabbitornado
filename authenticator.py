db = {
    'charles': { 'name': 'charles', 'password': 'foobar'},
}

def memory_authenticate(name, password):
    if(db.has_key(name) and (db[name]['password'] == password)):
        return db[name]
    return None

def full_public(name,password):
    return dict(name=name, password=password)

db_conn=None
def db_connect():
    import MySQLdb
    global db_conn
    try:
        if(db_conn == None):
            db_conn = MySQLdb.connect('localhost', 'rabbitornado', 'rabbitornado', 'rabbitornado')
    except MySQLdb.Error, e:
        print "MySQLdb.Error %d: %s" % (e.args[0], e.args[1])
        
    return db_conn

def db_authenticate(name, password):
    import MySQLdb
    user = None
    try:
        conn = db_connect()
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("select id, name, password from users where name=%s and password=%s", (name, password))
        user = cur.fetchone()
        cur.close()
        print "USER DB ", user

    except MySQLdb.Error, e:
        print "MySQLdb.Error %d: %s" % (e.args[0], e.args[1])

    return user

authenticate=full_public
