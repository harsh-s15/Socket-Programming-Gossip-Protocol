import socket
import threading
import pickle
import csv

import warnings
warnings.filterwarnings("ignore")

# reading ip addresses of seed nodes from config.csv
with open(r'config.csv','r') as f:
    config = csv.reader(f)
    seedNodes = list(config)
    seedNodes = [(x[0],int(x[1])) for x in seedNodes[1:]]

class SeedNode:
    def __init__(self, ip, port):
        """
        Initialize a new SeedNode object with the given IP address and port number.

        """
        self.ip = ip
        self.port = port
        self.output_file = output_file
        self.peer_list = set()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.lock = threading.Lock()

    def handle_dead_node(self, dead_node_ip, dead_node_port, timestamp, reporting_peer_ip):
        """
        Handle a dead node reported by a peer.

        """
        dead_node = (dead_node_ip, dead_node_port)
        if dead_node in self.peer_list:
            self.peer_list.remove(dead_node)
            print(f"({self.ip}:{self.port}) : Dead node reported by {reporting_peer_ip}: {dead_node}")

        # Log dead node messages to output file
        self.lock.acquire()
        with open(self.output_file, 'a') as f:
            f.write(f"Dead node reported by {reporting_peer_ip}: {dead_node}\n")
        self.lock.release()

    def start(self):
        """
        Start the seed node and handle incoming connections.

        """
        self.socket.bind((self.ip, self.port))
        self.socket.listen()

        print(f"SeedNode set up on ({self.ip}:{self.port})\n")

        while True:
            peerSocket, peerAddr = self.socket.accept()
            threading.Thread(target=self.handle_connection, args=(peerSocket, peerAddr)).start()

    def handle_connection(self, peerSocket, peerAddr):
        """
        Handle incoming connections.

        """
        with peerSocket:
            while True:
                data = peerSocket.recv(1024).decode('utf-8')

                if data.startswith("Register"):

                    self.lock.acquire()
                    _, peerIP, peerPort = data.split(':')
                    print(f"\n({self.ip}:{self.port}) : Received connection request - {data}")
                    with open(self.output_file, 'a') as f:
                        f.write(f"({self.ip}:{self.port}) : Received connection request - {data}\n")
                    self.peer_list.add((peerIP, int(peerPort)))
                    self.lock.release()

                elif data.startswith("RequestPeerList"):
                    _, peer_ip, peer_port = data.split(':')
                    peerSocket.sendall(pickle.dumps(self.peer_list))

                elif data.startswith("Dead Node"):
                    self.lock.acquire()
                    _, dead_node_ip, dead_node_port, timestamp, reporting_peer_ip = data.split(':')
                    dead_node = (dead_node_ip, int(dead_node_port))

                    print(f"\n({self.ip}:{self.port}) : Dead node reported by {reporting_peer_ip}:{dead_node}")
                    with open(self.output_file,'a') as f:
                        f.write(f"({self.ip}:{self.port}) : Dead node reported by {reporting_peer_ip}:{dead_node}\n")
                    if dead_node in self.peer_list:
                        self.peer_list.remove(dead_node)
                    self.lock.release()


if __name__ == "__main__":
    output_file = "outputfile.txt"

    with open(r'outputfile.txt','w') as f:
        pass

    seeds = [SeedNode(x[0],x[1]) for x in seedNodes]
    for i in range(len(seeds)):
        threading.Thread(target=seeds[i].start).start()