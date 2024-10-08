<h1>Steps to Test:</h1>

<ol>
<li>
<h3>Setup:</h3>

Make sure Python is installed on your system.
Download the provided seed.py, peer.py, and config.csv files.
Make sure your system supports dynamic multithreading.

</li>

<li>
<h3>Configuration:</h3>

Modify config.csv to add or remove seed nodes and peers.
Each line in config.csv should contain an IP address and port number separated by a comma. The first line should contain the header and subsequent lines should list the seed nodes and peers.
</li>


<li>
<h3>Run Seed Nodes:</h3>

Run seed.py to start seed nodes. Each seed node listens for incoming connections from peers.
Example command: <code>python seed.py</code>
</li>

<li>
<h3>Run Peer Nodes:</h3>

Run peer.py to start peer nodes. Each peer node registers with seed nodes, connects to other peers, and initiates gossip protocol and liveness checks.
Enter the port number for the peer when prompted.
Example command: <code>python peer.py</code>
Run multiple instances of peer.py (on different command prompt windows) with different port numbers to simulate multiple peers.
</li>

![image](https://github.com/user-attachments/assets/af723e4c-7b01-4336-bfb3-cc11a7106900)

In fact, you can even connect 2 or more computers using socket programming. Here's how : Replace localhost (in config.csv) with the ip of your own system (the one which is going to spawn the seed nodes by running <code>seed.py</code>). eg - 172.31.87.53 
<br>
You can use the python statement <code>socket.gethostbyname(socket.gethostname())</code> to get the IP of your machine. Next, make sure all the computer(s) are connected to the same WIFI network, and run the file <code>peer.py</code> on the systems you wish to designate as peers. Upon entering an unused port number for the peer nodes, you can easily see the connection request being trasmitted to the seed node from the peers, and subsequent gossip-protocol interaction.


<li>
<h3>Testing Features:</h3>

<h4>Gossip Protocol:</h4> Monitor the terminal output of peer nodes to observe gossip messages being exchanged.
<h4>Liveness Messages:</h4> Check if liveness messages are sent and received between peers, as indicated in the terminal output.
<h4>Node Killing:</h4> Press enter in the terminal running a peer node to simulate killing the node. Observe termination confirmation in the terminal.
<h4>Dynamic Configuration:</h4> Modify config.csv to add or remove seed nodes and peers. Restart the seed and peer nodes to reflect the changes.

<li>
<h3>Logging:</h3>

Logs of events such as peer registrations, dead node reports, and received messages are appended to output.txt.
</li>

</ol>

![gossip in library](https://github.com/user-attachments/assets/3deed94d-9e09-4d13-957a-5a27a15c183c)


PS. Here is a quick snap of what the protocol looks like running on multiple connected systems, lol! (IIT Jodhpur Library, CC-LAB-1)

