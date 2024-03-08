import pandas as pd
import numpy as np
import yfinance as yf
from itertools import combinations

def portfolio_metrics(dataframe, columns_to_use, years_simulated=5, set_size=3, var_confidence=0.05, cvar_confidence=0.05, trading_days_per_year=252, user=None):
    # Initialize results DataFrame
    results_list = []

    # Check if SPY exists for Portfolio Beta calculation
    include_beta = 'SPY' in dataframe.columns

    # Generate all unique combinations
    all_combinations = list(combinations(columns_to_use, set_size))

    # Filter DataFrame based on years simulated
    latest_date = dataframe['Date'].max()
    earliest_date = pd.Timestamp(latest_date) - pd.DateOffset(years=years_simulated)
    filtered_df = dataframe[dataframe['Date'] >= earliest_date]

    for selected_columns in all_combinations:
        returns = filtered_df[list(selected_columns)].pct_change(fill_method=None).dropna()
        risk_free_rate = filtered_df['risk_free_rate'].loc[returns.index].mean() / 100  # Convert to decimal
        weights = np.array([1./set_size] * set_size)

        # Adjust weights based on user's risk tolerance and investment goals
        if user:
            if user.risk_tolerance == 'Aggressive':
                weights *= 1.2
            elif user.risk_tolerance == 'Conservative':
                weights *= 0.8
            
            if user.investment_goals == 'Short-Term Gains':
                # Emphasize total return for short-term gains
                metrics_score = total_return
            elif user.investment_goals == 'Long-Term Growth':
                # Emphasize CAGR for long-term growth
                metrics_score = cagr

        # Sharpe Ratio
        expected_return = np.sum(returns.mean() * weights) * trading_days_per_year
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * trading_days_per_year, weights)))
        sharpe_ratio = (expected_return - risk_free_rate) / portfolio_volatility

        # VaR and CVaR
        portfolio_return_series = (returns * weights).sum(axis=1)
        var_value = portfolio_return_series.quantile(var_confidence)
        cvar_value = portfolio_return_series[portfolio_return_series <= var_value].mean()

        # Maximum Drawdown
        cumulative_returns = (1 + portfolio_return_series).cumprod()
        max_value = cumulative_returns.cummax()
        drawdowns = cumulative_returns / max_value - 1
        max_drawdown = drawdowns.min()

        # Sortino Ratio
        negative_returns = portfolio_return_series[portfolio_return_series < 0]
        downside_deviation = negative_returns.std() * np.sqrt(trading_days_per_year)
        sortino_ratio = (expected_return - risk_free_rate) / downside_deviation

        # Portfolio Beta
        if include_beta:
            spy_returns = filtered_df['SPY'].diff() / filtered_df['SPY'].shift(1)
            aligned_data = pd.concat([portfolio_return_series, spy_returns], axis=1).dropna()
            portfolio_beta = aligned_data.iloc[:, 0].cov(aligned_data.iloc[:, 1]) / aligned_data.iloc[:, 1].var()

        # Total Return and CAGR
        total_return = cumulative_returns.iloc[-1] - 1  # subtract 1 to convert to percentage
        cagr = (cumulative_returns.iloc[-1] ** (1 / years_simulated)) - 1  # again, subtract 1 for percentage

        # Append to results
        metrics = {f'stock_{i+1}': stock for i, stock in enumerate(selected_columns)}
        metrics['Sharpe_Ratio'] = sharpe_ratio
        metrics['VaR'] = var_value
        metrics['CVaR'] = cvar_value
        metrics['Max_Drawdown'] = max_drawdown
        metrics['Sortino_Ratio'] = sortino_ratio
        metrics['Total_Return'] = total_return
        metrics['CAGR'] = cagr
        if include_beta:
            metrics['Portfolio_Beta'] = portfolio_beta

        results_list.append(metrics)

    # Convert results to DataFrame
    results_df = pd.DataFrame(results_list)

    return results_df

def sort_and_display(df, sort_by, ascending=True, rows_to_show=5):
    # Sort the DataFrame by the specified column
    sorted_df = df.sort_values(by=sort_by, ascending=ascending).head(rows_to_show)

    # Find columns that start with 'stock_'
    stock_cols = [col for col in df.columns if col.startswith('stock_')]

    # Add the column to sort by
    columns_to_display = stock_cols + [sort_by]

    # Display the sorted and filtered DataFrame
    return sorted_df.loc[:, columns_to_display]
