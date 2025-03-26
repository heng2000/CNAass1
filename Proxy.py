# Include the libraries for socket and system calls
import socket
import sys
import os
import argparse
import re
import time
#python Proxy.py localhost 8080 tasklist | findstr python taskkill /F /PID 12345

#next step: handles url redirection 301 302
#handles cache-control
# 1MB buffer size
BUFFER_SIZE = 1000000

# Get the IP address and Port number to use for this web proxy server
parser = argparse.ArgumentParser()
parser.add_argument('hostname', help='the IP Address Of Proxy Server')
parser.add_argument('port', help='the port number of the proxy server')
args = parser.parse_args()
proxyHost = args.hostname
proxyPort = int(args.port)

# Create a server socket, bind it to a port and start listening
#Formatted string literals
try:
  # Create a server socket
  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  print ('Created socket')
  print(f"{proxyHost}:{proxyPort}...")
except:
  print ('Failed to create socket')
  sys.exit()

try:
  # Bind the the server socket to a host and port
  server_socket.bind((proxyHost, proxyPort))
  print ('Port is bound')
except:
  print('Port is already in use')
  sys.exit()

try:
  # Listen on the server socket
  server_socket.listen(5)
  print ('Listening to socket')
except:
  print ('Failed to listen')
  sys.exit()

# continuously accept connections
while True:
  print ('Waiting for connection...')
  clientSocket = None

  # Accept connection from client and store in the clientSocket
  try:
    clientSocket, clientAddr = server_socket.accept()
    print ('Received a connection')
    print(f'Received a connection from {clientAddr}')
  except:
    print ('Failed to accept connection')
    sys.exit()

  # Get HTTP request from client
  # and store it in the variable: message_bytes

  #get message form client at most 4096 b
  message_bytes = clientSocket.recv(4096)
  message = message_bytes.decode('utf-8')
  print ('Received request:')
  print ('< ' + message)

  # Extract the method, URI and version of the HTTP client request 
  requestParts = message.split()
  method = requestParts[0]
  URI = requestParts[1]
  version = requestParts[2]

  print ('Method:\t\t' + method)
  print ('URI:\t\t' + URI)
  print ('Version:\t' + version)
  print ('')

  # Get the requested resource from URI
  # Remove http protocol from the URI
  URI = re.sub('^(/?)http(s?)://', '', URI, count=1)

  # Remove parent directory changes - security
  URI = URI.replace('/..', '')

  # Split hostname from resource name
  resourceParts = URI.split('/', 1)
  hostname = resourceParts[0]
  resource = '/'

  if len(resourceParts) == 2:
    # Resource is absolute URI with hostname and resource
    resource = resource + resourceParts[1]

  print ('Requested Resource:\t' + resource)

  # Check if resource is in cache
  try:
    cacheLocation = './' + hostname + resource
    if cacheLocation.endswith('/'):
        cacheLocation = cacheLocation + 'default'

    print ('Cache location:\t\t' + cacheLocation)

    fileExists = os.path.isfile(cacheLocation)
    
    # Check wether the file is currently in the cache
    cacheFile = open(cacheLocation, "r")
    cacheData = cacheFile.readlines()
    #update whether cache is overdate
    #metaPath path for save mate file
    metaPath = cacheLocation + ".meta"
    #check whether metaPath is exist
    if os.path.exists(metaPath):
        #read
        with open(metaPath, "r") as meta:
            #find expireTime currentTime
            expireTime = int(meta.read())
            currentTime = int(time.time())
            #overdate
            if currentTime > expireTime:
                print(f"cache expired (expired at {expireTime},now {currentTime})")
                raise Exception("it is expired")
            else:
                print(f"cache still valid (expires at {expireTime},now {currentTime})")


#check cache and check though all cache,so we can use a for loop to go though
#if find, send back
    print ('Cache hit! Loading from cache file: ' + cacheLocation)
    # ProxyServer finds a cache hit
    # Send back response to client 

    for line in cacheData:
      clientSocket.sendall(line.encode())

    cacheFile.close()
    print ('Sent to the client:')
    print ('> ' + cacheData)
  except:
    # cache miss.  Get resource from origin server
    originServerSocket = None
    # Create a socket to connect to origin server
    # and store in originServerSocket
#does not find target form cache
#creat a socket and send req to server 
    try:
        originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('Created origin server socket')
    except:
        print('Failed to create socket for origin server')
        sys.exit()

    print ('Connecting to:\t\t' + hostname + '\n')
    try:
      # Get the IP address for a hostname
      address = socket.gethostbyname(hostname)
      # Connect to the origin server
      #connect?


      originServerSocket.connect((address, 80))
      
      
      print ('Connected to origin Server')

      originServerRequest = ''
      originServerRequestHeader = ''
      # Create origin server request line and headers to send
      # and store in originServerRequestHeader and originServerRequest
      # originServerRequest is the first line in the request and
      # originServerRequestHeader is the second line in the request


      originServerRequest = f"GET {resource} HTTP/1.1"
      originServerRequestHeader = f"Host: {hostname}\r\nConnection: close"

      # Construct the request to send to the origin server
      request = originServerRequest + '\r\n' + originServerRequestHeader + '\r\n\r\n'

      # Request the web resource from origin server
      print ('Forwarding request to origin server:')
      for line in request.split('\r\n'):
        print ('> ' + line)

      try:
        originServerSocket.sendall(request.encode())
      except socket.error:
        print ('Forward request to origin failed')
        sys.exit()

      print('Request sent to origin server\n')

      # Get the response from the origin server

      #reads data from a socket and save in response
      #fix: data is byte string, byt response is string
      #str and bytes can not conversion
      response = b""
      while True:
        data =originServerSocket.recv(BUFFER_SIZE)
        if not data:
          break
        response +=data
        #check redirection
        #check end of the headers
        #returns the index
      headerEnd = response.find(b'\r\n\r\n')
      #headers do not complete
      if headerEnd != -1:
          #get headers from the response
          #change to string
          header_text = response[:headerEnd].decode()
          #split headers into individual lines
          #first line
          #it should be 0 rather than 1
          status_line = header_text.splitlines()[0]
          #varify 301/302
          if "301" in status_line or "302" in status_line:
              print("Redirect:")
              #go though each line of the header
              for line in header_text.splitlines():
                  if line.startswith("Location:"):
                      #splits the line into two parts location and url
                      location_url = line.split(":",1)
                      print(f"redirect to: {location_url}")

      # Send the response to the client

      #send res back
      clientSocket.sendall(response)
      # Create a new file in the cache for the requested file.
      cacheDir, file = os.path.split(cacheLocation)
      print ('cached directory ' + cacheDir)
      if not os.path.exists(cacheDir):
        os.makedirs(cacheDir)
      cacheFile = open(cacheLocation, 'wb')

      # Save origin server response in the cache file
      # ~~~~ INSERT CODE ~~~~
      # ~~~~ END CODE INSERT ~~~~
      #??
      cacheFile.write(response)
      cacheFile.close()
      print ('cache file closed')
      #cacheTime save overdate time
      cacheTime=0
      #check end of the HTTP headers headerEnd
      headerEnd = response.find(b'\r\n\r\n')
      #FIND
      if headerEnd!= -1:
          #headerContent
          #response type is a byte and onlu get header part
          #change to string
          headerContent =response[:headerEnd].decode()
          #search for headers
          for line in headerContent.splitlines():
              #change to lowercase
              #if "Cache-Control" in line and "max-age" in line
              if "cache-control" in line.lower() and "max-age" in line.lower():
                  #used to find matched part a/more number and get hte number
                  #match = re.search(r'max-age=', line)
                  match = re.search(r'max-age=(\d+)')
                  if match:
                      #get the number last step
                      cacheTime = int(match.group(1))
                      print(f"Cache-Control: the  max-age = {cacheTime} seconds")
                      expires_at = int(time.time()) + cacheTime
                      with open(cacheLocation + ".meta", "w") as metafile:
                          metafile.write(str(expires_at))
                          print(f"Cache-Control: cache will expire at {expires_at}")

      # finished communicating with origin server - shutdown socket writes
      print ('origin response received. Closing sockets')
      originServerSocket.close()
       
      clientSocket.shutdown(socket.SHUT_WR)
      print ('client socket shutdown for writing')
    except OSError as err:
      print ('origin server request failed. ' + err.strerror)

  try:
    clientSocket.close()
  except:
    print ('Failed to close client socket')

    '''PS C:\Users\lenovo\Desktop\CNA\CNAass1> python Proxy.py localhost 8080
Created socket
localhost:8080...
Port is bound
Listening to socket
Waiting for connection...
Received a connection
Received a connection from ('127.0.0.1', 55957)
Received request:
< GET /http://httpbin.org/cache/0 HTTP/1.1
Host: localhost:8080
User-Agent: curl/8.10.1
Accept: */*


Method:         GET
URI:            /http://httpbin.org/cache/0
Version:        HTTP/1.1

Requested Resource:     /cache/0
Cache location:         ./httpbin.org/cache/0
cache expired (expired at 1742973996,now 1742974714)
Created origin server socket
Connecting to:          httpbin.org

Connected to origin Server
Forwarding request to origin server:
> GET /cache/0 HTTP/1.1
> Host: httpbin.org
> Connection: close
>
>
Request sent to origin server

cached directory ./httpbin.org/cache
cache file closed
Traceback (most recent call last):
  File "C:\Users\lenovo\Desktop\CNA\CNAass1\Proxy.py", line 128, in <module>
    raise Exception("it is expired")
Exception: it is expired

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\lenovo\Desktop\CNA\CNAass1\Proxy.py", line 268, in <module>
    match = re.search(r'max-age=(\d+)')
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: search() missing 1 required positional argument: 'string'
PS C:\Users\lenovo\Desktop\CNA\CNAass1>'''