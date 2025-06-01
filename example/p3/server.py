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

# Get the assigned peer ID and port number
global_my_peer_id = os.path.basename(global_peer_directory)

# Holding a list of files that are currently being uploaded to this server
global_current_upload_files_list = []
lock_current_upload_files_list = threading.Lock()  # A mutex lock to protect the shared variable "global_current_upload_files"

class ServerThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client

    def run(self):
        global global_served_files_directory
        global global_current_upload_files_list

        connectionSocket, addr = self.client
        
        try:

            request = connectionSocket.recv(1024).decode()

            if ( request.startswith("#FILELIST") ):
                response = "200 Files served:"
                served_files_list = os.listdir(global_served_files_directory)
                for served_file in served_files_list:
                    response += f" {served_file}"
                connectionSocket.send(response.encode())

            elif ( request.startswith("#UPLOAD") ):
                upload_bytes = int(request.split(" ")[-1])
                upload_filename = request[8:(-7-len(str(upload_bytes)))]

                lock_current_upload_files_list.acquire()
                is_receiving = upload_filename in global_current_upload_files_list
                if (not is_receiving):
                    global_current_upload_files_list.append(upload_filename)
                lock_current_upload_files_list.release()

                if (is_receiving):
                    response = f"250 Currently receiving file {upload_filename}"
                    connectionSocket.send(response.encode())
                elif ( upload_filename in os.listdir(global_served_files_directory) ):

                    lock_current_upload_files_list.acquire()
                    global_current_upload_files_list.remove(upload_filename)
                    lock_current_upload_files_list.release()
                    
                    response = f"250 Already serving file {upload_filename}"
                    connectionSocket.send(response.encode())
                else:

                    try:
                        response = f"330 Ready to receive file {upload_filename}"
                        connectionSocket.send(response.encode())

                        no_of_chunks = math.ceil( upload_bytes / 100 )
                        upload_file_buffer = []

                        for i in range(no_of_chunks):
                            request = connectionSocket.recv(1024).decode()
                            index_of_content = 16 + len(upload_filename) + len(str(i))
                            upload_file_buffer.append( request[index_of_content:] )
                            response = f"200 File {upload_filename} chunk {i} received"
                            connectionSocket.send(response.encode())
                            time.sleep(0.5)
                        
                        with open(f"{global_served_files_directory}/{upload_filename}", "w") as file:
                            for chunk in upload_file_buffer:
                                file.write(chunk)
                        
                        lock_current_upload_files_list.acquire()
                        global_current_upload_files_list.remove(upload_filename)
                        lock_current_upload_files_list.release()

                        response = f"200 File {upload_filename} received"
                        connectionSocket.send(response.encode())
                    
                    except:
                        lock_current_upload_files_list.acquire()
                        global_current_upload_files_list.remove(upload_filename)
                        lock_current_upload_files_list.release()
                        print(f"TCP connection to client {addr} failed")


            elif ( request.startswith("#DOWNLOAD") and request.endswith(".txt") ):
                download_filename = request[10:]
                
                if not ( download_filename in os.listdir(global_served_files_directory) ):
                    response = f"250 Not serving file {download_filename}"
                    connectionSocket.send(response.encode())
                else:

                    chunks = []
                    with open(f"{global_served_files_directory}/{download_filename}", 'r') as file:
                        while True:
                            chunk = file.read(100)
                            if not chunk:
                                break
                            chunks.append(chunk)
                    
                    # Calculate number of bytes
                    no_of_bytes = ( len(chunks) - 1 ) * 100 + len(chunks[-1])

                    response = f"330 Ready to send file {download_filename} bytes {no_of_bytes}"
                    connectionSocket.send(response.encode())

            elif ( request.startswith("#DOWNLOAD") ):
                download_filename = request.split(" ")[1]
                if not ( download_filename in os.listdir(global_served_files_directory) ):
                    response = f"250 Not serving file {download_filename}"
                    connectionSocket.send(response.encode())
                else:
                    
                    chunks = []
                    with open(f"{global_served_files_directory}/{download_filename}", 'r') as file:
                        while True:
                            chunk = file.read(100)
                            if not chunk:
                                break
                            chunks.append(chunk)
                    
                    # Calculate number of bytes
                    no_of_bytes = ( len(chunks) - 1 ) * 100 + len(chunks[-1])

                    try:
                        while True:
                            i = int(request.split(" ")[-1])
                            response = f"200 File {download_filename} chunk {i} {chunks[i]}"
                            connectionSocket.send(response.encode())
                            request = connectionSocket.recv(1024).decode()
                    except:
                        print(f"Client {addr} download completed")

            connectionSocket.close()
        
        except:
            print(f"TCP connection to client {addr} failed")

class ServerMain:
    def server_run(self):
        global global_assignment_directory, global_my_peer_id

        # Load the assigned port from peer settings
        with open( global_assignment_directory + "/peer_settings.txt" ) as file:
            line = file.readline()
            while line != '':
                line = line.strip()
                peer_id , ip_addr , str_port = line.split(" ")
                if ( peer_id == global_my_peer_id ):
                    server_port = int(str_port)
                line = file.readline()

        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind( ("", server_port) )
        serverSocket.listen(5)
        while True:
            client = serverSocket.accept()
            t = ServerThread(client)
            t.start()

if __name__ == "__main__":
    server = ServerMain()
    server.server_run()