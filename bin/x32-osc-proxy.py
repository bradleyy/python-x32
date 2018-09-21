"""
Proxy for Behringer X32 to touchOSC
Modified from https://github.com/tjoracoder/python-x32 by Teppo Rekola, sytem@iki.fi
test version 0.4, 17.1.2014 


This software is licensed under the Modified BSD License:

Copyright (c) 2013, Sigve Tjora
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the <organization> nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import OSC
import time
import threading
import re

# list of targets:
# host, udp-port, regexp to forward
# r'foo' notation for raw strings
targets = ( ( '10.0.0.31', 10024, r'.*' ),  ( 'localhost', 10025, r'foo' ) )
#targets = ( ( 'localhost', 10024, r'.*' ), ( 'localhost', 10025, r'/ch/02/.*' ), ( 'localhost', 10025, r'foo' ))


clients = {}


def request_x32_to_send_change_notifications(client):
    """request_x32_to_send_change_notifications sends /xremote repeatedly to
    mixing desk to make sure changes are transmitted to our server.
    """
    while True:
        client.send(OSC.OSCMessage("/xremote"))
        client.send(OSC.OSCMessage("/ch/01/mix/on"))
        client.send(OSC.OSCMessage("/ch/19/mix/on"))

        client.send(OSC.OSCMessage("/ch/02/mix/on"))
        client.send(OSC.OSCMessage("/ch/20/mix/on"))

        client.send(OSC.OSCMessage("/ch/01/mix/01/level"))
        client.send(OSC.OSCMessage("/ch/02/mix/01/level"))
        client.send(OSC.OSCMessage("/ch/03/mix/01/level"))
        client.send(OSC.OSCMessage("/ch/05/mix/01/level"))
        client.send(OSC.OSCMessage("/ch/17/mix/01/level"))

        client.send(OSC.OSCMessage("/ch/01/mix/02/level"))
        client.send(OSC.OSCMessage("/ch/02/mix/02/level"))
        client.send(OSC.OSCMessage("/ch/03/mix/02/level"))
        client.send(OSC.OSCMessage("/ch/05/mix/02/level"))
        client.send(OSC.OSCMessage("/ch/17/mix/02/level"))
        time.sleep(7)

def serve_proxy(proxy_server):
    proxy_server.serve_forever()

def print_all_x32_change_messages(x32_address, server_udp_port, client_udp_port):

    def send_to_clients(addr, data):
        # check regexp for each target, if true, send to ip:port of target
        txt = 'OSCMessage("%s", %s)' % (addr, data)
        print "input:" + txt

        for i,targetClient in enumerate(connections):
            if re.match( targets[i][2], addr):
                print "send: " + txt + " to: " + targets[i][0] + ":", targets[i][1]

                targetClient.send(OSC.OSCMessage(addr,data))

        for i, targetClient in enumerate(clients):
            clients[targetClient].send(OSC.OSCMessage(addr, data))

    def x32_msg_handler(addr, tags, data, client_address):
        send_to_clients(addr, data)

    def client_msg_handler(addr, tags, data, client_address):
        txt = '[%s] OSCMessage("%s", %s)' % (client_address, addr, data)
        print "input:" + txt
        if client_address not in clients:
            clients[client_address] = OSC.OSCClient()
            clients[client_address].connect(client_address)
        print clients
        x32_client.send(OSC.OSCMessage(addr, data))
        send_to_clients(addr, data) # x32 will not echo our own messages, we must do it ourselves


    x32_server = OSC.OSCServer(("", server_udp_port))
    x32_server.addMsgHandler("default", x32_msg_handler)
    x32_client = OSC.OSCClient(server=x32_server) #This makes sure that client and server uses same socket. This has to be this way, as the X32 sends notifications back to same port as the /xremote message came from
    
    x32_client.connect((x32_address, 10023))

    # gateway for proxied clients
    proxy_server = OSC.OSCServer(("", client_udp_port))
    proxy_server.addMsgHandler("default", client_msg_handler)

    proxy_thread = threading.Thread(target=serve_proxy, kwargs = {"proxy_server": proxy_server})
    proxy_thread.daemon=True # to get ctrl+c work
    proxy_thread.start()
    
    # connections to targets
    connections = list()
    print "create connections:"
    for i,host in enumerate(targets):
    	print host[0] , host[1]
    	connections.append( OSC.OSCClient() ) 
    	connections[i].connect((host[0],host[1]))    	
    print "\n"
    
    thread = threading.Thread(target=request_x32_to_send_change_notifications, kwargs = {"client": x32_client})
    thread.daemon=True # to get ctrl+c work
    thread.start()

    x32_server.serve_forever()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Forward OSC-messages from X32 to multiple clients, with filter by regular expressions per target. Targets are configured at the begining of this file.")
    parser.add_argument('--address', required = True,                        
                        help='name/ip-address of Behringer X32 mixing desk')
    parser.add_argument('--port', default = 10300,                        
                        help='UDP-port to open on this machine for X32 return traffic.')
    parser.add_argument('--client-port', default = 10023,
                        help='UDP-port to open on this machine for clients.')

    args = parser.parse_args()
    print_all_x32_change_messages(x32_address = args.address, server_udp_port = args.port, client_udp_port = args.client_port)
    
