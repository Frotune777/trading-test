from nselib import capital_market
import inspect

print("Functions in nselib.capital_market:")
for name, obj in inspect.getmembers(capital_market):
    if inspect.isfunction(obj):
        print(f"- {name}")
