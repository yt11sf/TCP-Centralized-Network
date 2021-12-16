#######################################################################
# File:             client_handler.py
# Author:           Jose Ortiz
# Purpose:          CSC645 Assigment #1 TCP socket programming
# Description:      Template ClientHandler class. You are free to modify this
#                   file to meet your own needs. Additionally, you are
#                   free to drop this client handler class, and use a version of yours instead.
# Running:          Python 2: python server.py
#                   Python 3: python3 server.py
#                   Note: Must run the server before the client.
########################################################################

import pickle
import socket
import textwrap
import time
import threading
from menu import Menu
from custom_exception import OptionSelectedIsInvalidError, ClientDisconnected


class ClientHandler(object):
    """
    The ClientHandler class provides methods to meet the functionality and services provided
    by a server. Examples of this are sending the menu options to the client when it connects,
    or processing the data sent by a specific client to the server.
    """

    def __init__(self, server_instance, clientsocket, addr, port):
        """
        Class constructor already implemented for you
        :param server_instance: normally passed as self from server object
        :param clientsocket: the socket representing the client accepted in server side
        :param addr: addr[0] = <server ip address> and addr[1] = <client id>
        """
        self.server_ip = addr[0]
        self.client_id = addr[1]
        self.client_id_key = ''
        self.port = port
        self.server = server_instance
        self.clientsocket = clientsocket
        self.lock = threading.Lock()
        self.unread_messages = []
        self.chat_messages = []
        # for web proxy
        self.cache = False
        self.auth = False
        self.private = True
        self.max_buffer = 4096
        # record client_handler object in server
        with self.lock:
            self.server.clients[self.client_id] = self
        # setting client info
        self.set_client_info()     
        # sending menu to client
        self.menu = Menu()
        self._sendMenu()

    def _sendMenu(self):
        """
        sends the menu options to the client after the handshake between client and server is done.
        :return: VOID
        """
        # send menu to client
        self._send(self.menu.get_menu())
        # process client response
        self.process_options()

    def process_options(self):
        """
        Process the option selected by the user and the data sent by the client related to that
        option. Note that validation of the option selected must be done in client and server.
        In this method, I already implemented the server validation of the option selected.
        :return:
        """
        try:
            data = self._receive()
            if not data:
                raise Exception()
            # validates a valid option selected
            if 'option_selected' in data.keys() and 1 <= data['option_selected'] <= 7:
                # with self.lock:
                #    print('process_option: ' + str(data))
                option = data['option_selected']
                # Get user list
                if option == 1:
                    self._send_user_list()
                # Send message
                elif option == 2:
                    self._send_messages()
                # Get message
                elif option == 3:
                    self._get_messages()
                # Create new chat room
                elif option == 4:
                    self._create_chat()
                # Join an existing chat room
                elif option == 5:
                    self._join_chat()
                # Turn web proxy server on
                elif option == 6:
                    with self.lock:
                        print(f'Client %s %d is opening proxy server' %
                              (self.client_id_key, self.client_id))
                    self._sendProxyMenu()
                # Disconnect from server
                elif option == 7:
                    #    with self.lock:
                    #        print(f'Client %d requesting to close connection' %
                    #              self.client_id)
                    raise ClientDisconnected()
                # temporary option to debugs
                elif option == 8:
                    self.check_living_thread()
                elif option == 9:
                    self.check_recipient_in_room()
                if option not in [7]:
                    # options are handled, sending menu
                    self._post_process()
            else:
                raise OptionSelectedIsInvalidError()
        # if option is invalid, prompt user to enter option again
        except OptionSelectedIsInvalidError:
            with self.lock:
                print(
                    f'client_handler The option selected by client %d is out of range' % self.client_id)
            self._send(self.menu.print_message(
                f'client_handler The option selected by client %d is out of range\n' % self.client_id))
            self._receive()
            self._post_process()
        # other exception
        # stop thread
        except ClientDisconnected:
            try:
                self._disconnect_from_server()
            except:
                pass
            with self.lock:
                print(f'Client %s %d disconnected' % (self.client_id_key, self.client_id))
        except TypeError as ex:
            if str(ex) != 'TypeError: \'NoneType\' object is not subscriptable':
                with self.lock:
                    print('process_option Type Error')
                self.server.send(self.clientsocket,
                                 self.menu.send_error_message('process_option', ex))
                self._receive()
                try:
                    self._disconnect_from_server()
                except:
                    pass
        except socket.error as ex:
            with self.lock:
                print(f'Client %d has forcibly closed connection in process_options' %
                      self.client_id)
                print(ex)
            self._disconnect_from_server()
        except Exception as ex:
            if str(ex) != '__enter__':
                with self.lock:
                    print(f'Client %d:  process_option error' % self.client_id)
                    print(ex)
                try:
                    self.server.send(
                        self.clientsocket, self.menu.send_error_message('process_option', ex))
                    self._receive()
                except:
                    pass
            try:
                self._disconnect_from_server()
            except:
                pass

    def _post_process(self):
        '''
        This function ask if user want to continue with main menu
        :return: void
        '''
        self.server.send(self.clientsocket,
                         self.menu.prompt_input('Do you want to continue with the main menu (y/n)? '))
        data = self._receive()
        try:
            if data['message'] == 'y':
                self._sendMenu()
            elif data['message'] == 'n':
                raise ClientDisconnected()
            else:
                self.server.send(self.clientsocket,
                                 self.menu.print_message(f'Option selected is out of range\n'))
                self._receive()
                self._post_process()
        except:
            raise ClientDisconnected()

    def _send_user_list(self):
        """
        TODO: send the list of users (clients ids) that are connected to this server.
        :return: VOID
        """
        formatted_list = []
        # getting all clients in server
        for client in self.server.clients.values():
            formatted_list.append(f"%s:%d" % (
                client.client_id_key, client.client_id))
        # Formatting user list.
        # Users in server: Jose:2345, Nina:8763, Alice:1234, John:4566
        output = "Users in server: "
        for a in formatted_list:
            if a != formatted_list[-1]:
                output += f'%s, ' % a
            else:
                output += f'%s\n' % a
        data = self.menu.print_message(output)
        self._send(data)
        self._receive()
        with self.lock:
            print(f'List of users send to client %s %d' %
                  (self.client_id_key, self.client_id))

    def _send_messages(self):
        """
        This function prompt the client to input for data required to
        send message to recipient
        :return: void
        """
        # prompt user to input message
        self._send(self.menu.prompt_send_message())
        data = self._receive()
        with self.lock:
            print(f'Message from %s %d to %s: %s' %
                  (self.client_id_key, self.client_id, data['recipient_id'], data['message']))
        # saving message to recipient client handler
        response = self._save_message(data['recipient_id'], data['message'])
        # acknowledge message is send
        self._send(response)
        self._receive()

    def _save_message(self, recipient_id, message):
        """
        TODO: link and save the message received to the correct recipient. handle the error if recipient was not found
        :param recipient_id:
        :param message:
        :return: response dict
        """
        try:
            # if recipient found
            if recipient_id in self.server.clients:
                # format message
                t = time.strftime('%Y-%m-%d %H:%M', time.localtime())
                message = f"%s :  %s (from %s)" % (
                    t, message, self.client_id_key)
                # store message in recipient client handler
                recipient = self.server.clients[recipient_id]
                with recipient.lock:
                    recipient.unread_messages.append(message)
                    self.server.clients[recipient_id] = recipient
                # acknowledge message is send
                data = self.menu.print_message('Message sent!\n')
            # if no recipient found
            else:
                data = self.menu.print_message('Recipient Not Found\n')
        except Exception as ex:
            with self.lock:
                print('_save_message error')
                print(ex)
            data = self.menu.send_error_message('_save_message error', ex)
        return data

    def _get_messages(self):
        """
        TODO: send all the unreaded messages of this client. if non unread messages found, send an empty list.
        TODO: make sure to delete the messages from list once the client acknowledges that they were read.
        :return: VOID
        """
        try:
            # if client has unread message
            if self.unread_messages:
                # format the message
                message = "My messages:\n"
                for m in self.unread_messages:
                    message += m + "\n"
                # clear unread message
                self.unread_messages.clear()
            # if client has no unread message
            else:
                message = 'You did not receive any message :(\n'
            data = self.menu.print_message(message)
        except Exception as ex:
            with self.lock:
                print('_send_message error')
                print(ex)
            data = self.menu.send_error_message('_send_message error', ex)
        self._send(data)
        self._receive()
        with self.lock:
            print(f'List of messages send to %s %d' %
                  (self.client_id_key, self.client_id))

    def _create_chat(self):
        """
        Creates a new chat room and join as host
        :return: void
        """
        # prompt client to enter room id
        self._send(self.menu.prompt_input(
            message='Enter new chat room id: ', res_type='int', res_key='room_id'))
        data = self._receive()
        room_id = data['room_id']

        # if room_id already exists, tell client and return
        if room_id in self.server.chat_room:
            self._send(self.menu.print_message(
                f'room id %d has been used\n' % room_id))
            self._receive()
        # if room_id does not exists
        else:
            try:
                # record the chat room in server
                with self.lock:
                    self.server.chat_room[room_id] = [self.client_id]

                # tell client chat is opened
                message = textwrap.dedent(f"""
                ----------------------- Chat Room %d ------------------------ 

                Type 'exit' to close the chat room.
                Chat room created by: %s
                Waiting for other users to join....
                """ % (room_id, self.client_id_key))
                self.server.send(self.clientsocket,
                                 self.menu.print_message(message))
                data = self._receive()
                with self.lock:
                    print(f'Client %s %d is joining chat room %d' %
                          (self.client_id_key, self.client_id, room_id))
                self._retrieve_chat(room_id, 'exit')
            except TypeError:
                pass
            except socket.error:
                raise socket.error
            except Exception as ex:
                with self.lock:
                    print(f'Client %d:  _create_chat error' % self.client_id)
                    print(ex)
                self.server.send(
                    self.clientsocket, self.menu.send_error_message('_create_chat', ex))
                self._receive()

    def _join_chat(self):
        '''
        Joining a chat as a guest
        :return: void
        '''
        # prompt client to enter room id
        self._send(self.menu.prompt_input(
            message='Enter chat room id to join: ', res_type='int', res_key='room_id'))
        data = self._receive()
        room_id = data['room_id']

        # if room_id does not exists, tell client and return
        if room_id not in self.server.chat_room:
            self._send(self.menu.print_message(
                f'room id %d does not exists\n' % room_id))
            self._receive()
        # if room_id does exists
        else:
            try:
                with self.lock:
                    # join the chat room
                    self.server.chat_room[room_id].append(self.client_id)

                # tell client chat is opened
                message = textwrap.dedent(f"""
                ----------------------- Chat Room %d ------------------------
                Joined to chat room %d
                Type 'bye' to exit this chat room.
                """ % (room_id, room_id))
                self.server.send(self.clientsocket,
                                 self.menu.print_message(message))
                self._receive()
                with self.lock:
                    print(f'Client %s %d is joining chat room %d' %
                          (self.client_id_key, self.client_id, room_id))

                # tell every recipient in the chat room that client joined the chat
                for recipient_id in self.server.chat_room[room_id]:
                    # do not send to self
                    if recipient_id != self.client_id:
                        # get the recipient socket
                        recipient_socket = self.server.clients[recipient_id]
                        '''
                        with self.lock:
                            print(f'guest %s %d is telling recipient %d about joining' % (
                                self.client_id_key, self.client_id, recipient_id))
                        '''
                        # send to the recipient
                        self.server.send(recipient_socket.clientsocket,
                                         self.menu.print_message(f"%s joined." % self.client_id_key))
                        self.server.receive(recipient_socket.clientsocket)

                # with self.lock:
                #    print(f'client %s %d is joining chat' % (self.client_id_key, self.client_id))
                self._send(self.menu.prompt_input(
                    self.client_id_key + '> '))
                data = self._receive()
                self._send_chat(room_id, f'%s> %s' %
                                (self.client_id_key, data['message']))
                self._retrieve_chat(room_id, 'bye')
            except TypeError:
                pass
            except socket.error:
                raise socket.error
            except Exception as ex:
                with self.lock:
                    print(f'Client %d:  _join_chat error' % self.client_id)
                    print(ex)
                self.server.send(
                    self.clientsocket, self.menu.send_error_message('_join_chat', ex))
                self._receive()

    def _retrieve_chat(self, room_id, exit_key):
        '''
        Send chat message to client if any.
        Then request input.
        :return: void
        '''
        try:
            e_k = f'%d bye bye' % self.client_id
            while True:
                if len(self.chat_messages) != 0:
                    # send formatted chat_messages to client
                    self._send(self.menu.print_message(
                        '\n'.join(self.chat_messages)))
                    self._receive()

                    if e_k in self.chat_messages:
                        with self.lock:
                            print(f'Client %s %d leaving chat room %d' % (
                                self.client_id_key, self.client_id, room_id))
                        self.chat_messages.clear()
                        break
                    # clearing chat messages
                    self.chat_messages.clear()

                    # prompt chat to enter input
                    self._send(self.menu.prompt_input(
                        self.client_id_key + "> "))
                    data = self._receive()

                    # if client exiting chat room
                    if data['message'] == exit_key:
                        # client is a host
                        if data['message'] == 'exit':
                            with self.lock:
                                print(f'Host %s %d is closing chat' %
                                      (self.client_id_key, self.client_id))
                            for recipient_id in self.server.chat_room[room_id]:
                                # do not send to self
                                if recipient_id != self.client_id:
                                    # get the recipient handler
                                    recipient_handler = self.server.clients[recipient_id]
                                    #with self.lock:
                                    #    print(f'%d bye bye' % recipient_id)
                                    with recipient_handler.lock:
                                        # send to the recipient
                                        recipient_handler.chat_messages.append(
                                            f'%d bye bye' % recipient_id)
                                    with self.lock:
                                        print(f'%s' % '\n'.join(
                                            recipient_handler.chat_messages))
                            self.server.chat_room.pop(room_id)
                        # client is a guest
                        elif data['message'] == 'bye':
                            self.server.chat_room[room_id].remove(
                                self.client_id)
                            self._send_chat(
                                room_id, f'%s disconnected from the chat.' % self.client_id_key)
                        break

                    # send message to every recipient in chat room
                    self._send_chat(room_id, f'%s> %s' %
                                    (self.client_id_key, data['message']))
                time.sleep(.7)
        except:
            pass

    def _send_chat(self, room_id, message):
        '''
        Sending the message to all recipient in chat room except self
        '''
        for recipient_id in self.server.chat_room[room_id]:
            # do not send to self
            if recipient_id != self.client_id:
                # get the recipient handler
                recipient_handler = self.server.clients[recipient_id]
                with recipient_handler.lock:
                    # send to the recipient
                    recipient_handler.chat_messages.append(message)

    ####### Deprecated Synchronous Messaging #######
    '''
    def _create_chat(self):
        """
        Creates a new chat in this server where two or more users can share messages in real time.
        """
        # prompt client to enter room id
        self._send(self.menu.prompt_input(
            message='Enter new chat room id: ', res_type='int', res_key='room_id'))
        data = self._receive()
        room_id = data['room_id']

        # if room_id already exists, tell client and return
        if room_id in self.server.chat_room:
            self._send(self.menu.print_message(
                f'room id %d has been used\n' % room_id))
            self._receive()
        # if room_id does not exists
        else:
            try:
                # record the chat room in server
                with self.lock:                    
                    self.server.chat_room[room_id] = [self.client_id]                

                # telling client to handle chat
                self.server.send(self.clientsocket,
                                 self.menu.open_chat('exit'))
                self._receive()

                # listening to client chat response
                message = textwrap.dedent(f"""
                ----------------------- Chat Room %d ------------------------ 

                Type 'exit' to close the chat room.
                Chat room created by: %s
                Waiting for other users to join....
                """ % (room_id, self.client_id_key))
                self._listen_chat_client(room_id, message, 'exit')

            except socket.error as ex:
                with self.lock:
                    print(
                        f'Client %d has forcibly closed connection in _create_chat' % self.client_id)
                raise socket.error()
            except Exception as ex:
                with self.lock:
                    print(f'Client %d:  _create_chat error' % self.client_id)
                    print(ex)
                self.server.send(
                    self.clientsocket, self.menu.send_error_message('_create_chat', ex))
                self._receive()

    def _join_chat(self):
        """
        join a chat in a existing room
        """
        # prompt client to enter room id
        self.server.send(self.clientsocket,
                         self.menu.prompt_input(message='Enter chat room id to join: ', res_type='int', res_key='room_id'))
        data = self._receive()
        room_id = data['room_id']

        # if room_id does not exists, tell client and return
        if room_id not in self.server.chat_room:
            self.server.send(self.clientsocket,
                             self.menu.print_message(f'room id %d does not exists\n' % room_id))                             
            self._receive()
        # if room_id does exists
        else:
            try:
                with self.lock:
                    # join the chat room
                    self.server.chat_room[room_id].append(self.client_id)
                # telling client to handle chat
                self._send(self.menu.open_chat('bye'))
                self._receive()

                
                # tell every recipient in the chat room that client joined the chat
                for recipient in self.server.chat_room[room_id]:
                    # do not send to self
                    if recipient != self.client_id:
                        # get the recipient socket
                        recipient_socket = self.server.clients[recipient]
                        # send to the recipient
                        self.server.send(recipient_socket.clientsocket,
                                         self.menu.print_message(self.client_id_key + " joined."))

                # listening to client chat response
                message = textwrap.dedent(f"""
                ----------------------- Chat Room %d ------------------------
                Joined to chat room %d
                Type 'bye' to exit this chat room.
                """ % (room_id, room_id))   
                self._listen_chat_client(room_id, message, 'bye')

            except socket.error as ex:
                with self.lock:
                    print(
                        f'Client %d has forcibly closed connection in _join_chat' % self.client_id)
                raise socket.error()
            except Exception as ex:
                with self.lock:
                    print(f'Client %d:  _join_chat error' % self.client_id)
                    print(ex)
                self.server.send(
                    self.clientsocket, self.menu.send_error_message('_join_chat', ex))
                self._receive()
   
    def _listen_chat_client(self, room_id, message, exit_key):
        """
        This function listen to the client when the client is in a chat room
        :param: room_id, message to client, key word to exit
        """
        print(f'Client %d listening to chat %d' %(self.client_id, room_id))
        # tell client server is ready
        self._send(self.menu.print_message(message))
        with self.lock:
            print(f'Client %d waiting for ack %d' %(self.client_id, room_id))
        data = self._receive()
        with self.lock:
            print(f'client %d is receiving status' % self.client_id)
            print(data)
        # simply listen to self.client
        # let other client_handler to access self.send
        while True:
            try:
                # getting the message from client
                data = self._receive()
                with self.lock:
                    print(f'client %d has data' % self.client_id)
                    print(data)

                if 'status' in data:
                    continue
                # if client's chat closed
                elif 'chat-closed' in data:
                    # with self.lock:
                    # print(f'Client %d disconnected from chat %d' %
                    #      (self.client_id, room_id))
                    break

                message = data['message']
                # if client want to exit chat
                if message == exit_key:
                    # if client is a host
                    if exit_key == 'exit':
                        # for every recipient in the chat room
                        for recipient in self.server.chat_room[room_id]:
                            # tell recipient client to close chat
                            recipient_socket = self.server.clients[recipient]
                            # send to the recipient
                            self.server.send(recipient_socket.clientsocket, self.menu.close_chat())
                            self.server.receive(recipient_socket.clientsocket)
                        with self.lock:
                            # remove chat room from record
                            del self.server.chat_room[room_id]

                    # if client is a guest
                    else:
                        with self.lock:
                            # remove self from chat room
                            self.server.chat_room[room_id].remove(
                                self.client_id)
                        # tell every recipient client left chat
                        for recipient in self.server.chat_room[room_id]:
                            # tell recipient client to close chat
                            recipient_socket = self.server.clients[recipient]
                            # send to the recipient
                            self.server.send(
                                recipient_socket.clientsocket,
                                self.menu.print_message(f'%s disconnected from the chat.' % self.client_id_key))
                            self.server.receive(recipient_socket.clientsocket)
                        # telling self to close chat
                        self.server.send(self.clientsocket,
                                         self.menu.close_chat())
                        self._receive()

                else:
                    # for every recipient in the chat room
                    for recipient in self.server.chat_room[room_id]:
                        # do not send to self
                        if recipient != self.client_id:
                            # get the recipient socket
                            recipient_socket = self.server.clients[recipient]
                            # send to the recipient
                            self.server.send(recipient_socket.clientsocket,
                                             self.menu.print_message(self.client_id_key + "> " + message))
                            self.server.receive(recipient_socket.clientsocket)
            except socket.error as ex:
                raise socket.error()         
            except Exception as ex:
                with self.lock:
                    print(f'Client %d:  _listen_chat error' % self.client_id)
                    print(ex)
                self.server.send(
                    self.clientsocket, self.menu.send_error_message('_listen_chat', ex))
                raise
    '''

    def delete_client_data(self):
        """
        delete all the data related to this client from the server.
        :return: VOID
        """
        try:
            with self.lock:
                #print(f'deleted client_id %d from clients[]' % self.client_id)
                del self.server.clients[self.client_id]
        except:
            pass
        return True

    def _disconnect_from_server(self):
        """
        TODO: call delete_client_data() method, and then, disconnect this client from the server.
        :return: VOID
        """
        try:
            # prompt client to close connection
            self.server.send(self.clientsocket,
                             self.menu.prompt_close_connection())
            # acknowledge client closed
            self._receive()
            # close client socket
            self.clientsocket.close()
            # if 'client-closed' in data:
            # data['client-closed'] == True

        except:
            pass
        # delete all client data
        try:
            with self.delete_client_data():
                raise ClientDisconnected()
        except ClientDisconnected:
            raise ClientDisconnected()
        except:
            pass

    def check_living_thread(self):
        """Use this function to check which client threads are alive"""
        output = "Living Threads:\n"
        for i, t in self.server.threadStarted.items():
            with self.lock:
                print(str(i) + ': ' + str(t.is_alive()))
            output += str(i) + ': ' + str(t.is_alive()) + "\n"
        self._send(self.menu.print_message(output))
        self._receive()

    def check_recipient_in_room(self):
        """Use this function to check recipients in every chat room"""
        output = "Recipient in Rooms:\n"
        for i, r in self.server.chat_room:
            with self.lock:
                print(str(i) + ': ' + str(r))
            output += str(i) + ': ' + str(r) + "\n"
        self._send(self.menu.print_message(output))
        self._receive()

    def set_client_info(self):
        """
        Send client id to client
        :param clientsocket:
        :return:
        """
        clientid = {'clientid': self.client_id}
        self._send(clientid)        
        self.client_id_key = self._receive()['id_key']
        with self.lock:
            print(f'Client %s with clientid %d has connected to this server' %
                  (self.client_id_key, self.client_id))

    def _send(self, data):
        """
        TODO: Serializes the data with pickle, and sends using the accepted client socket.
        :param data:
        :return:
        """
        try:
            serialized_data = pickle.dumps(data)
            data_len = pickle.dumps(len(serialized_data))
            #print(data)
            #print(f'****************** length = %d ******************' %
            #      len(serialized_data))
            self.clientsocket.send(data_len)
            self.clientsocket.recv(1000)
            self.clientsocket.send(serialized_data)
            # print('_send: ' + str(data))
        except Exception as ex:
            with self.lock:
                print(ex)

    def _receive(self, MAX_BUFFER_SIZE=4096):
        """
        TODO: Deserializes the data with pickle
        :param clientsocket:
        :param MAX_BUFFER_SIZE:
        :return: the deserialized data
        """
        try:
            data = self.clientsocket.recv(MAX_BUFFER_SIZE)
            # print('_receive: ' + str(pickle.loads(data)))
            return pickle.loads(data)
        except Exception as ex:
            with self.lock:
                print(ex)

    """----------------------- Proxy Server -----------------------"""

    def _sendProxyMenu(self):
        # send menu to client
        self.server.send(self.clientsocket,
                         self.menu.get_proxy_menu(self.cache, self.auth, self.private))
        # process client response
        self._process_proxy_options()

    def _process_proxy_options(self):
        try:
            data = self._receive()
            if not data:
                raise ClientDisconnected()
            # validates a valid option selected
            if 'option_selected' in data.keys() and 1 <= data['option_selected'] <= 5:
                # with self.lock:
                #    print('_process_proxy_options: ' + str(data))
                option = data['option_selected']
                # web caching
                if option == 1:
                    self._proxy_cache()
                # authentication
                elif option == 2:
                    self._proxy_auth()
                # private browsing
                elif option == 3:
                    self._proxy_private()
                # send request
                elif option == 4:
                    self._proxy_request()
                # turn web proxy server off
                else:
                    self._close_proxy()
                if option != 7:
                    self._sendProxyMenu()
            else:
                raise OptionSelectedIsInvalidError()
        except OptionSelectedIsInvalidError:
            with self.lock:
                print(
                    f'_process_proxy_options The option selected by client %d is out of range' % self.client_id)
            self._send(self.menu.print_message(
                f'_process_proxy_options The option selected by client %d is out of range\n' % self.client_id))
            self._receive()
            self._sendProxyMenu()
        except ClientDisconnected:
            raise ClientDisconnected()
        except TypeError as ex:
            with self.lock:
                print('_process_proxy_options Type Error')
            raise TypeError()
        except socket.error as ex:
            with self.lock:
                print(f'Client %d has forcibly closed connection in _process_proxy_options' %
                      self.client_id)
                # print(ex)
            raise socket.error()
        except Exception as ex:
            with self.lock:
                print(f'Client %d: _process_proxy_options error' %
                      self.client_id)
                print(ex)
            raise Exception()

    def _proxy_cache(self):
        '''
        Toggle cache service
        '''
        self.cache = not self.cache
        self._send(self.menu.print_message(
            f'Web caching is turned %s' % ('On' if self.cache else 'Off')))
        self._receive()
        with self.lock:
            print(f'Client %s %d it turning %s web cache' %
                  (self.client_id_key, self.client_id, 'On' if self.cache else 'Off'))

    def _proxy_request(self):
        '''
        Check and determine if proxy request should be make
        '''
        # getting request from user
        self.server.send(self.clientsocket,
                         self.menu.prompt_input('request> '))
        data = self._receive()
        try:
            method = data['message'].split()[0]
            domain = data['message'].split()[1]
            # .replace('http://', ''). replace('https://', '')
        except Exception:
            with self.lock:
                print(
                    f'_proxy_request by client %d is invalid' % self.client_id)
            self._send(self.menu.print_message(
                f'_proxy_request by client %d is invalid\n' % self.client_id))
            self._receive()
            return

        with self.lock:
            print(f'Client %s %d is making proxy request to %s' %
                  (self.client_id_key, self.client_id, domain))

        # if cache service is turned on AND method is GET
        if method == 'GET' and self.cache == True:
            # ask if client cached the response
            self._send(self.menu.check_cache(domain))
            data = self._receive()
            # if client cached the response, send the menu
            if data['cached'] == True:
                with self.lock:
                    print(f'Client %s %d has the domain %s cache' %
                          (self.client_id_key, self.client_id, domain))
                return

        # make the proxy request
        self._make_proxy_request(method, domain)

    def _make_proxy_request(self, method, domain):
        '''
        Make proxy request to external domain
        '''
        # opening proxy socket
        proxysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            buffer_size = 3900  # buffer size for proxysocket recv

            with self.lock:
                print(f'Client %s %d connecting to domain %s' %
                      (self.client_id_key, self.client_id, domain))
            # request to domain
            proxysocket.connect((domain, 80))
            request = f"%s / HTTP/1.0\n%s\n\n" % (method, domain)
            proxysocket.send(request.encode())

            # getting response from domain
            result = proxysocket.recv(buffer_size).decode(errors='ignore')
            #print(result)

            # sending status code to client
            status = result.split('\r\n')[0].split(' ', 1)
            statusCode = status[1].split(' ')[0]
            statusMsg = status[1].split(' ')[1]
            self._send(self.menu.print_message(
                f'%s %s %s' % (
                    'Success' if statusCode == '200' else 'Failed', statusCode, statusMsg)))
            self._receive()

            # getting remaining response from domain
            buff = result.split('\r\n')[-1]
            data = ''
            proxysocket.settimeout(2.)
            while True:
                try:
                    # with self.lock:
                    #    print('***************** receiving *****************')
                    #    print(data)
                    data = proxysocket.recv(
                        buffer_size).decode(errors="ignore")
                    # with self.lock:
                    #    print('*********************************************')
                    if not data or data == 0:
                        break
                    buff += data
                except socket.timeout:
                    break
                except Exception as ex:
                    raise
            # with self.lock:
            #    print('================ out of loop ===================')

            # sending domain response to client
            self.server.send(self.clientsocket,
                             self.menu.cached_print_message(domain, self.cache and method == 'GET', buff))
            self._receive()

        except socket.gaierror as ex:
            with self.lock:
                print(f'_proxy_request client %d not successful (socket.gaierror)' %
                      self.client_id)
                print(ex)
            try:
                self._send(self.menu.send_error_message(
                    '_proxy_request not successful socket.gaierror', ex))
                self._receive()
            except:
                pass
        except socket.error as ex:
            with self.lock:
                print(f'_proxy_request client %d not successful (socket.error)' %
                      self.client_id)
                print(ex)
            try:
                self._send(self.menu.send_error_message(
                    '_proxy_request not successful socket.error', ex))
                self._receive()
            except:
                pass
        except Exception as ex:
            with self.lock:
                print('_proxy_request error')
                print(ex)
            raise
        finally:
            try:
                # closing proxy server
                proxysocket.close()
            except:
                pass

    def _close_proxy(self):
        '''
        Close proxy server
        '''
        # make sure all proxy services are closed
        if self.cache == True:
            self.cache = False
        if self.auth == True:
            self.auth = False
        if self.private == False:
            self.private = True
        # returning to main menu
        self._send(self.menu.print_message(
            'Proxy server closed closed\n'))
        self._receive()
        with self.lock:
            print(f'Client %s %d is closing proxy server' %
                  (self.client_id_key, self.client_id))
        self._post_process()
