import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from service import *
import re

st.title("Stock Indicator")

st.divider()

selection = st.pills("Options", options=["Financial index", "Compare stocks"], default="Financial index")

match selection:

    case "Financial index":

        stock_symbol = st.text_input(label="Stock symbol", placeholder="Please enter a stock symbol  (  e.g.  'NVDA'  ,  '0700.HK'  ) ")
        period = st.text_input(label="Period", value="1y", placeholder="Please enter the period  (e.g.  '2y'  ,  '6mo'  ,  '50d'  ) ")

        f_index = st.selectbox(label="Financial Index", options=("MA", "RSI", "MACD", "BOLL"), placeholder="Select the financial index", index=None)

        if stock_symbol:

            financial_info = get_stock_financial_info(stock_symbol)

            if financial_info.get("success") == True:
                financial_data = financial_info.get("data")
                
                f1, f2, f3= st.columns([3,1,1], gap="xxsmall")

                f1.metric("Market Cap", financial_data.get("marketCap"), format="dollar", border=True)
                f2.metric("Gross Margin", financial_data.get("grossMargins"), format="dollar", border=True)
                f3.metric("Price to Book P/B", financial_data.get("priceToBook"), format="%.2f", border=True)
                

                f4, f5 = st.columns([2,1], gap="xxsmall")

                f4.metric("Total Revenue", financial_data.get("totalRevenue"), format="dollar", border=True)
                f5.metric("Dividend Yield", financial_data.get("dividendYield"), format="percent", border=True)

                f6, f7 = st.columns([2,1], gap="xxsmall")

                f6.metric("Gross Profit", financial_data.get("grossProfits"), format="dollar", border=True)
                f7.metric("Dividend Rate", financial_data.get("dividendRate"), format="percent", border=True)
                

                f8, f9, f10, f11 = st.columns(4, gap="xxsmall")

                f8.metric("Trailing PE", financial_data.get("trailingPE"), border=True, format="%.3f")
                f9.metric("Forward PE", financial_data.get("forwardPE"), border=True, format="%.3f")
                
                if financial_data.get("trailingEps"):
                    f10.metric("Trailing EPS", f'${financial_data.get("trailingEps"):.2f}/s', format="dollar", border=True)

                else:
                    f10.metric("Trailing EPS", financial_data.get("trailingEps"), border=True)

                if financial_data.get("trailingEps"):
                    f11.metric("Forward EPS", f"${financial_data.get("forwardEps"):.2f}/s", format="dollar", border=True)

                else:
                    f11.metric("Forward EPS", financial_data.get("forwardEps"), border=True)
                              
                with st.expander("See financial info"):
                    df = pd.DataFrame({"info":financial_data.keys(), "value":financial_data.values()})
                    st.dataframe(df)

            stock_history = get_stock_history_cached(stock_symbol, data_period=period)

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
                st.write("Fail to calculate financial index, please check for the stock symbol")

        else:
            st.write("Please enter a stock symbol")

    case "Compare stocks":

        stock_symbol = st.text_input("Enter the stocks you want to compare", placeholder="Enter the stocks ( e.g. NVDA , AAPL )")
        period = st.text_input(label="Period", value="1y", placeholder="Please enter the period  (e.g.  '2y'  ,  '6mo'  ,  '50d'  ) ")
        symbol_list = re.split(r"\s*,\s*", stock_symbol.upper().strip())
        symbol_set = {*symbol_list}
        

        compare_stock = compare_stocks(*symbol_set, period=period)

        if compare_stock.get("success") == True:
            
            cs_data = compare_stock.get("data")

            select_cs = st.multiselect("Select the stocks you want to compare", options=cs_data.columns)

            st.write(compare_stock.get("message"))

            cs_fig = px.line(cs_data, x=cs_data.index, y=select_cs, title=" Stocks Percentange Change ( %Chg ) ")

            st.plotly_chart(cs_fig)

        else:

            st.write(compare_stock.get("message"))