from typing import List, Dict, Any
import pandas as pd

class ScreenerEngine:
    """
    PILLAR 2: Analytics Engine (A)
    Supports compound screening conditions.
    """
    def __init__(self, stocks_df: pd.DataFrame):
        self.df = stocks_df

    def run_screen(self, conditions: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Executes a screen based on a list of conditions.
        Example condition: {"field": "pe_ratio", "operator": "<", "value": 20}
        """
        filtered_df = self.df.copy()
        
        for condition in conditions:
            field = condition["field"]
            op = condition["operator"]
            val = condition["value"]
            
            if field not in filtered_df.columns:
                continue

            if op == ">":
                filtered_df = filtered_df[filtered_df[field] > val]
            elif op == "<":
                filtered_df = filtered_df[filtered_df[field] < val]
            elif op == "==":
                filtered_df = filtered_df[filtered_df[field] == val]
            elif op == ">=":
                filtered_df = filtered_df[filtered_df[field] >= val]
            elif op == "<=":
                filtered_df = filtered_df[filtered_df[field] <= val]
                
        return filtered_df
