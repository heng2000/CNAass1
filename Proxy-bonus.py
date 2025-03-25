'''
Author: yuheng li a1793138
Date: 2025-03-22 20:30:02
LastEditors: yuheng 
LastEditTime: 2025-03-25 19:42:56
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
#port and path of file filename connect to client
def fetch_and_cache_from_origin(webserver, port, resource, filename, client_socket):
    try:
        #inter net address for IPv4
        #socket type for TCP transport messages in the network
        #want to communicate with server
        origin_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        origin_socket.connect((webserver, port))
    except Exception as e:
        print("error message:", e)