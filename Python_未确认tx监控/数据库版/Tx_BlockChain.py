import json
import time
from authproxy import AuthServiceProxy, JSONRPCException
import mysql.connector  # @UnresolvedImport

#para for connect to the bitcoind
BCAccount = "root"
BCpassword = "911123"
host='127.0.0.1'
#para for connect to the database
DBAccount = "root"
DBpassword = "911123"
DBIP = '127.0.0.1'
DBname = 'test'
x = "','"
#running set up vari
looptime = 5
PushRound = 10
CurrentBlock = 0
dataindex = 0
MemoryData = {}
DBNoReduence = []


#check for set up the DBNoReduence list
def CheckDBNoReduence(height):
    global CurrentBlock
    global DBNoReduence
    global dataindex
    if CurrentBlock < height:
        CurrentBlock = height
        DBNoReduence = []   
        clenMemoryData()
        dataindex = 0   
    return

#get sender's address by sent gettx request to bitcoind
def GetSenderAddress(connection, tx, index):
    result = connection.getrawtransaction(tx, 1)
    result = result["vout"][index]["scriptPubKey"]["addresses"]
    return result[0]

#deleted the useless data for vout in tx, to reduce the memory useage
def GetShorterVout(input):
    input["scriptPubKey"] = input["scriptPubKey"]["addresses"][0]
    return input

#decode the tx, then push the detail in a dict form
def GetTXdetail(connection, hash, height):
    tx = connection.getrawtransaction(hash, 1)  
    vinlist = []
    voutlist = []

    #get sender's address from previous transaction
    for vin in tx["vin"]:
        vinlist.append({"address":GetSenderAddress(connection, vin["txid"], vin["vout"]), "fromTx": vin["txid"]})

    #delete the useless data to reduce the memory usage
    for vout in tx["vout"] :
        voutlist.append(GetShorterVout(vout))  
    return {"input":vinlist, "output": voutlist, "height":height}


#main function for program, get the blocktemp from bitcoind, then check wheather this hash already
#existed, if yes then do nothing, else push it into memory database.
def TXListen(connection):
    transactions = connection.getrawmempool()
    height = connection.getblockcount() + 1
    CheckDBNoReduence(height)

    for transaction in transactions:
        if not(transaction in DBNoReduence):
            MemoryData[transaction] = GetTXdetail(connection, transaction, height)
            DBNoReduence.append(transaction)
    return

#called after push memory to database, clen the memory
def clenMemoryData():
    global MemoryData
    MemoryData ={}
    return 
    
#the function that used to push memory to database
def DBsaves():
    DB = mysql.connector.connect(user=DBAccount, password=DBpassword,host=DBIP,database=DBname)
    DBcur = DB.cursor()
    global dataindex
   
    for data in MemoryData:
        dataindex += 1
        thisheigh = str(MemoryData[data]["height"])
        DBcur.execute("INSERT INTO Tx value ('"  + data + x + thisheigh\
               + x + thisheigh + "_" + str(dataindex) + "')")
        
        #push input address to database
        inputindex = 0
        for input in MemoryData[data]["input"]:
            DBcur.execute("INSERT INTO Txin value ('"  + thisheigh + "_" + str(dataindex)
               + x + str(inputindex) + x + input["address"] + x + input["fromTx"] + "')")
            inputindex += 1
            
        #push output address to database   
        for output in MemoryData[data]["output"]:
            DBcur.execute("INSERT INTO Txout value ('"  + thisheigh + "_" + str(dataindex) + x + str(output["n"])\
                   + x + output["scriptPubKey"] + x + str(output["value"]) + "')")
            
    DB.commit()
    clenMemoryData()
    return

#call it to run 
def run():
    count = 0
    connection = AuthServiceProxy("http://" + BCAccount + ":" + BCpassword + "@" + host + ":8332/")
    while True:
        try:
            TXListen(connection)
            count += 1
        except JSONRPCException:
            pass
    
        if count == PushRound:
            DBsaves()
            count = 0
        time.sleep(looptime)
    return



run()
