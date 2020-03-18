import collections
import smtplib


def write_file(file_name, string):
    with open(file_name, 'w+') as f:
        f.write(string)


def read_file(file_name):
    with open(file_name) as f:
        content = f.readlines()
    content = [x.strip() for x in content]
    return content


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
    data = raw_query_str
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
