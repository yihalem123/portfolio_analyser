from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import pandas as pd
import yfinance as yf
import datetime
from portfolio_analysis import portfolio_metrics

app = FastAPI()

class PortfolioRequest(BaseModel):
    investment_goal: str
    risk_tolerance: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the Portfolio Optimization API!"}

@app.post("/portfolio/")
async def optimize_portfolio(portfolio_request: PortfolioRequest):
    # Load risk-free rates and stock data
    risk_free_rate = yf.Ticker("^TNX").history(period="10y")['Close']
    risk_free_rate = risk_free_rate.rename('risk_free_rate')
    if isinstance(risk_free_rate.index, pd.DatetimeIndex) and risk_free_rate.index.tzinfo is not None:
        risk_free_rate.index = risk_free_rate.index.tz_localize(None)

    years_back = years_simulated
    current_date = datetime.datetime.today().strftime('%Y-%m-%d')
    start_date = datetime.datetime.today() - datetime.timedelta(days=years_back*365)
    start_date = start_date.strftime('%Y-%m-%d')
    end_date = current_date

    data = yf.download(tickers='AAPL GOOGL MSFT AMZN TSLA NVDA INTC ADBE CSCO CMCSA AVGO TXN COST QCOM TMUS CHTR INTU AMGN AMAT ISRG GILD MU BKNG AMD LRCX MDLZ ADP MELI  CSX BIIB ADI REGN LULU CTSH MAR EA BIDU JD NXPI KLAC WBA ASML KHC EXC WDAY CTAS MCHP EA SPY JPM CAT COKE BLK', start=start_date, end=end_date, progress=False)['Adj Close']
    data.reset_index(inplace=True)
    data  = pd.merge(data, risk_free_rate, left_on='Date', right_index=True, how='left')
    data['risk_free_rate'] = data['risk_free_rate'].fillna(method='ffill')
    data = data.dropna(axis=1, how='all')

    # Define columns to use for portfolio analysis
    columns_to_use = data.columns.tolist()
    columns_to_use.remove('Date')
    columns_to_use.remove('risk_free_rate')



    # Perform portfolio optimization
    results_df = portfolio_metrics(data, columns_to_use, set_size=set_size, var_confidence=var_confidence, cvar_confidence=cvar_confidence)

    # Filter results based on investment goal


    # Sort results by selected columns
    sorted_results = results_df.sort_values(by=result_columns, ascending=False).head(3)

    # Convert results to dictionary
    result_dict = sorted_results.to_dict(orient='records')

    return result_dict

@app.get("/optimize")
async def optimize_portfolio(
    years_simulated: int = Query(..., description="Number of years to simulate."),
    set_size: int = Query(..., description="Size of the portfolio."),
):
    # Load risk-free rates and stock data
    risk_free_rate = yf.Ticker("^TNX").history(period="10y")['Close']
    risk_free_rate = risk_free_rate.rename('risk_free_rate')
    if isinstance(risk_free_rate.index, pd.DatetimeIndex) and risk_free_rate.index.tzinfo is not None:
        risk_free_rate.index = risk_free_rate.index.tz_localize(None)
    years_back = int(years_simulated)
    current_date = datetime.datetime.today().strftime('%Y-%m-%d')
    start_date = datetime.datetime.today() - datetime.timedelta(days=years_back*365)
    start_date = start_date.strftime('%Y-%m-%d')
    end_date = current_date

    data = yf.download(tickers='AAPL GOOGL MSFT AMZN TSLA NVDA INTC ADBE CSCO CMCSA AVGO TXN COST QCOM TMUS CHTR INTU AMGN AMAT ISRG GILD MU BKNG AMD LRCX MDLZ ADP MELI  CSX BIIB ADI REGN LULU CTSH MAR EA BIDU JD NXPI KLAC WBA ASML KHC EXC WDAY CTAS MCHP EA SPY JPM CAT COKE BLK', start=start_date, end=end_date, progress=False)['Adj Close']
    data.reset_index(inplace=True)
    data  = pd.merge(data, risk_free_rate, left_on='Date', right_index=True, how='left')
    data['risk_free_rate'] = data['risk_free_rate'].fillna(method='ffill')
    data = data.dropna(axis=1, how='all')

    # Define columns to use for portfolio analysis
    columns_to_use = data.columns.tolist()
    columns_to_use.remove('Date')
    columns_to_use.remove('risk_free_rate')

    # Perform portfolio optimization
    results_df = portfolio_metrics(data, columns_to_use, set_size=set_size, years_simulated=years_simulated)

    return results_df.to_dict(orient='records')
if __name__ == '__main__':
    app.run(debug=True)
