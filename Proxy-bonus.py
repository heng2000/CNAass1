import re
import os
from email.utils import parsedate_to_datetime
import socket
import sys
import datetime
from datetime import datetime, timezone


def getCachefromPath(urlReceive):
    urlReceive = re.sub('^(/?)http(s?)://', '', urlReceive, count=1)
    urlReceive = urlReceive.replace('/..', '')
    parts = urlReceive.split('/', 1)
    hostname = parts[0]
    resource = '/'
    if len(parts) == 2:
        resource += parts[1]
    cacheLocation = './' + hostname + resource
    if cacheLocation.endswith('/'):
        cacheLocation += 'default'
    dirPath = os.path.dirname(cacheLocation)
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
    return cacheLocation

def checkExpired(cachePath):
    headerPath = cachePath +"header"
    #print(headerPath)
    #do not exit means overdate
    if not os.path.exists(headerPath):
        return True
#read only
    with open(headerPath, 'r') as f:
        for line in f:
            #if find expires
            if line.lower().startswith("expires:"):
                try:
                    #split as 2 parts the second is date string strip() to remove sapve and
                    #parsedate_to_datetime change to datetime type
                    expireTime = parsedate_to_datetime(line.split(":", 1)[1].strip())
                    now = datetime.now(timezone.utc)
                    return now >= expireTime
                except Exception:
                    return True
    #expired if nothing match
    return True

def saveHeader(cachePath, responseContent, responsHeader):
    #GET THE CACHE PATH ADN wirte in the file content
    try:
        with open(cachePath, 'wb') as f:
            f.write(responseContent)
    except:
        print("can not write to cache fielcontent")
    #file header 
    headerPath = cachePath +"header"
    try:
        with open(headerPath, 'w') as f:
            for line in responsHeader:
                f.write(line + "\n")
    except:
        print("can not write to cache header")


#get client socket and url
def getRequest(cS, url):
    cachePath = getCachefromPath(url)
    #check whether cache is exist
    if os.path.exists(cachePath) and not checkExpired(cachePath):
        try:
            with open(cachePath, 'rb') as f:
                cS.sendall(f.read())
            print("read")
            return
        except:
            print("fail to read getRequest()")
    #cache does not exist or overdate
    print("from origin server")

    URI = re.sub('^(/?)http(s?)://', '', url, count=1)
    # Remove parent directory changes - security
    URI = URI.replace('/..', '')
    resourceParts = URI.split('/', 1)
    hostname = resourceParts[0]
    resource = '/' + resourceParts[1] if len(resourceParts) == 2 else '/'
    #connection with originServerSocket
    try:
        originServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        originServerSocket.connect((hostname, 80))
        print(f"connect to {hostname}:80")
    except Exception as e:
        print(f"connect failed: {e}")
        return
    originServerRequest = f"GET {resource} HTTP/1.1"
    originServerRequestHeader = f"Host: {hostname}\r\nConnection: close"
    request = originServerRequest + '\r\n' + originServerRequestHeader + '\r\n\r\n'
    try:
        originServerSocket.sendall(request.encode())

    except originServerSocket.error:
        print ('Forward request to origin failed')

        sys.exit()

    print('Request sent to origin server\n')

    #reveive response
    response = b""
    while True:
        data = originServerSocket.recv(4096)
        if not data:
            break
        response += data
    originServerSocket.close()
    #send to client
    try:
        cS.sendall(response)
    except:
        print("send all error")

    headerEnd  =response.find(b"\r\n\r\n")
    if headerEnd  !=-1:
        splitHeader =response[:headerEnd ].decode().split("\r\n")
        body =response[headerEnd  + 4:]
        saveHeader(cachePath , body,splitHeader)
        #if get html page
        #check whether ave html in respinse text
        if b"text/html" in splitHeader:
            #string
            htmlPart =body.decode()
            linkPart =GetHrefSrc(htmlPart)
            for link in linkPart:
                SaveHttpPage(link)
            #finish to write
    cS.shutdown(socket.SHUT_WR)
#Look for "href=" and "src=" in the HTML. (2 marks)

def GetHrefSrc(htmlContent):
    hrefPart = re.findall(r'href=["\'](http[s]?://[^"\']+)["\']', htmlContent)
    srcPart = re.findall(r'src=["\'](http[s]?://[^"\']+)["\']', htmlContent)
    return hrefPart + srcPart

def SaveHttpPage(url):
    cachePath= getCachefromPath(url)
    #check wheteher exist
    if os.path.exists(cachePath):
        return
    #get url
    urlReceive =re.sub('^(/?)http(s?)://', '', url, count=1)
    parts =urlReceive.split('/', 1)
    hostname= parts[0]
    resource = '/' + parts[1] if len(parts) == 2 else '/'

    createSocket =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #createSocket.settimeout(5)
    createSocket.connect((hostname, 80))

    request =f"GET {resource} HTTP/1.1\r\nHost: {hostname}\r\nConnection: close\r\n\r\n"
    createSocket.sendall(request.encode())

    response = b""
    while True:
        data =createSocket.recv(4096)
        if not data:
            break
        response += data
    createSocket.close()

    headerEnd =response.find(b"\r\n\r\n")
    if headerEnd  != -1:
        splitHeader = response[:headerEnd ].decode().split("\r\n")
        body = response[headerEnd  + 4:]
        saveHeader(cachePath , body,splitHeader)
        print(f"Find : {url}")

if __name__ == "__main__":
    if len(sys.argv) <= 2:
        print("Not enough arguments.")
        print("Usage: python Proxy-bonus.py <IP> <Port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    serverConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverConnection.bind((host, port))
    serverConnection.listen(5)
    print(f"Proxy running on {host}:{port}")

    while True:
        client_socket, addr = serverConnection.accept()
        try:
            request_data = client_socket.recv(4096).decode()
            first_line = request_data.split('\n')[0]
            url = first_line.split(' ')[1]
            getRequest(client_socket, url)
        except Exception as e:
            print("ero check error message", e)
        client_socket.close()