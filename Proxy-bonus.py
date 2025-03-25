'''
Author: yuheng li a1793138
Date: 2025-03-22 20:30:02
LastEditors: yuheng 
LastEditTime: 2025-03-25 20:03:18
FilePath: \CNAass1\Proxy-bonus.py
Description: 

Copyright (c) ${2024} by ${yuheng li}, All Rights Reserved. 
'''
#if exist .expires file at ht same time the expires does not overdate
#return from cache
#else try to re-get resource form server-update cache and .expires ifle
#the question is how to get the timestamp of .expires

#save to resource
'''
curl -iS http://localhost:8080/http://httpbin.org/cache/0
curl -iS http://localhost:8080/http://httpbin.org/cache/3600
'''

#server ip
#port and path of file
def fetch_and_cache_from_origin(webserver, port,filename):
    try:
        #inter net address for IPv4
        #socket type for TCP transport messages in the network
        #want to communicate with server
        origin_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        origin_socket.connect((webserver, port))
        response = b""
        request_header = response.find(b'\r\n\r\n')
        header_text = response[:request_header].decode()
        full_request = header_text + request_header
        #send all req
        origin_socket.sendall(full_request)
        #empty string
        response_text =""
        response_text = origin_socket.recv(4096)
        #save
        with open(filename, 'wb') as cache_file:
            cache_file.write(response_text)
        origin_socket.close()

    except Exception as e:
        print("error message:", e)

def main():
    webserver = "http://localhost:8080/http://httpbin.org/redirect-to?url=http://http.badssl.com&status_code=301"
    port =8080
    filename ="test1.txt"
    try:
        fetch_and_cache_from_origin(webserver,port,filename)

    except Exception as e:
            print("error : ", e)

if __name__ == "__main__":
    main()