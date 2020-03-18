import getpass
import json
import os
import random
import string
import subprocess

import flask_login
from flask import Flask, request, redirect
from flask import render_template
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin

import utils

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = ''
app.config['SECRET_KEY'] = "lkkajdghdadkglajkgah"

db_path = "/home/r/PycharmProjects/fabchat_flask_server/client_db.json"
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

FABRIC_DIR = "/home/" + getpass.getuser() + "/FabricProjects/fabchat/fabchat/javascript/"
NODE_PATH = "/usr/local/lib/node/bin/node"
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
                random.SystemRandom().choice(string.digits) for _ in
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


def registerUser(user):
    output = "dummy"

    try:
        output = subprocess.check_output(
            [NODE_PATH, FABRIC_DIR + "registerUser.js", user]).decode().split()
    except:
        pass

    if DEBUG:
        print(' '.join(output))

    if output != "dummy" and output[len(output) - 1] == "wallet":
        return 0
    else:
        return 1


def createMsg(req_obj):
    user = req_obj['email']
    msgText = req_obj['msgtext']
    msgText = ''.join([i if ord(i) < 128 else ' ' for i in msgText])
    msgText = '__'.join(msgText.split())
    output = "dummy"

    try:
        output = subprocess.check_output(
            [NODE_PATH, FABRIC_DIR + "invoke.js", "createMsg", msgText, user_dict[user]["wallet"],
             user]).decode().split()
    except:
        pass

    if DEBUG:
        print(' '.join(output))

    if output != "dummy" and output[len(output) - 1] == "submitted":
        return 0
    else:
        return 1


def flagMsg(req_obj):
    msgID = req_obj['msgID']
    user = req_obj['email']
    output = "dummy"

    try:
        output = subprocess.check_output(
            [NODE_PATH, FABRIC_DIR + "invoke.js", "flagMsg", msgID, user_dict[user]["wallet"]]).decode().split()
    except:
        pass

    if DEBUG:
        print(' '.join(output))

    if output != "dummy" and output[len(output) - 1] == "submitted":
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
            [NODE_PATH, FABRIC_DIR + "query.js", msgID, user_dict[user]["wallet"]]).decode().split()
    except:
        pass

    if DEBUG:
        print(' '.join(output))

    if output != "dummy" and output[6] == "evaluated,":
        return 0, json.loads(output[len(output) - 1])
    else:
        return 1, " "


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


class User(UserMixin):
    def __init__(self, id):
        self.id = id


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/', methods=['POST'])
def home_post():
    if request.form['email'] in user_dict and user_dict[request.form['email']]['pwd'] == request.form['pwd']:
        login_user(User(request.form['email']))
        return redirect('/dashboard')
    else:
        return render_template('response.html', response="Invalid email/password!")


@app.route('/dashboard/')
@login_required
def dashboard():
    return render_template('dashboard.html', numUsers=len(user_dict))


@app.route('/dashboard/', methods=['POST'])
@login_required
def dashboard_post():
    req_dict = {}
    req_dict['email'] = flask_login.current_user.id
    if request.form['submit_button'] == 'Post Message':
        req_dict['msgtext'] = request.form['msgtext']
        if createMsg(req_dict) == 0:
            return render_template('response.html', response="Message posted successfully!")
        else:
            return render_template('response.html', response="Failed to post message!")
    elif request.form['submit_button'] == 'See All Messages':
        res, raw_query_str = queryAllMsgs(req_dict)
        if res == 0:
            query_lst = utils.format_query(raw_query_str)
            return render_template('show_query.html', query_lst=query_lst)
        else:
            return render_template('response.html', response="Failed to query messages!")
    elif request.form['submit_button'] == 'Flag Message':
        req_dict['msgID'] = request.form['msgID']
        if flagMsg(req_dict) == 0:
            return render_template('response.html', response="Message flagged successfully!")
        else:
            return render_template('response.html',
                                   response="Failed to flag message! Are you entering a valid message ID?")
    elif request.form['submit_button'] == 'Query Message':
        req_dict['msgID'] = request.form['msgID']
        res, raw_query_str = queryAllMsgs(req_dict, True)
        if res == 0:
            query_lst = utils.format_query(raw_query_str, True)
            return render_template('show_query.html', query_lst=query_lst)
        else:
            return render_template('response.html',
                                   response="Failed to query message! Are you entering a valid message ID?")


@app.route('/register', methods=['POST'])
def register_post():
    res = handle_setup(request.form, "True")
    if res == 0:
        return render_template('response_home.html',
                               response="Registration successful! Check your email inbox/spam for password.")
    else:
        return render_template('response_home.html',
                               response="Registration failed! You're already registered. Check your email's inbox/spam folder for password.")


@app.route('/register')
def register():
    return render_template('register.html')


if __name__ == '__main__':
    app.run()
