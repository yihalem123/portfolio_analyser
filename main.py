from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import yfinance as yf
import datetime
from portfolio_analysis import portfolio_metrics
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

class PortfolioRequest(BaseModel):
    years_simulated: int
    set_size: int
    tickers: List[str]
    order_by: str
    ascending: bool

@app.post("/portfolio/")
async def optimize_portfolio(portfolio_request: PortfolioRequest):
    tickers = portfolio_request.tickers
    years_simulated = portfolio_request.years_simulated
    set_size = portfolio_request.set_size
    order_by = portfolio_request.order_by
    ascending = portfolio_request.ascending

    data = await fetch_data(tickers, years_simulated)

    columns_to_use = data.columns.tolist()
    columns_to_use.remove('Date')
    if 'risk_free_rate' in columns_to_use:
        columns_to_use.remove('risk_free_rate')

    results_df = portfolio_metrics(data, columns_to_use, set_size=set_size, years_simulated=years_simulated)

    sorted_results = results_df.sort_values(by=order_by, ascending=ascending).head(3)

    return sorted_results.to_dict(orient='records')

@app.get("/optimize")
async def optimize_portfolio(
    years_simulated: int = Query(..., description="Number of years to simulate."),
    set_size: int = Query(..., description="Size of the portfolio."),
    tickers: List[str] = Query(None, description="List of stock tickers."),
    order_by: str = Query("Total_Return", description="Column to order by."),
    ascending: bool = Query(True, description="Sort order (True for ascending, False for descending)."),
):
    data = await fetch_data(tickers, years_simulated)

    columns_to_use = data.columns.tolist()
    columns_to_use.remove('Date')
    if 'risk_free_rate' in columns_to_use:
        columns_to_use.remove('risk_free_rate')

    results_df = portfolio_metrics(data, columns_to_use, set_size=set_size, years_simulated=years_simulated)

    sorted_results = results_df.sort_values(by=order_by, ascending=ascending)

    return sorted_results.to_dict(orient='records')

async def fetch_data(tickers: List[str], years_simulated: int):
    current_date = datetime.datetime.today().strftime('%Y-%m-%d')
    start_date = datetime.datetime.today() - datetime.timedelta(days=years_simulated * 365)
    start_date = start_date.strftime('%Y-%m-%d')
    end_date = current_date

    tickers_str = ' '.join(tickers)
    data = yf.download(tickers=tickers_str, start=start_date, end=end_date, progress=False)['Adj Close']
    data.reset_index(inplace=True)

    risk_free_rate = yf.Ticker("^TNX").history(period="5y")['Close']
    risk_free_rate = risk_free_rate.rename('risk_free_rate')
    if isinstance(risk_free_rate.index, pd.DatetimeIndex) and risk_free_rate.index.tzinfo is not None:
        risk_free_rate.index = risk_free_rate.index.tz_localize(None)

    data = pd.merge(data, risk_free_rate, left_on='Date', right_index=True, how='left')
    data['risk_free_rate'] = data['risk_free_rate'].ffill()
    data = data.dropna(axis=1, how='all')

    return data

if __name__ == '__main__':
    app.run(debug=True)
