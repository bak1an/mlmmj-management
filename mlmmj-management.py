#!/usr/bin/python

import sys
import smtplib
import email
import subprocess
import re

# smtp for sending reply emails
smtp = smtplib.SMTP("localhost")

# PASSWORD - password for do any action. must be in message subject.
# AUTHORIZED_SENDERS - list of senders, who will be able to send mails for this script.
# SEND_ERRORS - set to False if you don't want recieve error emails from this script
# MLMMJ_SPOOL - path to mlmmj spool
# MLMMJ_BINS - path to mlmmj binaries
# MY_ADDRESS - address from which this script will mail you

PASSWORD = "pass"
AUTHORIZED_SENDERS = ["first@sender.com", "other@sender.com"]
SEND_ERRORS = True
MLMMJ_SPOOL = "/var/spool/mlmmj/"
MLMMJ_BINS = "/usr/bin/"
MY_ADDRESS = "mlmmj-management@localhost"
ALLOWED_ACTIONS = {"sub":(2, MLMMJ_BINS+"mlmmj-sub -L \"%s\" -a \"%s\""), 
                   "unsub":(2, MLMMJ_BINS+"mlmmj-unsub -L \"%s\" -a \"%s\""), 
                   "list":(1, MLMMJ_BINS+"mlmmj-list -L \"%s\"")}

email_re = re.compile(r"[\b<]([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,5})[\b>]")

def prepare_commnad(arguments):
    action = ALLOWED_ACTIONS.get(arguments[0])
    command = "echo \"lol wut?\""
    if len(arguments) != (action[0] + 1):
        raise Exception("wrong number of arguments")
    # there must more 'pythonic' way to do it
    if action[0] == 1:
        command = action[1] % MLMMJ_SPOOL + arguments[1]
    elif action[0] == 2:
        command = action[1] % (MLMMJ_SPOOL + arguments[1], arguments[2])
    return command

def run_command(cmd):
    res = ""
    process = subprocess.Popen(cmd, 
                               shell=True, 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.STDOUT)
    for line in process.stdout:
        res += line
    code = process.wait()
    return "subprocess returned: %s\n\n%s" % (str(code), res)

def process_command(msg):
    try:
        msg_from = msg.get("from", "")
        msg_subj = msg.get("subject", "")
        msg_body = msg.get_payload()
        from_match = email_re.search(msg_from)
        if not from_match or not from_match.group(1) or from_match.group(1) not in AUTHORIZED_SENDERS: 
            return (1, "Hi %s!\nSorry, but you are not authorized to send messages for me." % msg_from)
        if msg_subj != PASSWORD:
            return (1, "Hi! Sorry, but '%s' is not a password. Roll again!" % msg_subj)
        arguments = map(lambda s: str(s).strip(), msg_body.split(";"))
        if arguments[0] not in ALLOWED_ACTIONS.keys():
            return (1, "Hi! I don't know how to run '%s'" % arguments[0])
        command = prepare_commnad(arguments)
        return (0, run_command(command))
    except Exception, e:
        return (1, "There was some error, show it to bak1an: \n\n%s" % e)

raw_data = sys.stdin.readlines()
msg = email.message_from_string(reduce(lambda a,b: a+b, raw_data, ""))

command_result = process_command(msg)

if (command_result[0] != 0 and SEND_ERRORS) or command_result[0] == 0:
    smtp.sendmail(MY_ADDRESS, [msg["from"]], command_result[1])

