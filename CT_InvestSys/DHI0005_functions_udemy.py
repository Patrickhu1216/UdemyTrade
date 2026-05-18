"""
DHI0005_functions.py
This is the main functions file intended for a standalone course!

This file should be either saved in your Google Drive so it can be imported.
Alternatively, you can drag and drop the file into a Colab instance.

Please watch the tutorial video in this course to learn more about how to use this file.

The functions in this file are intended to be used with:
Building an Investment Trading System with Python

Last revisions: December 18, 2024

"""
# install/import needed libraries
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf


def retrieve_prices_yf(tickers: list, start_date: str, end_date: str, frequency: str = 'D',
                       common_inception: bool = False) -> pd.DataFrame:
    """
    Retrieve adjusted close prices for given investment tickers within a specified date range, resampled to a specified frequency.

    Params:
    tickers (list): A list of investment ticker symbols.
    start_date (str): The start date for the price data in 'YYYY-MM-DD' format.
    end_date (str): The end date for the price data in 'YYYY-MM-DD' format.
    frequency (str): The frequency for resampling the data. 'D' for daily (default), 'W' for weekly, and 'M' for monthly.
    common_inception (bool): If True, only returns dates where all tickers have data. Defaults to False.

    Returns:
    pd.DataFrame: A DataFrame with adjusted close prices resampled to the specified frequency.

    Raises:
    ValueError: If tickers are not provided in a list of strings.

    Example:
    >>> retrieve_prices(['AAPL', 'MSFT'], '2020-01-01', '2020-12-31', 'W')
    """

    # Validate tickers input
    if not isinstance(tickers, list) or not all(isinstance(ticker, str) for ticker in tickers):
        raise ValueError('Please supply tickers in a list of strings')

    # Retrieve the pricing data using yfinance
    df_prices = yf.download(tickers, start_date, end_date)['Close']

    # Resample data based on the frequency
    if frequency == 'W':
        df_prices = df_prices.resample('W-FRI').last()
    elif frequency == 'M':
        df_prices = df_prices.resample('ME').last()

    # Remove all rows containing NaN if common_inception is True
    if common_inception:
        df_prices.dropna(inplace=True)

    df_prices.index = df_prices.index.tz_localize(None)

    return df_prices


def cumulative_return_graph_plotly(returns, start_date=None, end_date=None):
    """
    Generates a line graph showing the cumulative return of investments over time.

    This function calculates the cumulative return from a DataFrame of periodic returns
    and plots it as a percentage. The cumulative return is the total change in the investment
    value from the beginning of the time series.

    Parameters:
    returns (pd.DataFrame): A DataFrame where each column represents a different investment
                            and contains their respective periodic returns.
    start_date (str or None): Start date of the time period to consider for the returns. Defaults to None.
    end_date (str or None): End date of the time period to consider for the returns. Defaults to None.

    Returns:
    None: The function outputs the graph directly and does not return any value.

    Note:
    The function assumes the input DataFrame's index represents dates and the columns represent
    different investment securities or portfolios.
    """
    # Set default start_date and end_date if they are None
    if start_date is None:
        start_date = returns.index[0]
    elif isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d')

    if end_date is None:
        end_date = returns.index[-1]
    elif isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

    # Filter the returns DataFrame based on the provided date range
    returns = returns.loc[start_date:end_date]

    # Calculate cumulative returns in percentage
    df_cumulative = ((1 + returns).cumprod() - 1).mul(100)

    # Convert index to NumPy array to avoid the FutureWarning
    x_values = df_cumulative.index.to_numpy()

    # Create a new figure
    fig = go.Figure()

    # Add a line for each column in the DataFrame
    for col in df_cumulative.columns:
        fig.add_trace(go.Scatter(x=x_values, y=df_cumulative[col], mode='lines', name=col))

    # Set the title and axis labels
    fig.update_layout(
        title='Cumulative Percent Returns',
        xaxis_title='Date',
        yaxis_title='Cumulative Return (%)',
        yaxis_tickformat=',',  # Add thousands separator
    )

    # Show the plot
    fig.show()