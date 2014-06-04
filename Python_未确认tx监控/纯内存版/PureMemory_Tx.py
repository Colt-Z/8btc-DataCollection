import time
from authproxy import AuthServiceProxy, JSONRPCException
from geventwebsocket import WebSocketServer, WebSocketApplication, Resource
import traceback

#para for connect to the bitcoind
BCAccount = "root"
BCpassword = "911123"
host='127.0.0.1'
#running set up vari
connection = AuthServiceProxy("http://" + BCAccount + ":" + BCpassword + "@" + host + ":8332/")
looptime = 5
CurrentBlock = 0
ShortTxInfo = {}
FullTxInfo = {}
AddressRefference = {}
#variable for json return
inval = 0
outval = 0




def GetSenderDetail(hash, index, script):
    global inval
    result = {}
    tx = connection.getrawtransaction(hash, 1)["vout"][index]
    inval += tx["value"]
    result["addr"] = tx["scriptPubKey"]["addresses"][0]
    result["amount"] = str(tx["value"])
    result["prev_output"] = hash
    result["script"] = script
    return result

def GetVoutDetail(input):
    global outval
    result = {}
    outval += input["value"]
    result["addr"] = input["scriptPubKey"]["addresses"][0]
    result["amount"] = str(input["value"])
    result["redeemed_input"] = "Not yet redeemed"
    result["script"] = input["scriptPubKey"]["asm"]
    return result

def SetAddressRefference(address, hash):
    if not(address in AddressRefference.keys()):
        AddressRefference[address] = [hash]      
    if not(hash in AddressRefference[address]):
        AddressRefference[address].append(hash)   
    return


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
            index = GetSenderDetail(vin["txid"], vin["vout"], vin["scriptSig"]["asm"])
            input.append(index)
            SetAddressRefference(index["addr"], hash)

        for vout in tx["vout"]:
            index = GetVoutDetail(vout)
            output.append(index)
            SetAddressRefference(index["addr"], hash)
        
        result["block_height"] = -1
        result["fee"] = inval - outval
        result["hash"] = hash
        result["inputs"] = input
        result["outputs"] = output
        result["size"] = len(tx["hex"])/2
        result["tx_time"] = time.time()
        result["total_input"] = str(inval)
        result["total_output"] = outval
    except:
        print("error on: " + hash)
        traceback.print_exc()
        result["error"] = "can't find this transaction"
    
    return result

def DeletedAddressPointer(inputs, tx):
    for input in inputs:
        addr = input["addr"]
        if (addr in AddressRefference.keys() and tx in AddressRefference[addr]):
            AddressRefference[addr].remove(tx)
            if (len(AddressRefference[addr]) == 0):
                del AddressRefference[addr]
    return


def DeletedConforedTx():
    hash = connection.getblockhash(CurrentBlock)
    txs = connection. getblock(hash)["tx"]
    
    for tx in txs:
        if (tx in ShortTxInfo):
            del ShortTxInfo[tx]
            DeletedAddressPointer(FullTxInfo[tx]["inputs"], tx)
            DeletedAddressPointer(FullTxInfo[tx]["outputs"], tx)
            del FullTxInfo[tx]
    return


#check for set up the DBNoReduence list
def CheckDBNoReduence(height):
    global CurrentBlock
    global dataindex
    global ShortTxInfo
    if CurrentBlock < height:
        CurrentBlock = height  
        DeletedConforedTx()
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
    height = connection.getblockcount() 
    CheckDBNoReduence(height)

    for transaction in transactions:
        if not(transaction in ShortTxInfo):
            ShortTxInfo[transaction] = GetTXdetail(transaction)
            FullTxInfo[transaction] = GetJsonTx(transaction)
    return
    

#call it to run 
def watcher():
    while True:
        try:
            TXListen()
        except JSONRPCException:
            pass   
        time.sleep(looptime)
    return




class EchoApplication(WebSocketApplication):
    def on_open(self):
        print ("Connection opened")

    def on_message(self, message):
        self.ws.send(message)

    def on_close(self, reason):
        print (reason)

WebSocketServer(('', 8000),Resource({'/': EchoApplication})).serve_forever()




