import ast
import collections
import os
import smtplib


def send_file(file_name, socket_obj):
    """ Robust file transfer method """
    BYTES_RECV = 1024

    statinfo = os.stat(file_name)
    file_size = statinfo.st_size

    # encode filesize as 32 bit binary
    fsize_b = bin(file_size)[2:].zfill(32)
    socket_obj.send(fsize_b.encode('ascii'))

    f = open(file_name, 'rb')

    while file_size >= BYTES_RECV:
        l = f.read(BYTES_RECV)
        socket_obj.send(l)
        file_size -= BYTES_RECV

    if file_size > 0:
        l = f.read(file_size)
        socket_obj.send(l)

    f.close()


def recv_file(file_name, socket_obj):
    """ Robust file transfer method """
    BYTES_RECV = 1024

    fsize_b = socket_obj.recv(32).decode('ascii')
    fsize = int(fsize_b, 2)

    f = open(file_name, 'wb')
    file_size = fsize

    while file_size >= BYTES_RECV:
        buff = bytearray()
        while len(buff) < BYTES_RECV:
            buff.extend(socket_obj.recv(BYTES_RECV - len(buff)))
        f.write(buff)
        file_size -= BYTES_RECV

    if file_size > 0:
        buff = bytearray()
        while len(buff) < file_size:
            buff.extend(socket_obj.recv(file_size - len(buff)))
        f.write(buff)

    f.close()


def write_file(file_name, string):
    with open(file_name, 'w+') as f:
        f.write(string)


def read_file(file_name):
    with open(file_name) as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    return content


def ascii_len(s):
    """ returns string size in bytes """
    return len(s.encode('ascii'))


def send_string(string, socket_obj):
    size = ascii_len(string)

    # encode string size as 32 bit binary
    fsize_b = bin(size)[2:].zfill(32)
    socket_obj.send(fsize_b.encode('ascii'))

    socket_obj.send(string.encode('ascii'))


def recv_string(socket_obj):
    fsize_b = socket_obj.recv(32).decode('ascii')
    fsize = int(fsize_b, 2)

    return socket_obj.recv(fsize).decode('ascii')


def send_verification_email(recv_addr, pwd):
    try:
        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.starttls()
        session.login("fabchat.service@gmail.com", "fabchat-test")
        message = "Subject: Hi there!\n\nYour password is " + pwd + "."
        session.sendmail("fabchat.service@gmail.com", recv_addr, message)
        session.quit()
    except Exception as e:
        print(e)
        return "-1"


def format_query(raw_query_str, byID=False):
    data = ast.literal_eval(raw_query_str)
    query_dict = {}
    query_lst = []
    if not byID:
        for idx, val in enumerate(data):
            val['Record']['msgText'] = ' '.join(val['Record']['msgText'].split('__'))
            if 'owner' in val['Record']:
                query_dict[int(val['Key'])] = val['Record']['msgText'] + " " + val['Record']['owner']
            else:
                query_dict[int(val['Key'])] = val['Record']['msgText']
        od = collections.OrderedDict(sorted(query_dict.items()))
        for k, v in od.items():
            query_lst.append(str(k) + " " + v)
        query_lst.reverse()
    else:
        if 'owner' in data:
            msg = ' '.join(data['msgText'].split('__')) + " " + data['owner']
        else:
            msg = ' '.join(data['msgText'].split('__'))
        query_lst.append(msg)

    return query_lst
