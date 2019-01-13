#!/usr/bin/env python3

from queue import Queue, Empty
import select, socket


class User(object):

    def __init__(self, sock):
        addr, port = s.getpeername()
        self.addr = addr
        self.port = port
        self.sock = sock
        self.name = None
        self.auth = False

    def login(self, name):
        name = name.replace("@", "")
        self.name = "@{}".format(name)
        self.auth = True


def add_user(user):
    users[user.port] = user


def rem_user(user):
    del users[user.port]


def get_user(sock):
    addr, port = s.getpeername()
    if port in users:
        return users[port]
    user = User(sock)
    users[port] = user
    return user


def get_user_by_name(name):
    for k, u in users.items():
        if u.name == name:
            return u


def list_peers():
    arr = []
    for k, u in users.items():
        arr.append(u.name)
    return "> {}".format(", ".join(arr))


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)
server.bind(('127.0.0.1', 2323))
server.listen(5)
inputs = [server]
outputs = []
message_queues = {}
users = {}


def bradcast(message, excep=None):
    data = message.encode('utf-8')
    for k, u in users.items():
        if excep and u.name == excep.name:
            continue

        sock = u.sock
        if sock not in message_queues:
            message_queues[sock] = Queue()

        message_queues[sock].put(data)
        if sock not in outputs:
            outputs.append(sock)


def process_msg(sock, data):
    line = data.decode('utf-8')
    arr = line.split(" ")
    if len(arr) > 1:
        arg1, arg2 = arr[0], " ".join(arr[1:])
    else:
        arg1, arg2 = arr[0], ""

    user = get_user(sock)
    if arg1.lower() == "login":
        if arg2:
            if user.auth:
                data = "> Already logged in ({}).".format(arg2).encode('utf-8')
                message_queues[sock].put(data)
            else:
                user.login(arg2)
                bradcast("> {} has entered.".format(arg2), excep=user)
                data = "USERNAME:{}".format(user.name[1:]).encode('utf-8')   # LOGOUT_SIGNAL
                message_queues[sock].put(data)
        else:
            data = "> What is your name?".encode('utf-8')
            message_queues[sock].put(data)

    elif arg1.lower() == "help":
        msg = "> use commands: \n"
        msg += "  login [nick] \n  logout \n  @nick text...  \n  who \n  me \n  quit\n\n"
        data = msg.encode('utf-8')
        message_queues[sock].put(data)

    elif not user.auth:
        data = "> You are not authenticated.".encode('utf-8')
        message_queues[sock].put(data)

    elif arg1.lower() == "logout" or arg1.lower() == "exit":
        name = user.name
        rem_user(user)
        bradcast("{} has left.".format(name))
        data = "logout".encode('utf-8')   # LOGOUT_SIGNAL
        message_queues[sock].put(data)

    elif arg1.lower() == "who":
        data = list_peers().encode('utf-8')
        message_queues[sock].put(data)

    elif arg1.lower() == "me":
        data = "> {}".format(user.name).encode('utf-8')
        message_queues[sock].put(data)

    elif arg1[0] == "@":
        to = get_user_by_name(arg1)
        if not to:
            data = "> Sorry I dont know {}".format(arg1).encode('utf-8')
            message_queues[sock].put(data)
        else:
            user = get_user(sock)
            sock = to.sock
            msg = "{}> {}".format(user.name, arg2)
            data = msg.encode('utf-8')
            message_queues[sock].put(data)

    elif arg1.lower() == "exit":
        data = "> Bye bye".encode('utf-8')
        message_queues[sock].put(data)

    else:
        data = "> Message lost! - use @nick text..".encode('utf-8')
        message_queues[sock].put(data)

    # send reply
    if sock not in outputs:
        outputs.append(sock)


print("Chat server started.")
print("====================")
while inputs:
    r, w, x = select.select(inputs, outputs, inputs)
    for s in r:
        if s is server:
            # new client connection
            connection, client_address = s.accept()
            connection.setblocking(0)
            inputs.append(connection)
            message_queues[connection] = Queue()
            print("A new client connection registered {}.".format(client_address))
        else:
            data = s.recv(1024)
            if data:
                # message from client
                print("Received message from : {}, length: {}b.  content: '{}'".format(
                    s.getpeername(), len(data), data.decode('utf-8')))

                # process msg
                process_msg(s, data)

            else:
                # quit client
                print("A client connection quit  {}.".format(s.getpeername()))
                if s in outputs:
                    outputs.remove(s)
                inputs.remove(s)
                s.close()
                del message_queues[s]

    for s in w:
        # send reply
        try:
            next_msg = message_queues[s].get_nowait()
            print("Sent message to: {}    content: '{}'".format(
                s.getpeername(), next_msg.decode('utf-8')))
        except Empty:
            outputs.remove(s)
        else:
            s.send(next_msg)

    for s in x:
        # exceptions
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()
        del message_queues[s]
