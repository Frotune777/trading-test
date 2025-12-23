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
  - generic [ref=e45] [cursor=pointer]:
    - button "Open Next.js Dev Tools" [ref=e46]:
      - img [ref=e47]
    - generic [ref=e52]:
      - button "Open issues overlay" [ref=e53]:
        - generic [ref=e54]:
          - generic [ref=e55]: "0"
          - generic [ref=e56]: "1"
        - generic [ref=e57]: Issue
      - button "Collapse issues badge" [ref=e58]:
        - img [ref=e59]
  - alert [ref=e61]
```