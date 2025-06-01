import os
import socket
import threading
import math
import time

# Get files / directories path
global_current_file_path = os.path.abspath(__file__)
global_peer_directory = os.path.dirname(global_current_file_path)
global_assignment_directory = os.path.dirname(global_peer_directory)
global_served_files_directory = global_peer_directory + "/served_files"

# Get the assigned peer ID
global_my_peer_id = os.path.basename(global_peer_directory)

# Create dictionnaries to store peers' IP addesses and port numbers
global_available_peers = []
global_peer_ips = {}
global_peer_ports = {}

# For temporary storage of downloaded file / chunks
global_download_buffer = {}

# The serving peers set during #DOWNLOAD
global_serving_peers_set = []
global_download_file_size = 0
lock_serving_peers_set = threading.Lock()

class FlielistThread(threading.Thread):
    def __init__(self, peer_id):
        threading.Thread.__init__(self)
        self.peer_id = peer_id

    def run(self):
        global global_peer_ips, global_peer_ports

        try:
            clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientSocket.connect( (global_peer_ips[self.peer_id], global_peer_ports[self.peer_id]) )
            request = "#FILELIST"
            clientSocket.send(request.encode())
            print(f"Client ({self.peer_id}): {request}")
            response = clientSocket.recv(1024).decode()
            print(f"Server ({self.peer_id}): {response}")
            clientSocket.close()
        except:
            print(f"TCP connection to server {self.peer_id} failed")

class UploadThread(threading.Thread):
    def __init__(self, peer_id, filename, no_of_bytes, chunks):
        threading.Thread.__init__(self)
        self.peer_id = peer_id
        self.filename = filename
        self.no_of_bytes = no_of_bytes
        self.chunks = chunks

    def run(self):
        global global_peer_ips, global_peer_ports

        try:
            clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientSocket.connect( (global_peer_ips[self.peer_id], global_peer_ports[self.peer_id]) )
            request = f"#UPLOAD {self.filename} bytes {self.no_of_bytes}"
            clientSocket.send(request.encode())
            print(f"Client ({self.peer_id}): {request}")
            response = clientSocket.recv(1024).decode()
            print(f"Server ({self.peer_id}): {response}")

            if response.startswith("330"):

                for i in range( len(self.chunks) ):

                    part_request = f"#UPLOAD {self.filename} chunk {i}"
                    request = f"{part_request} {self.chunks[i]}"
                    clientSocket.send(request.encode())
                    print(f"Client ({self.peer_id}): {part_request}")
                    response = clientSocket.recv(1024).decode()
                    print(f"Server ({self.peer_id}): {response}")
                    
                    if not response.startswith("200"):
                        print(f"File {self.filename} upload failed")
                        clientSocket.close()
                        return
                
                response = clientSocket.recv(1024).decode()
                print(f"Server ({self.peer_id}): {response}")
                if response.startswith("200"):
                    print(f"File {self.filename} upload success")
                else:
                    print(f"File {self.filename} upload failed")

            clientSocket.close()
        except:
            print(f"TCP connection to server {self.peer_id} failed")

class DownloadRequestThread(threading.Thread):
    def __init__(self, peer_id, filename):
        threading.Thread.__init__(self)
        self.peer_id = peer_id
        self.filename = filename

    def run(self):
        global global_peer_ips, global_peer_ports, global_serving_peers_set, global_download_file_size

        try:
            clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientSocket.connect( (global_peer_ips[self.peer_id], global_peer_ports[self.peer_id]) )
            request = f"#DOWNLOAD {self.filename}"
            clientSocket.send(request.encode())
            print(f"Client ({self.peer_id}): {request}")
            response = clientSocket.recv(1024).decode()
            print(f"Server ({self.peer_id}): {response}")
            clientSocket.close()

            if response.startswith("330"):
                lock_serving_peers_set.acquire()
                global_serving_peers_set.append(self.peer_id)
                global_download_file_size = int(response.split(" ")[-1])
                lock_serving_peers_set.release()
        except:
            print(f"TCP connection to server {self.peer_id} failed")

class DownloadTransferThread(threading.Thread):
    def __init__(self, peer_id, filename, offset, no_of_chunks, no_of_peers):
        threading.Thread.__init__(self)
        self.peer_id = peer_id
        self.filename = filename
        self.offset = offset
        self.no_of_chunks = no_of_chunks
        self.no_of_peers = no_of_peers
        
    def run(self):
        global global_peer_ips, global_peer_ports, global_download_buffer

        try:
            clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            clientSocket.connect( (global_peer_ips[self.peer_id], global_peer_ports[self.peer_id]) )
            
            for i in range( self.offset , self.no_of_chunks , self.no_of_peers ):
                time.sleep(0.5)
                request = f"#DOWNLOAD {self.filename} chunk {i}"
                clientSocket.send(request.encode())
                print(f"Client ({self.peer_id}): {request}")
                response = clientSocket.recv(1024).decode()
                
                index_of_content = 17 + len(self.filename) + len(str(i))

                print(f"Server ({self.peer_id}): {response[:index_of_content]}")

                if not response.startswith("200"):
                    clientSocket.close()
                    return
                
                global_download_buffer[i] = response[index_of_content:]

            time.sleep(0.5)
            clientSocket.close()
            
        except:
            print(f"TCP connection to server {self.peer_id} failed")

class ClientMain:
    def client_run(self):
        global global_assignment_directory
        global global_available_peers
        global global_peer_ips
        global global_peer_ports
        global global_served_files_directory
        global global_my_peer_id
        global global_download_buffer
        global global_serving_peers_set
        global global_download_file_size

        # Load the peer settings
        with open( global_assignment_directory + "/peer_settings.txt" ) as file:
            line = file.readline()
            while line != '':
                line = line.strip()
                peer_id , ip_addr , str_port = line.split(" ")
                global_available_peers.append(peer_id)
                global_peer_ips[peer_id] = ip_addr
                global_peer_ports[peer_id] = int(str_port)
                line = file.readline()

        # Holding child threads' reference for joining later
        threads = []

        # While loop to keep accepting user's command
        while True:

            # Print a newline to separate each command session
            print()

            # Accept user command
            command = input("Input your command: ")

            if ( command.startswith("#FILELIST") ):

                requested_peers = command.split(" ")[1:]

                threads.clear()
                for peer_id in requested_peers:
                    if peer_id in global_available_peers:
                        t = FlielistThread(peer_id)
                        threads.append(t)
                        t.start()
                
                for t in threads:
                    t.join()

            elif ( command.startswith("#UPLOAD") ):

                requested_filename = command.split(" ")[1]
                requested_peers = command.split(" ")[2:]

                if requested_filename in os.listdir(global_served_files_directory):

                    # Open the requested file
                    chunks = []
                    with open(f"{global_served_files_directory}/{requested_filename}", 'r') as file:
                        while True:
                            chunk = file.read(100)
                            if not chunk:
                                break
                            chunks.append(chunk)
                    
                    # Calculate number of bytes
                    no_of_bytes = ( len(chunks) - 1 ) * 100 + len(chunks[-1])

                    print(f"Uploading file {requested_filename}")
                    
                    threads.clear()
                    for peer_id in requested_peers:
                        if peer_id in global_available_peers:
                            t = UploadThread(peer_id, requested_filename, no_of_bytes, chunks)
                            threads.append(t)
                            t.start()
                    
                    for t in threads:
                        t.join()
                
                else:
                    print(f"Peer {global_my_peer_id} does not serve file {requested_filename}")
                
            elif ( command.startswith("#DOWNLOAD") ):

                requested_filename = command.split(" ")[1]
                requested_peers = command.split(" ")[2:]

                if requested_filename in os.listdir(global_served_files_directory):
                    print(f"File {requested_filename} already exists")
                else:

                    global_download_buffer.clear()
                    global_serving_peers_set.clear()

                    print(f"Downloading file {requested_filename}")

                    threads.clear()
                    for peer_id in requested_peers:
                        if peer_id in global_available_peers:
                            t = DownloadRequestThread(peer_id, requested_filename)
                            threads.append(t)
                            t.start()

                    for t in threads:
                        t.join()
                    
                    if not global_serving_peers_set:
                        str_serving_peers = ""
                        for peer_id in global_serving_peers_set:
                            str_serving_peers += f"{peer_id} "
                        print(f"File {requested_filename} download failed, peers {str_serving_peers}are not serving the file")
                    else:

                        offset = 0
                        no_of_chunks = math.ceil( global_download_file_size / 100 )
                        no_of_peers = len(global_serving_peers_set)

                        threads.clear()
                        for peer_id in global_serving_peers_set:
                            t = DownloadTransferThread(peer_id, requested_filename, offset, no_of_chunks, no_of_peers)
                            threads.append(t)
                            t.start()
                            offset += 1

                        for t in threads:
                            t.join()

                        if len(global_download_buffer) != no_of_chunks:
                            print(f"File {requested_filename} download failed")
                        else:
                            with open(f"{global_served_files_directory}/{requested_filename}", "w") as file:
                                for i in range( len(global_download_buffer) ):
                                    file.write( global_download_buffer[i] )
                            print(f"File {requested_filename} download success")

                    global_download_buffer.clear()
                    global_serving_peers_set.clear()

if __name__ == "__main__":
    client = ClientMain()
    client.client_run()