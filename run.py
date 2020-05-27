from slack import RTMClient
from siaskynet import Skynet
import asyncio
import os
import re
import requests


MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
acceptable_commands = ["upload"]

def upload_file(filename, options):
    skylink = "https://siasky.net/" + upload_file_request(filename, options).json()["skylink"]
    return skylink

def upload_file_request(filename, opts=None):
    if opts is None:
        opts = Skynet.default_upload_options()

    host = opts.portal_url
    path = opts.portal_upload_path
    url = f'{host}/{path}'

    res = requests.get(filename)
    filename = opts.custom_filename if opts.custom_filename else os.path.basename(filename.split("/")[-1])
    f = open(filename, "w+")
    f.write(res.text)
    f.close()
    f = open(filename, "rb")
    r = requests.post(url, files={opts.portal_file_fieldname: (filename, f)})
    return r

@RTMClient.run_on(event="message")
def handle_message(**payload):
    data = payload['data']
    web_client = payload['web_client']
    rtm_client = payload['rtm_client']
    text = None
    if 'text' in data:
        channel_id = data['channel']
        thread_ts = data['ts']
        user = data['user']
        text = data.get('text', [])
        match =  re.match(MENTION_REGEX, text)
        if match:
            user_id, message = match.groups()
            message = message.strip(" ")
        else:
            message = text
        
        message = message.replace(u'\xa0', u' ')
        split_message = message.split(" ")
        command = split_message.pop(0)
        files = split_message

        files_options = {
        "token": os.environ['SLACK_BOT_TOKEN'],
        "channel": channel_id,
        "user": user,
        }


        #res = requests.get('https://slack.com/api/files.list', files_options)
        #print(res.text)
        res = requests.get(files[0][1:-1])

        if command in acceptable_commands:
            options = Skynet.default_upload_options()
            #for filename in files:
            filename = files[0][1:-1]
            skylink = upload_file(filename, options)
            response = web_client.chat_postMessage(
                    channel=channel_id,
                    text=str(skylink),
                    thread_ts=thread_ts
                    )
        

if __name__ == "__main__":

    client = RTMClient(token=os.environ["SLACK_BOT_TOKEN"])
    client.start()
