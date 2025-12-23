# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - main [ref=e3]:
    - generic [ref=e5]:
      - generic [ref=e6]:
        - img [ref=e7]
        - textbox "Search stocks, ETFs, indices... (Press '/')" [ref=e10]
      - button "Feedback" [ref=e12]
    - generic [ref=e15]:
      - generic [ref=e16]:
        - heading "Market Pulse" [level=2] [ref=e17]
        - paragraph [ref=e18]: Live market overview and institutional activity.
      - generic [ref=e25]:
        - generic [ref=e27]: Trend Leaders (Volume)
        - table [ref=e30]:
          - rowgroup [ref=e31]:
            - row "Symbol Price % Chg Volume" [ref=e32]:
              - columnheader "Symbol" [ref=e33]
              - columnheader "Price" [ref=e34]
              - columnheader "% Chg" [ref=e35]
              - columnheader "Volume" [ref=e36]
          - rowgroup [ref=e37]:
            - row "Loading market data..." [ref=e38]:
              - cell "Loading market data..." [ref=e39]
  - button "Open Next.js Dev Tools" [ref=e46] [cursor=pointer]:
    - img [ref=e47]
```