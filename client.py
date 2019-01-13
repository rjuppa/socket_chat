#!/usr/bin/env python3

import socket
import sys
import select

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 2323))
user_name = ""

print("Chat client started.")
print("====================")
while True:
    if sock._closed:
        break

    r, w, x = select.select([sys.stdin, sock], [], [])
    if not r:
        continue

    if r[0] is sys.stdin:
        message = input()
        if not message:
            continue

        if message == "quit":
            sock.close()
            break

        sock.send(message.encode('utf-8'))

    else:
        data = sock.recv(1024)
        if not data:
            sock.close()
            continue

        msg = data.decode('utf-8')
        if msg == "logout":
            sock.close()
            continue

        if msg[:9] == "USERNAME:":
            user_name = msg[9:]
            print("system> Welcome {}".format(user_name))

        else:
            backspace = "\x08" * (len(user_name) + 2)
            if msg[0] == "@":
                # another client
                print("{}{}".format(backspace, msg[1:]))

            if msg[0] == ">":
                # server '\x08'

                print("{}system>{}".format(backspace, msg[1:]))

        if user_name:
            sys.stdout.write("{}> ".format(user_name))
            sys.stdout.flush()
