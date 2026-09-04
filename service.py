import yfinance as yf
import pandas as pd
import numpy as np
import os
import sqlite3

def get_stock_history(ticker_symbol, period="1y", interval="1d"):
    if ticker_symbol:
        ticker = yf.Ticker(ticker_symbol.upper()) # 拿到ticker对象，将股票参数转换为大写.upper()
        try: # 防止网络波动，爬取失败

            history = ticker.history(period=period,interval=interval)

            if history.empty: # 判断DataFrame是否为空
                return {"success":False, "data":None, "message":f"Fail to fetch stock history for {ticker_symbol}"}
            
            return {"success":True, "data":history, "message":f"Successfully fetched stock history for {ticker_symbol}"}
            
        except Exception as e:
            return {"success":False, "data":None, "message":f"Fail to fetch stock history for {ticker_symbol},error:{e}"}
        
    else:
        return {"success":False, "data":None, "message":f"Ticker symbol is Empty"}

    
    

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
        



def get_stocks_financial_info(ticker_symbol):
    stock_info = get_stock_info(ticker_symbol)
    stock_data = stock_info.get("data")
    if stock_data:
   
        keys = [
        "marketCap", "nonDilutedMarketCap", "enterpriseValue", "totalRevenue", 
        "revenuePerShare", "revenueGrowth", "grossProfits", "grossMargins", 
        "ebitda", "ebitdaMargins", "operatingMargins", "profitMargins", 
        "netIncomeToCommon", "earningsGrowth", "earningsQuarterlyGrowth", 
        "trailingPE", "forwardPE", "pegRatio", "priceToSalesTrailing12Months", 
        "priceToBook", "bookValue", "enterpriseToRevenue", "enterpriseToEbitda", 
        "trailingEps", "forwardEps", "epsTrailingTwelveMonths", "epsForward", 
        "epsCurrentYear", "priceEpsCurrentYear", "returnOnAssets", "returnOnEquity", 
        "totalCash", "totalCashPerShare", "totalDebt", "debtToEquity", 
        "quickRatio", "currentRatio", "freeCashflow", "operatingCashflow"
        ]

        stock_financial_info = {k: stock_data.get(k) for k in keys} # 用列表推导式拿到 key ：value

        return {"success":True, "data":stock_financial_info, "message":f"Successfully fetched stock info for {ticker_symbol}"}

    else:

        return {"success":False, "data":None, "message":f"Fail to fetch stock info for {ticker_symbol}"}
       
    

def ma(ticker_symbol):
    history = get_stock_history(ticker_symbol)
    history_data = history.get("data")

    if history.get("success") == True:

        copy_history_data = history_data.copy() # 复制一份数据，防止污染原始history数据

        copy_history_data["MA20"] = copy_history_data["Close"].rolling(window=20).mean() # rolling（20) 计算每个 close 前 20 天的平均值
        return {"success":True, "data":copy_history_data, "message":f"Successfully added MA20 for stock {ticker_symbol}"}

    else:

        return {"success":False, "data":None, "message":f"Fail to add MA20 for stock {ticker_symbol}"}


def rsi(ticker_symbol):
    history = get_stock_history(ticker_symbol)
    history_data = history.get("data")

    if history.get("success") == True:

        copy_history_data = history_data.copy()

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
        print(close,avg_gain,avg_loss,rsi)
        


        rsi_df = pd.DataFrame({"Date":copy_history_data.index, "close":close, "diff":diff, "gain":gain,"loss":loss, "avg_gain":avg_gain, "avg_loss":avg_loss, "14 days RSI":rsi})

        return {"success":True, "data":rsi_df, "message":f"Successfully calculated RSI for stock {ticker_symbol}"}

    else:

        return {"success":False, "data":None, "message":f"Fail to calculate RSI for stock {ticker_symbol}"}


def macd(ticker_symbol):
    history = get_stock_history(ticker_symbol)
    history_data = history.get("data")

    if history.get("success") == True:

        copy_history_data = history_data.copy()
        close = copy_history_data["Close"]
        print(close.ewm(span=12,adjust=False).mean())
        





macd("aapl")



    


    


