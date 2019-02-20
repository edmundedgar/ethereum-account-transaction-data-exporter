import json
import datetime
import requests
import parsedatetime 
from decimal import *

ETH_TO_WEI = 1000000000000000000
eth_jpy = {}

def init():
    load_jpy_data()
    process_accounts()

def process_accounts():

    with open('accounts.json') as json_data:
        accounts = json.load(json_data)

    aliases = {}
    with open('aliases.json') as json_data:
        aliases_raw = json.load(json_data)

    for a in aliases_raw:
        aliases[a.lower()] = aliases_raw[a]

    print(",".join(["tsstr", "txid", "fromacc", "fromacctype", "toacc", "toacctype", "val", "txcost", "exchange_rate", "txtype", "txcostjpy", "valjpy"]))

    for acc in accounts:
        # print (acc, accounts[acc])
        handle_account(acc, aliases)

def handle_account(acc, aliases):

    url = 'http://api.etherscan.io/api'
    params = {
        'module': 'account',
        'action': 'txlist',
        'address': acc,
        'startblock': 0,
        'endblock': 99999999,
        'sort': 'asc',
        'apikey': 'YourApiKeyToken'
    }
    resp = requests.get(url=url, params=params)
    data = resp.json() # Check the JSON Response Content documentation below
    for d in data['result']:
        crunch_result(d, aliases)

    params['action'] = 'txlistinternal'
    resp = requests.get(url=url, params=params)
    data = resp.json() # Check the JSON Response Content documentation below
    if data is None:
        return

    for d in data['result']:
        crunch_result(d, aliases)

def crunch_result(d, aliases):
    
    if 'cumulativeGasUsed' in d:
        txcost = Decimal(d['cumulativeGasUsed']) * Decimal(d['gasPrice'])
        txtype = 'external'
    else:
        txcost = Decimal(0)
        txtype = 'internal'
    toacc = d['to']
    fromacc = d['from']

    toacctype = 'UNKNOWN'
    if toacc.lower() in aliases:
        toacctype = aliases[toacc.lower()]

    fromacctype = 'UNKNOWN'
    if fromacc.lower() in aliases:
        fromacctype = aliases[fromacc.lower()]

    val = Decimal(d['value'])
    ts = d['timeStamp']
    tsval = datetime.datetime.fromtimestamp(int(ts))
    tsstr = tsval.strftime('%Y%m%d %H:%M:%S')
    tsdtstr = tsval.strftime('%Y%m%d')
    txid = d['hash']
    if tsdtstr not in eth_jpy:
        # Not in the date span we're interested in
        return
    exchange_rate = eth_jpy[tsdtstr]
    txcostjpy = (txcost * exchange_rate) / ETH_TO_WEI
    valjpy = (val * exchange_rate) / ETH_TO_WEI
    print(",".join([tsstr, txid, fromacc, fromacctype, toacc, toacctype, str(val), str(txcost), str(exchange_rate), txtype, str(txcostjpy), str(valjpy)]))


def load_jpy_data():
    f = open('ethjpy/cmc.txt', 'r')
    cal = parsedatetime.Calendar()
    for line in f:
        line = line.replace("\n","")
        bits = line.split("    ")
        if (len(bits) < 2):
            #print("skipping line", line)
            continue
        dthuman = bits[0]
        rt = bits[1].split(" ")[0].replace(",","")
        dt = cal.parseDT(dthuman)
        dtstr = dt[0].strftime('%Y%m%d')
        eth_jpy[dtstr] = Decimal(rt)

init()
