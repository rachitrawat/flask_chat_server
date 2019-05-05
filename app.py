import getpass
import json
import os
import random
import string
import subprocess

from flask import Flask, render_template, request

import utils

app = Flask(__name__)

db_path = "/home/r/PycharmProjects/flask_chat_server/client_db.json"
user_dict = {}
available_wallets = [x for x in range(1, 10000)]
if os.path.isfile(db_path):
    db_content = utils.read_file(db_path)[0]
    user_dict = json.loads(db_content)
    used_wallets = []
    # update available wallets
    for k, v in user_dict.items():
        used_wallets.append(int(v["wallet"][4:]))
    available_wallets = list(set(available_wallets) - set(used_wallets))
else:
    utils.write_file(db_path, "{}")

FABRIC_DIR = "/home/" + getpass.getuser() + "/WebstormProjects/hyperledger_project/fabchat/javascript/"
NODE_PATH = "/home/" + getpass.getuser() + "/node/bin/node"
DEBUG = False


def handle_setup(req_obj, flag):
    uid = req_obj['email']

    # registration
    if flag == "True":
        # if user already exists, fail
        # if no more wallets available, fail
        if uid in user_dict or not available_wallets:
            utils.send_verification_email(uid, user_dict[uid]['pwd'])
            return 1
        # else assign user with a wallet
        else:
            pwd = ''.join(
                random.SystemRandom().choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in
                range(4))
            utils.send_verification_email(uid, pwd)
            wallet_id = random.choice(available_wallets)
            available_wallets.remove(wallet_id)
            user_dict[uid] = {"pwd": pwd, "wallet": "user" + str(wallet_id)}
            # initial registration msg
            tmp_dict = {}
            tmp_dict['email'] = uid
            tmp_dict['msgtext'] = "$HELLO$"
            if registerUser(user_dict[uid]['wallet']) != 0 or createMsg(tmp_dict) != 0:
                user_dict.pop(uid)
                available_wallets.append(wallet_id)
                return 1
            utils.write_file(db_path, json.dumps(user_dict))
            return 0
    # login
    elif flag == "False":
        pwd = req_obj['pwd']
        # if user does not exist or pwd does not match, fail
        if uid not in user_dict or pwd != user_dict[uid]["pwd"]:
            return 1
        else:
            # if user exists and pwd matches, pass
            if pwd == user_dict[uid]["pwd"]:
                return 0
            # if user exists and pwd does not match, fail
            else:
                return 1


def registerUser(user):
    output = "dummy"

    try:
        output = subprocess.check_output(
            [NODE_PATH, FABRIC_DIR + "registerUser.js", user]).decode(
            'ascii').split()

    except:
        pass

    if DEBUG:
        print(' '.join(output))

    if output[len(output) - 1] == "wallet":
        return 0
    else:
        return 1


def createMsg(req_obj):
    user = req_obj['email']
    msgText = req_obj['msgtext']
    msgText = '__'.join(msgText.split())
    output = "dummy"

    try:
        output = subprocess.check_output(
            [NODE_PATH, FABRIC_DIR + "invoke.js", "createMsg", msgText, user_dict[user]["wallet"], user]).decode(
            'ascii').split()
    except:
        pass

    if DEBUG:
        print(' '.join(output))

    if output[len(output) - 1] == "submitted":
        return 0
    else:
        return 1


def flagMsg(req_obj):
    msgID = req_obj['msgID']
    user = req_obj['email']
    output = "dummy"

    try:
        output = subprocess.check_output(
            [NODE_PATH, FABRIC_DIR + "invoke.js", "flagMsg", msgID, user_dict[user]["wallet"]]).decode(
            'ascii').split()
    except:
        pass

    if DEBUG:
        print(' '.join(output))

    if output[len(output) - 1] == "submitted":
        return 0
    else:
        return 1


def queryAllMsgs(req_obj, byID=False):
    if not byID:
        msgID = "-1"
    else:
        msgID = req_obj['msgID']

    user = req_obj['email']
    output = "dummy"

    try:
        output = subprocess.check_output(
            [NODE_PATH, FABRIC_DIR + "query.js", msgID, user_dict[user]["wallet"]]).decode(
            'ascii').split()
    except:
        pass

    if DEBUG:
        print(' '.join(output))

    if output != "dummy" and output[6] == "evaluated,":
        return 0, json.loads(output[len(output) - 1])
    else:
        return 1, " "


@app.route('/')
def home():
    return render_template('home.html', numUsers=len(user_dict))


@app.route('/', methods=['POST'])
def home_post():
    res = handle_setup(request.form, "False")
    if res == 0:
        if request.form['submit_button'] == 'Post Message':
            if res == 0:
                createMsg(request.form)
                return render_template('response.html', response="Message posted successfully!")
            else:
                return render_template('response.html', response="Failed to post message!")
        elif request.form['submit_button'] == 'See All Messages':
            res, raw_query_str = queryAllMsgs(request.form)
            if res == 0:
                query_lst = utils.format_query(raw_query_str)
                return render_template('show_query.html', query_lst=query_lst)
            else:
                return render_template('response.html', response="Failed to query messages!")
        elif request.form['submit_button'] == 'Flag Message':
            res = flagMsg(request.form)
            if res == 0:
                return render_template('response.html', response="Message flagged successfully!")
            else:
                return render_template('response.html', response="Failed to flag message!")
        elif request.form['submit_button'] == 'Query Message':
            res, raw_query_str = queryAllMsgs(request.form, True)
            if res == 0:
                query_lst = utils.format_query(raw_query_str, True)
                return render_template('show_query.html', query_lst=query_lst)
            else:
                return render_template('response.html', response="Failed to query message!")
    else:
        return render_template('response.html', response="Invalid email/password!")


@app.route('/register', methods=['POST'])
def register_post():
    res = handle_setup(request.form, "True")
    if res == 0:
        return render_template('response_success.html',
                               response="Registration successful! Check your email inbox/spam for password.")
    else:
        return render_template('response.html',
                               response="Registration failed! You're already registered. Check your email's inbox/spam folder for password.")


@app.route('/register')
def register():
    return render_template('register.html')


if __name__ == '__main__':
    app.run()
