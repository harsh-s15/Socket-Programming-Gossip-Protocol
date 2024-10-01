import socket
import threading
import time
import random
import pickle

import csv

import warnings
warnings.filterwarnings("ignore")

from random import sample

class PeerNode:
    def __init__(self, ip, port, availableSeeds):
        """
        Initialize the PeerNode with IP, port, and available seed nodes

        """
        self.ip = ip
        self.port = port
        self.availableSeeds = availableSeeds
        self.output_file = output_file
        self.seed_nodes = set()
        self.connected_peers = set()
        self.messageList = set()
        self.gossip_count = 0
        self.connectedPeerSockets = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock = threading.Lock()
        self.dead = False
        self.peerCheckMisses = {}
        self.lastLivenessCheck = time.time()
        self.checkResponses = {}

    def kill(self):
        """
        Method to kill or terminate the peer node.

        """
        input()
        self.dead = True
        print('node is now dead')

    def start(self):
        """
        Method to start the peer node and handle incoming connections.

        """
        self.socket.bind((self.ip, self.port))
        self.socket.listen()

        # Register with seed nodes and connect to peers
        self.register_with_seed_nodes()
        self.connect_to_peers()

        # Start threads for broadcasting, killing, liveness check, and reporting dead nodes
        threading.Thread(target=self.broadcast).start()
        threading.Thread(target=self.kill).start()
        threading.Thread(target=self.livenessCheck).start()
        threading.Thread(target=self.reportDeadNode).start()

        while True:
            # Accept incoming connections from peers
            friendPeerSocket, friendPeerAddr = self.socket.accept()
            peer = pickle.loads(friendPeerSocket.recv(1024))
            self.connectedPeerSockets[peer] = friendPeerSocket
            self.connected_peers.add(peer)

            # Start a thread to listen to the connected peer
            threading.Thread(target=self.listenToPeers, args=(friendPeerSocket, peer,)).start()
            time.sleep(0.01)

    def listenToPeers(self, friendPeerSocket, peer):
        """
        Method to listen to incoming connections from peers.

        """
        while not (self.dead) and peer in self.connected_peers:
            try:
                data = friendPeerSocket.recv(1024).decode('utf-8')
            except:
                if self.dead:
                    break
            if self.dead:
                break
            if data.startswith('Liveness Request'):
                # Respond to liveness request
                if time.time() - float(data.split(':')[1]) < 0.01:
                    _, tstamp, senderIP = data.split(':')
                    livenessReply = f"Liveness Reply:{tstamp}:{senderIP}:{self.ip}{self.port}"
                    friendPeerSocket.send(livenessReply.encode('utf-8'))

            elif not (data.startswith('Liveness Reply')):
                # Process incoming message
                if time.time() - float(data.split(':')[0]) < 0.1:
                    self.lock.acquire()

                    if data not in self.messageList:
                        print(f"{data}")
                        with open(self.output_file, 'a') as f:
                            f.write(f"({self.ip}:{self.port}) : {data}\n")
                        for p in self.connectedPeerSockets:
                            if p != peer:
                                self.connectedPeerSockets[p].send(data.encode('utf-8'))
                        self.messageList.add(data)
                    self.lock.release()
            else:
                # Handle liveness reply
                print(data)
                peer = data.split(':')[3]
                peer = (peer[:-4], int(peer[-4:]))
                self.lock.acquire()
                if time.time() - self.lastLivenessCheck < 0.01:
                    if peer in self.peerCheckMisses:
                        self.peerCheckMisses[peer] -= 1
                self.lock.release()

    def broadcast(self):
        """
        Method to broadcast messages to connected peers.

        """
        while self.gossip_count < 10 and not (self.dead):
            message = f"{time.time()}:{self.ip}#{self.port}:gossip#{self.gossip_count}"

            self.lock.acquire()
            if self.dead:
                break
            for peer in self.connectedPeerSockets:
                peerSocket = self.connectedPeerSockets[peer]
                peerSocket.send(message.encode('utf-8'))
                time.sleep(0.01)
            self.lock.release()
            self.gossip_count += 1
            time.sleep(5)

    def livenessCheck(self):
        """
        Method to check the liveness of connected peers.

        """
        while not (self.dead):
            time.sleep(13)
            if self.dead:
                break
            self.lock.acquire()
            for peer in self.connected_peers:
                peerSocket = self.connectedPeerSockets[peer]
                livenessCheckmsg = f"Liveness Request:{time.time()}:{self.ip}#{self.port}"
                self.lastLivenessCheck = time.time()
                peerSocket.send(livenessCheckmsg.encode('utf-8'))

                if peer not in self.peerCheckMisses:
                    self.peerCheckMisses[peer] = 1
                else:
                    self.peerCheckMisses[peer] += 1
            self.lock.release()

    def reportDeadNode(self):
        """
        Method to report dead nodes to seed nodes.

        """
        while not (self.dead):
            self.lock.acquire()
            peerToBeRemoved = []

            for peer in self.connectedPeerSockets:
                if peer in self.peerCheckMisses and self.peerCheckMisses[peer] == 3:

                    peerToBeRemoved.append(peer)
                    deadMsg = f"Dead Node:{peer[0]}:{peer[1]}:{time.time()}:{self.ip}#{self.port}"

                    with open(self.output_file, 'a') as f:
                        f.write(f"({self.ip}:{self.port}) : {deadMsg}\n")

                    for seedNode in self.seed_nodes:
                        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                            s.connect(seedNode)
                            s.send(deadMsg.encode('utf-8'))
                    print(f'{deadMsg}')


            for deadPeer in set(peerToBeRemoved):
                self.connectedPeerSockets[deadPeer].close()
                self.connected_peers.remove(deadPeer)
                del (self.connectedPeerSockets[deadPeer])
                del (self.peerCheckMisses[deadPeer])

            self.lock.release()
            time.sleep(0.01)

            # Log reported dead nodes to output file


    def send_registration_request(self, seed_node):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(seed_node)
            registration_message = f"Register:{self.ip}:{self.port}"
            s.sendall(registration_message.encode('utf-8'))


    def register_with_seed_nodes(self):
        """
        Method to register with seed nodes.

        """
        l = []
        for seed_node in sample(self.availableSeeds, (len(self.availableSeeds) // 2) + 1):
            # separate socket instance for each peer-socket connection
            self.send_registration_request(seed_node)
            l.append(seed_node)
        self.seed_nodes = set(l[:])

        print(f"Connected to seeds :")
        for s in self.seed_nodes:
            print(f'{s[0]}:{s[1]}')

    def connect_to_peers(self):
        """
        Method to connect to available peers.

        """
        l = []
        for seed_node in self.seed_nodes:
            l.extend(self.request_peer_list(seed_node))
        l = set(l)
        self.connected_peers.update(random.sample(l, min(4, len(l))))

        print(f"Received peerList from seeds :")
        for p in l:
            print(f'{p[0]}:{p[1]}')

        self.lock.acquire()
        with open(r'outputfile.txt','a') as f:
            f.write(f'({self.ip}:{self.port}) : Received Peer List - {list(l)}\n')
        self.lock.release()

        print(f"Connecting to the following peers :")
        for p in self.connected_peers:
            print(f'{p[0]}:{p[1]}')
        print('----------------------------------------------------------------')


        self.lock.acquire()

        for peer in self.connected_peers:
            self.peerCheckMisses[peer] = 0
            self.connectedPeerSockets[peer] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connectedPeerSockets[peer].connect(peer)
            self.connectedPeerSockets[peer].send(pickle.dumps((self.ip, self.port)))
            threading.Thread(target=self.listenToPeers, args=(self.connectedPeerSockets[peer], peer)).start()

            time.sleep(0.01)
        self.lock.release()

    def start_liveness_check(self):
        """
        Method to start the liveness check.
        """
        while True:
            self.send_liveness_request()
            time.sleep(13)



    def request_peer_list(self, seed_node):
        """
        Method to request a peer list from a seed node.

        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(seed_node)
            request_message = f"RequestPeerList:{self.ip}:{self.port}"
            s.sendall(request_message.encode('utf-8'))
            peer_list = pickle.loads(s.recv(1024))
            return [p for p in peer_list if p[1] != self.port]


    def send_liveness_request(self):
        """
        Method to send a liveness request to connected peers.

        """
        for peer in self.connected_peers:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(peer)
                liveness_request = f"Liveness Request:{time.time()}:{self.ip}"
                s.sendall(liveness_request.encode('utf-8'))
                response = s.recv(1024).decode('utf-8')

                if response.startswith("Liveness Reply"):
                    _, sender_timestamp, sender_ip, _ = response.split(':')
                    if sender_timestamp == str(time.time()) and sender_ip == peer[0]:
                        print(f"Liveness Reply received from {peer}")


output_file = "outputfile.txt"

with open(r'config.csv','r') as f:
    config = csv.reader(f)

    seed_nodes = list(config)
    seed_nodes = [(x[0],int(x[1])) for x in seed_nodes[1:]]

peerPort = int(input('Enter peer Port : '))
peer = PeerNode("localhost", peerPort, seed_nodes)

threading.Thread(target=peer.start).start()