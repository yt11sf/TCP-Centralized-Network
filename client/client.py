#######################################################################
# File:             client.py
# Author:           Jose Ortiz
# Purpose:          CSC645 Assigment #1 TCP socket programming
# Description:      Template client class. You are free to modify this
#                   file to meet your own needs. Additionally, you are
#                   free to drop this client class, and add yours instead.
# Running:          Python 2: python client.py
#                   Python 3: python3 client.py
#
########################################################################

import socket
import pickle
import time
from custom_exception import ClientClosedException, ServerResponseException, ThreadClosedException


class Client(object):
    """
    The client class provides the following functionality:
    1. Connects to a TCP server 
    2. Send serialized data to the server by requests
    3. Retrieves and deserialize data from a TCP server
    """

    def __init__(self, id_key):
        """
        Class constractpr
        """
        # Creates the client socket
        # AF_INET refers to the address family ipv4.
        # The SOCK_STREAM means connection oriented TCP protocol.
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientid = 0
        self.id_key = id_key
        self.res_thread = None
        self.cache_table = []
        self.cache_path = 'Projects\TCP-Client-Server-Centralized-Network\client\cache\\'

    def set_info(self):
        data = self.receive()
        print(data)
        self.client_id = data['clientid']  # sets the client id to this client
        self.send({'id_key': self.id_key})
        print('Your client info is:')
        print('Client Name: ' + str(self.id_key))
        print("Client ID: " + str(self.client_id))

    def connect(self, host="127.0.0.1", port=12005):
        """
        TODO: Connects to a server. Implements exception handler if connection is resetted. 
            Then retrieves the cliend id assigned from server, and sets
        :param host: 
        :param port: 
        :return: VOID
        """
        try:
            self.clientSocket.connect((host, port))
            print(f'Successfully connected to server: %s/%d' % (host, port))
            self.set_info()
            # client is put in listening mode to retrieve data from server.
            while True:
                try:
                    # with self.lock:
                    #    print('waiting for server')
                    data = self.receive()
                    if not data:  # if wanna break by server command, put continue?
                        break
                    # with self.lock:
                    #    print(data)
                    response = self.handle_response(data)
                    # if there is a response
                    if response:
                        self.send(response)
                #except ThreadClosedException as ex:
                #    with self.lock:
                #        print(
                #            '\n-----------------------Thread Closed-----------------------\n')
                except ClientClosedException as ex:
                #    with self.lock:
                    print('\n--------------------Client Disconnected---------------------\n')
                    break
                except ServerResponseException as ex:
                #    with self.lock:
                    print('Server Response Invalid')
                except:
                    raise

        except socket.error as ex:
            print('Client cannot connect')
            print(ex)
        except Exception as ex:
            print('General Exception')
            print(ex)
        self.close()

    def handle_response(self, data):
        """
        This function handle the client's action according to the protocols send by the server
        :param: deserialized server response
        :return: raw client response
        """
        # with self.lock:
        #    print(data)
        response = {}
        # going through all the data
        for header in data['headers']:
            # if printing message
            if header['type'] == 'print':
                self.print_message(header['body'])
            # if getting input
            elif header['type'] == 'input':
                response[header['body']['res-key']
                         ] = self.get_input(header['body'])
                ####### Deprecated Synchronous Messaging #######
                '''
                    # if opening/joining chat
                    elif header['type'] == 'open-chat':
                        self.open_thread(header['body'],  self.response_thread)
                    # if closing a chat
                    elif header['type'] == 'close-chat':
                        self.close_thread()
                        raise ThreadClosedException()
                '''
            # return status
            elif header['type'] == 'ignore':
                response = 'ignore'
            # if closing connection
            elif header['type'] == 'close':
                response['client-closed'] = True
                self.send(response)
                raise ClientClosedException()
            # checking cache
            elif header['type'] == 'check-cache':
                response = self.check_cache(header['body'])
            else:
            #    with self.lock:
                print(header)
                raise ServerResponseException()
        if response:
            if response != 'ignore':
                return response
        else:
            return {'status': 'ok'}

    def print_message(self, body):
        """
        This function simply print the message from the server
        :param: protocol's body
        """
        message = body['message']
        if 'cacheable' in body and body['cacheable'] == True:
            self.caching(body)
        #with self.lock:
        print(message)

    def get_input(self, body):
        """
        This function get the client response according to the server protocols
        :param: protocol's body
        :return: client response body
        """
        while True:
            try:
                message = body['message']
                data_type = body['res-type']
                data = input(message)
                if data_type == 'string':
                    data = str(data)
                elif data_type == 'int':
                    data = int(data)
                break
            except:
                #with self.lock:
                print('\n--->Client Input Invalid<---\n')
        if data == -10:
            #print('listen: ' + str(self.thread['listen'].is_alive()))
            print('response: ' + str(self.res_thread.is_alive()))
        return data

    ####### Deprecated Synchronous Messaging #######
    '''
    def open_thread(self, body, th):
        """
        This function handle the chat functionality by spawning 2 threads.
        1 for listening to the server, 1 for sending data to server.
        :param: deserialized server response
        :return: void
        """
        try:
            self.res_thread = threading.Thread(target=th)
            self.res_thread.start()
            self.close_chat_key = body['close-key']
        except Exception as ex:
            with self.lock:
                print('open_thread error')
                print(ex)

    def response_thread(self):
        """
        This function response to the server when client input data        
        """
        #print('response thread is started')
        while self.res_thread.is_alive():
            try:
                message = input()
                data = {'message': message}
                if data['message'] != '':
                    self.send(data)
                # detected close chat keyword, blocking input
                if message == self.close_chat_key:
                    raise ThreadClosedException()
            except ThreadClosedException as ex:
                break
            except socket.error as ex:
                break
            except Exception as ex:
                with self.lock:
                    print('response_chat exception')
                    print(ex)

    def close_thread(self):
        """
        This function close threads when client exit chat
        """
        # with self.lock:
        #    print('\n--------------Closing chat--------------')
        self.close_chat_key = ''
        data = {'chat-closed': True}
        self.send(data)
    '''

    def send(self, data):
        """
        TODO: Serializes and then sends data to server
        :param data:
        :return:
        """
        # print('send: ' + str(data))
        s_data = pickle.dumps(data)
        self.clientSocket.send(s_data)

    def receive(self, MAX_BUFFER_SIZE=4090):
        """
        TODO: Desearializes the data received by the server
        :param MAX_BUFFER_SIZE: Max allowed allocated memory for this data
        :return: the deserialized data.
        """
        data_len = pickle.loads(self.clientSocket.recv(MAX_BUFFER_SIZE))
        self.clientSocket.send(pickle.dumps({'status': 'ok'}))
        buff = b''
        curr_len = 0
        while curr_len < data_len:
            data = self.clientSocket.recv(MAX_BUFFER_SIZE)
            if not data:
                break
            buff += data
            curr_len += len(data)
        # print('receive: ' + str(pickle.loads(buff)))
        # return deserializes data from server
        return pickle.loads(buff)

    def close(self):
        """
        TODO: close the client socket
        :return: VOID
        """
        self.clientSocket.close()

    """----------------------- Proxy Server -----------------------"""

    def check_cache(self, body):
        """
        Check if cache exists, 
        use cache if exists, else tell server to fetch request
        :param: server response body
        "return" dictionary to response to server
        """
        try:
            for c in self.cache_table:
                # if cache exists in cache_table
                if body['domain'] == c['domain']:
                    # open cache and print it
                    with open(self.cache_path + c['identifier'], 'rb') as cachefile:
                        data = pickle.load(cachefile)
                        
                        print('Success 200 OK (cache)')
                        # print(data)
                    return {'cached': True}
        except Exception as ex:
            print('check_cache failed')
            print(ex)
        return {'cached': False}

    def caching(self, body):
        try:
            t = time.strftime('%Y-%m-%d %H:%M', time.localtime())
            identifier = f'%d-%d.pickle' % (hash(body['domain']), hash(t))
            self.cache_table.append({
                'domain':  body['domain'],
                'last-modified': t,
                'identifier': identifier
            })
            #print(self.cache_table)
            with open(self.cache_path + identifier, 'wb') as cachefile:
                pickle.dump(body['message'], cachefile)
        except Exception as ex:
            print('caching failed')
            print(ex)

if __name__ == '__main__':
    host = input('Enter the server IP Address: ') or "127.0.0.1"
    port = input('Enter the server port: ') or 12005
    id_key = input('Your id key (i.e your name): ')
    client = Client(id_key)
    client.connect(host, int(port))
