#######################################################################################
# File:             menu.py
# Author:           Jose Ortiz
# Purpose:          CSC645 Assigment #1 TCP socket programming
# Description:      Template Menu class. You are free to modify this
#                   file to meet your own needs. Additionally, you are
#                   free to drop this Menu class, and use a version of yours instead.
# Important:        The server sends a object of this class to the client, so the client is
#                   in charge of handling the menu. This behaivor is strictly necesary since
#                   the client does not know which services the server provides until the
#                   clients creates a connection.
# Running:          This class is dependent of other classes.
# Usage :           menu = Menu() # creates object
#
########################################################################################

import textwrap


class Menu(object):
    """
    This class handles all the actions related to the user menu.
    An object of this class is serialized ans sent to the client side
    then, the client sets to itself as owner of this menu to handle all
    the available options.
    Note that user interactions are only done between client and user.
    The server or client_handler are only in charge of processing the
    data sent by the client, and send responses back.
    """
    @ staticmethod
    def get_menu():
        """
        Wrapper for data needed to send menu to client
        :return: python list containing protocols
        """
        menu = textwrap.dedent("""
        ****** TCP CHAT ******
        -----------------------
        Options Available:
        1. Get user list
        2. Sent a message
        3. Get my messages
        4. Create a new channel
        5. Chat in a channel with your friends
        6. Turn web proxy server on
        7. Disconnect from server\n""")
        # Debugging tools
        # 8. Check living threads
        # 9. Check recipient in room

        data = {'headers': [
            {
                'type': 'print',
                'body': {'message': menu}
            },
            {
                'type': 'input',
                'body': {
                        'message': "Your option <enter a number>: ",
                        'res-key': 'option_selected',
                        'res-type': 'int'
                }
            }
        ]}
        return data

    @staticmethod
    def prompt_send_message():
        """
        Wrapper for data needed to prompt client to send a message
        :return: python list containing protocols
        """
        data = {'headers': [
            {
                'type': 'input',
                'body': {
                        'message': 'Enter your message: ',
                        'res-key': 'message',
                        'res-type': 'string'
                }
            },
            {
                'type': 'input',
                'body': {
                        'message': 'Enter recipient id: ',
                        'res-key': 'recipient_id',
                        'res-type': 'int'
                }
            }
        ]}
        return data

    @staticmethod
    def print_message(message):
        """
        Wrapper for data needed for client to print
        :return: python list containing protocols
        """
        data = {'headers': [
            {
                'type': 'print',
                'body': {'message': message}
            }
        ]}
        return data

    @staticmethod
    def prompt_input(message, res_type='string', res_key='message'):
        """
        Wrapper for data needed to prompt client to enter an input
        :param: message, response type, response key
        :return: python list containing protocols
        """
        data = {'headers': [
            {
                'type': 'input',
                'body': {
                        'message': message,
                        'res-key': res_key,
                        'res-type': res_type
                }
            }
        ]}
        return data

    @staticmethod
    def open_chat(keyword):
        """
        Wrapper for data needed to prompt client to handle chat
        :return: python list containing protocols
        """
        data = {'headers': [
            {
                'type': 'open-chat',
                'body': {'close-key': keyword}
            }
        ]}
        return data

    @staticmethod
    def close_chat():
        """
        Wrapper for data needed to prompt client to close chat
        :return: python list containing protocols
        """
        data = {'headers': [{'type': 'close-chat'}]}
        return data

    @staticmethod
    def send_error_message(func_name, ex):
        """
        Wrapper for data needed to tell client that server has error
        :param: function name, exception message
        :return: python list containing protocols
        """
        data = {'headers': [
            {
                'type': 'print',
                'body': {'message':  func_name + ' error'}
            },
            {
                'type': 'print',
                'body': {'message': ex}
            }
        ]}
        return data

    @staticmethod
    def prompt_close_connection():
        """
        Wrapper for data to prompt client to close connection
        :return: python list containing protocols
        """
        data = {'headers': [
            {'type': 'close'}
        ]}
        return data

    @staticmethod
    def get_proxy_menu(cache, auth, private):
        """
        Wrapper for data needed for sending proxy menu
        :return: python list containing protocols
        """

        menu = textwrap.dedent(f"""
        *** Proxy Server Settings *** 
        1. Turn web caching %s
        2. Turn authentication %s
        3. Turn private browsing %s
        4. Send a request (GET, HEAD OR POST): 
        5. Turn web proxy server off\n"""
                               % ('Off' if cache else 'On', 'Off' if auth else 'On', 'Off' if private else 'On'))

        data = {'headers': [
            {
                'type': 'print',
                'body': {
                        'message': menu
                }
            },
            {
                'type': 'input',
                'body': {
                        'message': "Your option <enter a number>: ",
                        'res-key': 'option_selected',
                        'res-type': 'int'
                }
            }
        ]}
        return data

    @staticmethod
    def prompt_proxy(type):
        """
        Wrapper for data needed to prompt switching cache service
        :return: python list containing protocols
        """
        data = {'headers': [{'type': type }]}
        return data

    @staticmethod
    def cached_print_message(domain, cacheable, message):
        """
        Wrapper for data needed for client to print,
        prompt client to cache the message
        :return: python list containing protocols
        """
        data = {'headers': [
            {
                'type': 'print',
                'body': {
                    'cacheable': cacheable,
                    'domain': domain,
                    'message': message
                }
            }
        ]}
        return data

    @staticmethod
    def check_cache(domain):
        """
        Wrapper for data needed for client to check if domain is cached
        :return: python list containing protocols
        """
        data = {'headers': [
            {
                'type': 'check-cache',
                'body': {'domain': domain}
            }
        ]}
        return data
