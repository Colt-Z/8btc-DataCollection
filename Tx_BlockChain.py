import json
import time
from authproxy import AuthServiceProxy, JSONRPCException

#setup variables
BCAccount = "root"
BCpassword = "911123"
host='127.0.0.1'
looptime = 5
PushRound = 5
MemoryData = {}

def GetSenderAddress(connection, tx, index):
    result = connection.getrawtransaction(tx, 1)
    result = result["vout"][index]["scriptPubKey"]["addresses"]
    return result[0]

def GetShorterVout(input):
    input["scriptPubKey"] = input["scriptPubKey"]["addresses"][0]
    return input

def GetTXdetail(connection, data, height):
    tx = connection.decoderawtransaction(data)
    vins = tx["vin"]
    vouts = tx["vout"]    
    vinlist = []
    voutlist = []
    #get sender's address from previous transaction
    for vin in vins:
        vinlist.append(GetSenderAddress(connection, vin["txid"], vin["vout"]))
    #delete the useless data to reduce the memory usage
    for vout in vouts:
        voutlist.append(GetShorterVout(vout))   
    
    return {"input":vinlist, "output": voutlist, "height":height}

def TXListen(connection):
    blocktemp = connection.getblocktemplate()
    transactions = blocktemp["transactions"]
    height = blocktemp["height"]
    
    for transaction in transactions:
        hash = transaction["hash"]
        if not(hash in MemoryData):
            MemoryData[hash] = GetTXdetail(connection, transaction["data"], height)
    return

def DBsaves():
    print(MemoryData)
    return

def run():
    count = 0
    connection = AuthServiceProxy("http://" + BCAccount + ":" + BCpassword + "@" + host + ":8332/")
    while count < 99:
        TXListen(connection)
        count += 1
        time.sleep(looptime)
        if count == PushRound:
            DBsaves()
            count = 0
    return


run()
