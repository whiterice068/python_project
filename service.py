import yfinance as yf
import pandas as pd
import numpy as np
import sqlite3 
import time
import json
from io import StringIO


def df_to_json(df):
    data = df.to_json()
    return data

def dict_to_json(dictio):
    data = json.dumps(dictio)
    return data

def read_df(json_df):
    data = pd.read_json(StringIO(json_df))
    return data

def read_dict(json_dictio):
    data = json.loads(json_dictio)
    return data

def cache(get_function, symbol:str, to_json, read_json, data_type:str, *args:str, expire:int=3600):

    conn = sqlite3.connect("service.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    period = args[0] if args else None

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_data(
        symbol TEXT,
        data TEXT,
        period TEXT DEFAULT NULL,
        cached_at INTEGER,
        expire INTEGER,
        data_type TEXT,
        UNIQUE (symbol, period, data_type)
        )
        """)
    
    if period is not None:
        select_record = ("SELECT * from stock_data WHERE symbol = ? AND period = ? AND data_type = ?")
        record = cursor.execute(select_record, (symbol, period, data_type))

    else:
        select_record = ("SELECT * from stock_data WHERE symbol = ? AND period IS NULL AND data_type = ?")
        record = cursor.execute(select_record, (symbol, data_type))
    
    record_data = record.fetchone()

    if not record_data or (time.time() - record_data["cached_at"]) >= record_data["expire"]:

        upsert = ("""
                INSERT INTO stock_data (symbol, data, period, cached_at, expire, data_type)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, period, data_type)
                DO UPDATE SET data = EXCLUDED.data, cached_at = EXCLUDED.cached_at
                """)
        
        fetch_data = get_function(symbol, *args)

        if fetch_data.get("success") == True:

            data = fetch_data.get("data")
            json_data = to_json(data)

            cursor.execute(upsert, (symbol, json_data, period, time.time(), expire, data_type))
            conn.commit()

            cursor.close()
            conn.close()

            return {"success":True, "data":data, "message":fetch_data.get("message")}

        else:

            cursor.close()
            conn.close()
            return {"success":False, "data":None, "message":fetch_data.get("message")}


    else:

        json_data = record_data["data"]
        data = read_json(json_data)
        cursor.close()
        conn.close()

        return {"success":True, "data":data, "message":"Successfully fetched cached data"}


    
def get_stock_history(ticker_symbol, period="1y", interval="1d"):

    if ticker_symbol:
        ticker = yf.Ticker(ticker_symbol.upper()) # 拿到ticker对象，将股票参数转换为大写.upper()

        try: # 防止网络波动，爬取失败

            history = ticker.history(period=period, interval=interval)
            frmt_index = history.index.tz_localize(None)
            history.index = frmt_index

            if history.empty: # 判断DataFrame是否为空
                return {"success":False, "data":None, "message":f"Fail to fetch stock history for {ticker_symbol}"}
            
            return {"success":True, "data":history, "message":f"Successfully fetched stock history for {ticker_symbol}"}
            
        except Exception as e:
            return {"success":False, "data":None, "message":f"Fail to fetch stock history for {ticker_symbol},error:{e}"}
        
    else:
        return {"success":False, "data":None, "message":f"Ticker symbol is Empty"}


def get_stock_history_cached(ticker_symbol, data_period="1y"):
    symbol = ticker_symbol
    period = data_period
    cached_data = cache(get_stock_history, symbol, df_to_json, read_df, "history", period)
    return cached_data


def get_stock_info(ticker_symbol):

    if ticker_symbol:

        ticker = yf.Ticker(ticker_symbol.upper())

        try:
            info = ticker.info # 拿到ticker对象的info

            # 如果info中的 “symbol” key 为空或不等于传入的参数，返回失败
            if info.get('symbol') is None:
                return {"success":False, "data":None, "message":f"Fail to fetch stock info for {ticker_symbol}"}
            
            if info.get('symbol').upper() != ticker_symbol.upper():
                return {"success":False, "data":None, "message":f"Fail to fetch stock info for {ticker_symbol}"}
            
            else:
                return {"success":True, "data":info, "message":f"Successfully fetched stock info for {ticker_symbol}"}
            
            
        except Exception as e:
            
            return {"success":False, "data":None, "message":f"Fail to fetch stock info for {ticker_symbol},error:{e}"}

    else:
        return {"success":False, "data":None, "message":f"Ticker Symbol is Empty"}

        
def get_stock_info_cached(ticker_symbol):
    symbol = ticker_symbol
    cached_data = cache(get_stock_info, symbol, dict_to_json, read_dict, "info")
    return cached_data


def get_stock_financial_info(ticker_symbol):

    stock_info = get_stock_info_cached(ticker_symbol)
    stock_data = stock_info.get("data")
    if stock_data:
   
        keys = [
        "marketCap", "nonDilutedMarketCap", "enterpriseValue", "totalRevenue", 
        "revenuePerShare", "revenueGrowth", "grossProfits", "grossMargins", 
        "ebitda", "ebitdaMargins", "operatingMargins", "profitMargins", 
        "netIncomeToCommon", "earningsGrowth", "earningsQuarterlyGrowth", 
        "trailingPE", "forwardPE", "pegRatio", "priceToSalesTrailing12Months", 
        "priceToBook", "bookValue", "enterpriseToRevenue", "enterpriseToEbitda", 
        "trailingEps", "forwardEps", "devidendYield", "devidendRate",
        "epsCurrentYear", "priceEpsCurrentYear", "returnOnAssets", "returnOnEquity", 
        "totalCash", "totalCashPerShare", "totalDebt", "debtToEquity", 
        "quickRatio", "currentRatio", "freeCashflow", "operatingCashflow"
        ]

        stock_financial_info = {k: stock_data.get(k) for k in keys} # 用列表推导式拿到 key ：value

        return {"success":True, "data":stock_financial_info, "message":f"Successfully fetched stock info for {ticker_symbol}"}

    else:

        return {"success":False, "data":None, "message":f"Fail to fetch stock info for {ticker_symbol}"}
       
    
def ma(stock_data):

    copy_history_data = stock_data.copy() # 复制一份数据，防止污染数据

    ma20 = copy_history_data["Close"].rolling(window=20).mean() # rolling（20) 计算每个 close 前 20 天的平均值
    ma20_df = pd.DataFrame({"Date":copy_history_data.index, "Close":copy_history_data.get("Close"), "MA20":ma20})

    return ma20_df


def rsi(stock_data):

    copy_history_data = stock_data.copy()

    close = copy_history_data["Close"]
    diff = close.diff()

    gain = diff.where(diff > 0)
    gain.fillna(0, inplace=True)

    loss = abs(diff.where(diff < 0))
    loss.fillna(0, inplace=True)

    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()

    conditions = [((avg_gain == 0) & (avg_loss == 0)),
                    ((avg_gain == 0) & (avg_loss > 0)),
                    ((avg_gain > 0) & (avg_loss == 0))
                    ]

    choices = [50,0,100]

    normal_rsi = 100 - (100 / (1 + (avg_gain / avg_loss)))

    rsi = np.select(conditions, choices, default=normal_rsi)
    

    rsi_df = pd.DataFrame({"Date":copy_history_data.index, "close":close, "diff":diff, "gain":gain,"loss":loss, "avg_gain":avg_gain, "avg_loss":avg_loss, "14 days RSI":rsi})

    return rsi_df


def macd(stock_data):

    copy_history_data = stock_data.copy()
    close = copy_history_data["Close"]

    macd_line = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    color = histogram.apply(lambda x :"positive" if x > 0 else "negative") 

    macd_df = pd.DataFrame({"Date":copy_history_data.index, "close":close, "macd_line":macd_line, "signal_line":signal_line,"histogram":histogram, "color":color})

    return macd_df
       
def boll(stock_data):

    copy_history_data = stock_data.copy()
    close = copy_history_data["Close"]

    middle_band = close.rolling(window=20).mean()
    stdev = close.rolling(window=20).std(ddof=0)
    upper_band = middle_band + stdev * 2
    lower_band = middle_band - stdev * 2

    boll_df = pd.DataFrame({"Date":copy_history_data.index, "close":close, "middle_band":middle_band, "upper_band":upper_band,"lower_band":lower_band})

    return boll_df


def compare_stocks(*args: str, period="1y"):

    all_series = []
    invalid_stock = []

    for stock in args:
        stock_history = get_stock_history_cached(stock, data_period=period)

        if stock_history.get("success") == True:

            stock_data = stock_history.get("data")
            copy_history_data = stock_data.copy()

            close_series = pd.Series(copy_history_data["Close"], name=stock.upper())
                        
            all_series.append(close_series)
            
        else:
            invalid_stock.append(stock)

    if all_series:
        all_stock_df = pd.concat(all_series, axis=1, join="inner")

    else:
        return {"success":False, "data":None, "message":f"Invalid stock / stock was not entered"}

    print(all_stock_df)

    all_stock_df = (all_stock_df / all_stock_df.iloc[0]) * 100

    if invalid_stock:
        return {"success":True, "data":all_stock_df, "message":f"Some of the stocks are invalid. Invalid stocks : {invalid_stock}"}

    else:
        return {"success":True, "data":all_stock_df, "message":f"Successfully calculated stocks percentage change"}









        

            

    











        


        


