import signal
import socket
# import threading
import select
import time
import sys
import re

BUFFER_SIZE = 4096
DELAY = 0.0001
# DEFAULT_FORWARD = ('0.0.0.0', 8000)

class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception, e:
            print e
            return False

class Server:
    input_list = []
    channel = {}

    def __init__(self, host, port, forward_host, forward_port):
        self.__clients = {}
        self.server = None
        self.stop = False
        self.forward_to = (forward_host, forward_port) 

        # signal.signal(signal.SIGINT, self.shutdown)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)

    def shutdown(self):
        self.stop = True
    
    def main_loop(self):
        self.input_list.append(self.server)

        while not self.stop:
            time.sleep(DELAY)
            ss = select.select
            inputready, outputready, exceptready = ss(self.input_list, [], [])
            for self.s in inputready:
                if self.s == self.server:
                    self.on_accept()
                    break
                
                self.data = self.s.recv(BUFFER_SIZE)
                if len(self.data) == 0:
                    self.on_close()
                    break
                else:
                    self.on_recv()
    
    def on_accept(self):
        forward = Forward().start(self.forward_to[0], self.forward_to[1])
        clientsock, clientaddr = self.server.accept()
        if forward:
            print clientaddr, "has connected"
            self.input_list.append(clientsock)
            self.input_list.append(forward)
            self.channel[clientsock] = forward
            self.channel[forward] = clientsock
        else:
            print "Can't establish connection with remote server.",
            print "Closing connection with client side", clientaddr
            clientsock.close()
    
    def on_close(self):
        print self.s.getpeername(), "has disconnected"
        #remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[self.s]

    def on_recv(self):
        data = self.data
        # here we can parse and/or modify the data before send forward
        # print data
        regex = "(?:GET|POST|PUT|OPTIONS|DELETE) (.+) HTTP/1.1.*"
        url = ""
        m = re.match(regex, data)
        if m:
            url = m.groups(1)
            print url[0]
        self.channel[self.s].send(data)



def main(args):
    if len(args) < 3:
        print 'Usage: <host> <port> <remote_host> <remote_port>'
        print 'Example : localhost 8080 localhost 8081'
        return

    server = Server(args[1], int(args[2]), args[3], int(args[4]))
    print "Server init complete. Server starting..."
    server.main_loop()

if __name__ == "__main__":
    main(sys.argv)

    