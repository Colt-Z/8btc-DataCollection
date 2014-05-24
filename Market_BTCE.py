import json
import time
import urllib.request
import mysql.connector  # @UnresolvedImport


# setup variable
btce = ["https://btc-e.com/api/2/btc_usd/ticker", "vol_cur", 0];
bitstamp = ["https://www.bitstamp.net/api/ticker/", "volume", 0];
okcoin = ["https://www.okcoin.com/api/ticker.do", "vol" , 1];
huobi = ["http://market.huobi.com/staticmarket/ticker_btc_json.js", "vol", 1];
btcchina = ["https://data.btcchina.com/data/ticker?market=btccny", "vol", 1];
Type = ["BTC_USD", "BTC_CND"];
#var for different setting
looptime = 30
PushRound = 10
DBAccount = "root"
DBpassword = "911123"
DBIP = '127.0.0.1'
DBname = 'test';

#elements for memory cache
Stackbtce = []
Stackbitstamp = []
Stackokcoin = []
Stackhuobi = []
Stackbtcchina = []


#fix lenght for make sure use time as PK in database is easy for search 
def TimeLengthFix(input):
    if len(input) < 2:
        input= "0" + input
    return input

#function for get time, also the prime key of the table
def MyTime():
    now = time.localtime()
    #trans the local time to number, use this as primekey. 
    #this code may cause error if the time in the service be changed
    return int(str(now.tm_year) + TimeLengthFix(str(now.tm_mon)) + TimeLengthFix(str(now.tm_mday)) \
        + TimeLengthFix(str(now.tm_hour)) + TimeLengthFix(str(now.tm_min)) + TimeLengthFix(str(now.tm_sec)))

# function for read the data from json formate
def MyMarketVal(inputs):
    #read from website and put into json
    
    input = urllib.request.urlopen(inputs[0]).read()
    input = json.loads(input.decode('utf-8'))
    #in case of didffernt formate, switch to same
    if 'ticker' in input:
        input = input['ticker']
    #get data of high, low and last
    high = input['high']
    low = input['low']
    last = input['last']
    vol = input[inputs[1]]
    return [MyTime(),high,low ,last,  vol, Type[inputs[2]]]

#Main function for data collection
def IRData():
    try:  
        Stackbtce.append(MyMarketVal(btce))
    except:
        pass
    
    try:
        Stackbitstamp.append(MyMarketVal(bitstamp))
    except:
        pass
    
    try:    
        Stackokcoin.append(MyMarketVal(okcoin))
    except:
        pass
    
    try:
        Stackbtcchina.append(MyMarketVal(btcchina))
    except:
        pass
    
    try:
        Stackhuobi.append(MyMarketVal(huobi))
    except:
        pass
    
    return

#singal table push
def DBsave(DBcur, tablename, stack):
    while len(stack) > 0:
        val = str(stack.pop())[1:-1]
        DBcur.execute("INSERT INTO " + tablename + " value ("  + val + ")");
    
    return

#push data from memory to DB
def DBsaves():
    DB = mysql.connector.connect(user=DBAccount, password=DBpassword,host=DBIP,database=DBname)
    DBcur = DB.cursor()
    DBsave(DBcur,"market_btce",Stackbtce)
    DBsave(DBcur,"market_bitstamp",Stackbitstamp)
    DBsave(DBcur,"market_okcoin",Stackokcoin)
    DBsave(DBcur,"market_huobi",Stackhuobi)
    DBsave(DBcur,"market_btcchina",Stackbtcchina)
    DB.commit()
    return

def run():
    count = 0
    while True:
        IRData()
        count += 1
        if count == PushRound:
            DBsaves()
            count = 0
        time.sleep(looptime)
    return

run()

