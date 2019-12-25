import requests
import json
import threading

NODE_URL = "http://127.0.0.1:13786"  # Enter port number for coins rpc port
NODE_USER = "user"
NODE_PASSWORD = "password"

# Makes rpc connection


def rpc(method, params=[]):
    payload = json.dumps({
        "jsonrpc": "1.0",
        "method": method,
        "params": params,
    })
    response = requests.post(NODE_URL,
                             auth=(NODE_USER, NODE_PASSWORD),
                             data=payload).json()
    return response


# Gets a new address


def getAddress():
    WalletResponse = rpc('getnewaddress')
    print(WalletResponse)
    return WalletResponse


def getMasternodes():
    WalletResponse = rpc('getinfo')
    return WalletResponse


def nodeCount():
    WalletResponse = rpc('masternode', ['count'])
    return WalletResponse


# Gets user balance


def getBalance(userId):
    WalletBalance = rpc('getbalance', ["" + userId + ""])
    print(WalletBalance)
    return WalletBalance


# Assigns an address to an account based on discord ID


def getNewAddy(userId):
    NewAddy = rpc('getaccountaddress', ["" + str(userId) + ""])
    print(NewAddy)
    return NewAddy


# Send coins functionality


def sendCoins(uid, toAddress, amount):
    sendTx = rpc('sendfrom', [uid, toAddress, amount])
    # sendTx = rpc('sendfrom', [""+str(uid) + ' ' + str(toAddress) + ' ' + str(amount) + ""])
    # print(sendTx)
    return sendTx


# Gets value of cards for blackjack


def getCardValue(Draw):
    global cardValue
    if Draw.startswith("A"):
        cardValue = 1
    elif Draw.startswith("2"):
        cardValue = 2
    elif Draw.startswith("3"):
        cardValue = 3
    elif Draw.startswith("4"):
        cardValue = 4
    elif Draw.startswith("5"):
        cardValue = 5
    elif Draw.startswith("6"):
        cardValue = 6
    elif Draw.startswith("7"):
        cardValue = 7
    elif Draw.startswith("8"):
        cardValue = 8
    elif Draw.startswith("9"):
        cardValue = 9
    elif Draw.startswith("10"):
        cardValue = 10
    elif Draw.startswith("J"):
        cardValue = 10
    elif Draw.startswith("Q"):
        cardValue = 10
    elif Draw.startswith("K"):
        cardValue = 10
    return cardValue


# Set interval function
