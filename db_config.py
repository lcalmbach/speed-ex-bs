import os
import socket


if socket.gethostname() == 'cc75a393-92bb-4bff-8248-0d379f57cff7':
    DB_USER = "dxkqwxlfbaffnk"
    DB_PSSWD = os.environ.get('DB_PSSWD')
    DB_HOST = 'ec2-54-216-17-9.eu-west-1.compute.amazonaws.com'
    DB_DATABASE = 'd3f49ft1g3uc8t'
    DB_PORT = "5432"
else:
    DB_USER = "postgres"
    DB_PASS = 'password'
    DB_HOST = 'localhost' 
    DB_DATABASE = 'velox'
    DB_PORT = "5432"

