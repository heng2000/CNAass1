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
        #fix error splitHeader is str but i want is byte
        #always return f
        if any("text/html" in line.lower() for line in splitHeader):
            #string
            htmlPart =body.decode()
            linkPart =GetHrefSrc(htmlPart)
            for link in linkPart:
                SaveHttpPage(link)
            print("html find")
            #finish to write
    #cS.shutdown(socket.SHUT_WR)
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


C:\Users\lenovo\Desktop\CNA\CNAass1>curl -iS "http://localhost:8080/http://httpbin.org/html"
HTTP/1.1 200 OK
Date: Fri, 28 Mar 2025 05:20:04 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 3741
Connection: close
Server: gunicorn/19.9.0
Access-Control-Allow-Origin: *
Access-Control-Allow-Credentials: true

<!DOCTYPE html>
<html>
  <head>
  </head>
  <body>
      <h1>Herman Melville - Moby-Dick</h1>

      <div>
        <p>
          Availing himself of the mild, summer-cool weather that now reigned in these latitudes, and in preparation for the peculiarly active pursuits shortly to be anticipated, Perth, the begrimed, blistered old blacksmith, had not removed his portable forge to the hold again, after concluding his contributory work for Ahab's leg, but still retained it on deck, fast lashed to ringbolts by the foremast; being now almost incessantly invoked by the headsmen, and harpooneers, and bowsmen to do some little job for them; altering, or repairing, or new shaping their various weapons and boat furniture. Often he would be surrounded by an eager circle, all waiting to be served; holding boat-spades, pike-heads, harpoons, and lances, and jealously watching his every sooty movement, as he toiled. Nevertheless, this old man's was a patient hammer wielded by a patient arm. No murmur, no impatience, no petulance did come from him. Silent, slow, and solemn; bowing over still further his chronically broken back, he toiled away, as if toil were life itself, and the heavy beating of his hammer the heavy beating of his heart. And so it was.—Most miserable! A peculiar walk in this old man, a certain slight but painful appearing yawing in his gait, had at an early period of the voyage excited the curiosity of the mariners. And to the importunity of their persisted questionings he had finally given in; and so it came to pass that every one now knew the shameful story of his wretched fate. Belated, and not innocently, one bitter winter's midnight, on the road running between two country towns, the blacksmith half-stupidly felt the deadly numbness stealing over him, and sought refuge in a leaning, dilapidated barn. The issue was, the loss of the extremities of both feet. Out of this revelation, part by part, at last came out the four acts of the gladness, and the one long, and as yet uncatastrophied fifth act of the grief of his life's drama. He was an old man, who, at the age of nearly sixty, had postponedly encountered that thing in sorrow's technicals called ruin. He had been an artisan of famed excellence, and with plenty to do; owned a house and garden; embraced a youthful, daughter-like, loving wife, and three blithe, ruddy children; every Sunday went to a cheerful-looking church, planted in a grove. But one night, under cover of darkness, and further concealed in a most cunning disguisement, a desperate burglar slid into his happy home, and robbed them all of everything. And darker yet to tell, the blacksmith himself did ignorantly conduct this burglar into his family's heart. It was the Bottle Conjuror! Upon the opening of that fatal cork, forth flew the fiend, and shrivelled up his home. Now, for prudent, most wise, and economic reasons, the blacksmith's shop was in the basement of his dwelling, but with a separate entrance to it; so that always had the young and loving healthy wife listened with no unhappy nervousness, but with vigorous pleasure, to the stout ringing of her young-armed old husband's hammer; whose reverberations, muffled by passing through the floors and walls, came up to her, not unsweetly, in her nursery; and so, to stout Labor's iron lullaby, the blacksmith's infants were rocked to slumber. Oh, woe on woe! Oh, Death, why canst thou not sometimes be timely? Hadst thou taken this old blacksmith to thyself ere his full ruin came upon him, then had the young widow had a delicious grief, and her orphans a truly venerable, legendary sire to dream of in their after years; and all of them a care-killing competency.
        </p>
      </div>
  </body>
</html>