import re
import os
from email.utils import parsedate_to_datetime
def getCachefromPath(URI):
    URI = re.sub('^(/?)http(s?)://', '', URI, count=1)
    URI = URI.replace('/..', '')
    parts = URI.split('/', 1)
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
                    now = int(time.time())
                    return now >= expireTime
                except:
                    return True
    return True


def saveHeader(cachePath, responseContent, responsHeader):
    #GET THE CACHE PATH ADN wirte in the file content
    with open(cachePath, 'wb') as f:
        f.write(responseContent)
    #file header 
    headerPath = cachePath +"header"
    with open(headerPath, 'w') as f:
        for header in responsHeader:
            f.write(header + "\n")

if __name__ == "__main__":
    url = "http://httpbin.org/cache/60"
    print("Cache path:", getCachefromPath(url))
    Cachepath = getCachefromPath(url)
    responseContent = b"<html><body><h1>Hello, World!</h1></body></html>"
    responseHeader = [
        "GET /http://httpbin.org/cache/60 HTTP/1.1"
        "Host: localhost:8080"
        "User-Agent: curl/8.10.1"
        "Accept: */*"
        "Expires: Wed, 01 Apr 2025 12:00:00 GMT"
    ]
    saveHeader(Cachepath , responseContent, responseHeader)
    result =checkExpired(getCachefromPath(url))
    print(result)

    PS C:\Users\lenovo\Desktop\CNA\CNAass1> python Proxy-bonus.py
Cache path: ./httpbin.org/cache/60
True
PS C:\Users\lenovo\Desktop\CNA\CNAass1>
