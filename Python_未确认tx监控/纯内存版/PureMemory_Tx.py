import json
import time
from authproxy import AuthServiceProxy, JSONRPCException

#para for connect to the bitcoind
BCAccount = "root"
BCpassword = "911123"
host='127.0.0.1'
#running set up vari
connection = AuthServiceProxy("http://" + BCAccount + ":" + BCpassword + "@" + host + ":8332/")
looptime = 5
CurrentBlock = 0
MemoryData = {}
#variable for json return
inval = 0
outval = 0



def GetSenderDetail(hash, index, script):
    global inval
    result = {}
    tx = connection.getrawtransaction(hash, 1)["vout"][index]
    inval += tx["value"]
    result["addr"] = tx["scriptPubKey"]["addresses"][0]
    result["amount"] = tx["value"]
    result["prev_output"] = hash
    result["script"] = script
    return result

def GetVoutDetail(input):
    global outval
    result = {}
    outval += input["value"]
    result["addr"] = input["scriptPubKey"]["addresses"][0]
    result["amount"] = input["value"]
    result["redeemed_input"] = "Not yet redeemed"
    result["script"] = input["scriptPubKey"]["asm"]
    return result


def GetJsonTx(hash):
        
    result = {}
    input = []
    output = []
    global inval
    global outval
    inval = 0
    outval = 0
        
    try:
        tx = connection.getrawtransaction(hash, 1)
  
        for vin in tx["vin"]:
            input.append(GetSenderDetail(vin["txid"], vin["vout"], vin["scriptSig"]["asm"]))
        
        for vout in tx["vout"]:
            output.append(GetVoutDetail(vout))
    
    
        result["block_height"] = -1
        result["fee"] = inval - outval
        result["hash"] = hash
        result["inputs"] = input
        result["outputs"] = output
        result["size"] = len(tx["hex"])/2
        result["tx_time"] = time.time()
        result["total_input"] = inval
        result["total_output"] = outval
    except:
        print("error on: " + hash)
        result["error"] = "can't find this transaction"
    
    return result


#check for set up the DBNoReduence list
def CheckDBNoReduence(height):
    global CurrentBlock
    global dataindex
    global MemoryData
    if CurrentBlock < height:
        CurrentBlock = height  
        MemoryData ={}  
    return


#decode the tx, then push the detail in a dict form
def GetTXdetail(hash):
    tx = connection.getrawtransaction(hash, 1)["vout"]  
    OutValue = 0
    #delete the useless data to reduce the memory usage
    for vout in tx:
        OutValue += vout["value"]  
    return [OutValue, time.time()]



#main function for program, get the blocktemp from bitcoind, then check wheather this hash already
#existed, if yes then do nothing, else push it into memory database.
def TXListen():
    transactions = connection.getrawmempool()
    height = connection.getblockcount() + 1
    CheckDBNoReduence(height)

    for transaction in transactions:
        if not(transaction in MemoryData):
            MemoryData[transaction] = GetTXdetail(transaction)
    return
    

#call it to run 
def run():
    while True:
        try:
            TXListen()
        except JSONRPCException:
            pass
    
        time.sleep(looptime)
    return


run()
