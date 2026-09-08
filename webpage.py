import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from service import *

st.title("Stock Indicator")

st.divider()

selection = st.pills("Options", options=["Financial index", "Compare stocks"], default="Financial index")

match selection:

    case "Financial index":

        stock_symbol = st.text_input(label="Stock symbol", placeholder="Please enter a stock symbol  (  e.g.  'NVDA'  ,  '0700.HK'  ) ")

        f_index = st.selectbox(label="Financial Index", options=("MA", "RSI", "MACD", "BOLL"), placeholder="Select the financial index", index=None)

        if stock_symbol:
            stock_history = get_stock_history(stock_symbol)

            if stock_history.get("success") == True:
                stock_data = stock_history.get("data")

                match f_index:

                    case "MA":
                        if len(stock_data) < 20:
                            st.warning("History data for this stock are less than 20 days, can't calculate MA20")

                        else:
                            ma_return = ma(stock_data)
                        
                            ma_fig = px.line(ma_return, x="Date", y=["Close", "MA20"], title="MA20 (Moving Average 20 days)")
                            st.plotly_chart(ma_fig)

                    case "RSI":
                        if len(stock_data) < 15:
                            st.warning("History data for this stock are less than 15 days, can't calculate RSI")

                        else:
                            rsi_return = rsi(stock_data)
                            
                            rsi_fig = px.line(rsi_return, x="Date", y="14 days RSI", title="RSI (Relative Strength Index)")
                            st.plotly_chart(rsi_fig)

                     
                    case "MACD":
                        if len(stock_data) < 35:
                            st.warning("History data for this stock are less than 35 days. Please note that the reference value is low.")

                        macd_return = macd(stock_data)

                        macd_line = px.line(macd_return, x="Date", y=["macd_line","signal_line"])
                        macd_bar = px.bar(macd_return, x="Date", y="histogram", color="color", color_discrete_map={"positive":"green", "negative":"red"})
                        macd_fig = go.Figure(data=macd_line.data + macd_bar.data)

                        macd_fig.update_layout(title="MACD ( Moving Average Convergence/Divergence Indicator )")
                        st.plotly_chart(macd_fig)

                    case "BOLL":
                        if len(stock_data) < 20:
                            st.warning("History data for this stock are less than 20 days, can't calculate BOLL")

                        else:
                            boll_return = boll(stock_data)
                            
                            boll_line = px.line(boll_return, x="Date", y=["middle_band", "upper_band", "lower_band"], title="BOLL (Bollinger Band)")
                            
                            st.plotly_chart(boll_line)

                    case _:
                        st.write("Please select a financial index")

                                                    
            else:
                st.write("Fail to claculate financial index")

        else:
            st.write("Please enter a stock symbol")

    case "Compare stocks":

        stock_symbol = st.text_input("Enter the stocks you want to compare", placeholder="Enter the stocks ( e.g. NVDA, AAPL )")
        symbol_list = stock_symbol.upper().split(",")
        

        compare_stock = compare_stocks(*symbol_list)

        if compare_stock.get("success") == True:
            
            cs_data = compare_stock.get("data")

            select_cs = st.multiselect("Select the stocks you want to compare", options=cs_data.columns)

            st.write(compare_stock.get("message"))

            cs_fig = px.line(cs_data, x=cs_data.index, y=select_cs, title=" Stocks Percentange Change ( %Chg ) ")

            st.plotly_chart(cs_fig)

        else:
            st.write(compare_stock.get("message"))

        




        

