import os
import socket


def get_origin():
    return '@'.join([str(os.getpid()), socket.gethostname()])
