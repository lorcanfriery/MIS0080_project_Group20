print("hello world")
print("hello again")
print("new")


# Testing FREDAPI
from fredapi import Fred
import pandas as pd

fred = Fred(api_key="e5f01fd50421590fffaebf8fec19052a")

eurusd = fred.get_series("DEXUSEU", observation_start="2015-01-01")
eurusd.name = "EURUSD"
print(eurusd.head())
