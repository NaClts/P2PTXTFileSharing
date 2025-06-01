# P2PTXTFileSharing
*A simple Python application for peer-to-peer (P2P) text file sharing*

## Description
The P2PTXTFileSharing is a simple P2P file sharing application implemented using Python socket programming. Being a much simplified version of real-world P2P systems, it only provides P2P file sharing of TXT files.

In this application, each peer acts as both a client and a server: 
* The client programs upload and download files to and from other peers.
* The server programs collaboratively serve files for others to download.

## Installation & Execution

1. For each machine that some peer(s) will be running on, create a new directory so that it will be identified as the "root directory" of this application.

2. Inside the root directory of each machine, create a text file `peer_settings.txt`. Each of them should save the same set and the entire list of peers. That is, on each line, the files save the following information: 
`peer_ID ip_addr server_port`

3. Inside the root directory of each machine, create "peer folder(s)". For example, if peers p1 & p2 will be running on some machine, that machine should create folders `p1` & `p2` in the root directory.

4. Inside each peer folder, save a copy of both `client.py` & `server.py`. The Python source files can be found in the `src` folder in this directory.

5. Inside each peer folder, create a directory `served_files`. This folder will store the files that will be served by the corresponding peer of this peer folder.

6. For each peer, execute the following commands in the corresponding peer folder:
* `python server.py`
* `python client.py`

## Usage

* **`#FILELIST p1 p2 p3 ...`**: Discover files served by specified peers (In this case: p1, p2, p3, ...)

* **`#UPLOAD filename p1 p2 p3 ...`**: Share the file with `filename` to a selected set of peers (In this case: p1, p2, p3, ...)

* **`#DOWNLOAD filename p1 p2 p3 ...`**: Download the file specified by `filename` from a group of peers (In this case: p1, p2, p3, ...); Note that the peers serving the wanted file will collaborate to speed up the file serving

## Example Setup & Demonstration

The example setup can be found in the folder `example` in this repository:

```
example
│   peer_settings.txt
├───p1
│   │   client.py
│   │   server.py
│   └───served_files
│           hello_world.txt
├───p2
│   │   client.py
│   │   server.py
│   └───served_files
│           lorem_ipsum.txt
├───p3
│   │   client.py
│   │   server.py
│   └───served_files
│           lorem_ipsum.txt
├───p4
│   │   client.py
│   │   server.py
│   └───served_files
│           lorem_ipsum.txt
└───p5
    │   client.py
    │   server.py
    └───served_files
```

In this example, we run 5 peers on a single machine. 2 files are served in this P2P system:
* `hello_world.txt` served by p1
* `lorem_ipsum.txt` served by p2, p3, and p4

The video below will demonstrate p5 downloading the 2 files from other peers:

[![Demonstration](https://img.youtube.com/vi/m4WNl_InvCU/0.jpg)](https://youtu.be/m4WNl_InvCU)

## Remarks

This project is submitted as HKU COMP3234 Course Assignment.
