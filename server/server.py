#######################################################################
# File:             server.py
# Author:           Jose Ortiz
# Purpose:          CSC645 Assigment #1 TCP socket programming
# Description:      Template server class. You are free to modify this
#                   file to meet your own needs. Additionally, you are
#                   free to drop this client class, and add yours instead.
# Running:          Python 2: python server.py
#                   Python 3: python3 server.py
#                   Note: Must run the server before the client.
########################################################################

from builtins import object
import socket
from threading import Thread
import pickle
from client_handler import ClientHandler


class Server(object):

    MAX_NUM_CONN = 10

    def __init__(self, ip_address='127.0.0.1', port=12005):
        """
        Class constructor
        :param ip_address:
        :param port:
        """

        # create an INET, STREAMing socket
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}  # dictionary of clients handlers objects handling clients. format {clientid:client_handler_object}
        self.host = ip_address
        self.port = port
        self.serversocket.bind((ip_address, port))        
        self.chat_room = {} # list of chat room where { room_id: [recipient list]}
        self.threadStarted = {}  # keeping track of thread started, use for debugging only

    def _listen(self):
        """
        Private method that puts the server in listening mode
        If successful, prints the string "Listening at <ip>/<port>"
        i.e "Listening at 127.0.0.1/10000"
        :return: VOID
        """
        try:
            self.serversocket.listen(self.MAX_NUM_CONN)
            print('Server listening at ' +
                  str(self.host) + '/'+str(self.port))
        except socket.error as ex:
            print('Server FAILED to listen')
            print(ex)
            self.serversocket.close()

    def _accept_clients(self):
        """
        Accept new clients
        :return: VOID
        """
        while True:
            try:
                # accepting client
                client_handler, addr = self.serversocket.accept()
                # starting client thread
                self.threadStarted[addr[1]] = Thread(target=self.client_handler_thread,
                                                     args=(client_handler, addr, self.port))
                self.threadStarted[addr[1]].start()
            except socket.error as ex:
                # handle socket exceptions
                print("Server cannot accept client: Socket error")
                print(ex)
                self.serversocket.close()
            except Exception as ex:
                # handle general exception
                print("Server cannot accept client: Thread error")
                print(ex)
                self.serversocket.close()

    def client_handler_thread(self, clientsocket, addr, port):
        """
        Sends the client id assigned to this clientsocket and
        Creates a new ClientHandler object
        See also ClientHandler Class
        :param clientsocket:
        :param address:
        :return: a client handler object.
        """        
        client_handler = ClientHandler(self, clientsocket, addr, port)
        return client_handler

    def send_client_id(self, clientsocket, id):
        """
        Send client id to client
        :param clientsocket:
        :return:
        """
        clientid = {'clientid': id}
        self.send(clientsocket, clientid)

    def send(self, clientsocket, data):
        """
        TODO: Serializes the data with pickle, and sends using the accepted client socket.
        :param clientsocket:
        :param data:
        :return:
        """
        try:
            serialized_data = pickle.dumps(data)
            data_len = pickle.dumps(len(serialized_data))
            #print(data)
            #print(f'****************** length = %d ******************' %
            #      len(serialized_data))
            clientsocket.send(data_len)
            clientsocket.recv(1000)
            clientsocket.send(serialized_data)
        except Exception as ex:
            print(ex)

    def receive(self, clientsocket, MAX_BUFFER_SIZE=4096):
        """
        TODO: Deserializes the data with pickle
        :param clientsocket:
        :param MAX_BUFFER_SIZE:
        :return: the deserialized data
        """
        try:
            data = clientsocket.recv(MAX_BUFFER_SIZE)
            # print(pickle.loads(data))
            return pickle.loads(data)
        except:
            pass

    def run(self):
        """
        Already implemented for you. Runs this client
        :return: VOID
        """
        self._listen()
        self._accept_clients()


if __name__ == '__main__':
    server = Server()
    server.run()
