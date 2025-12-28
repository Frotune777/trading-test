"""
Angel One Data Models
Data structures for Angel One API responses
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class ExchangeType(int, Enum):
    """Angel One exchange types"""
    NSE = 1
    NFO = 2
    BSE = 3
    BFO = 4
    MCX = 5
    NCDS = 7
    NCDEX = 13


class SubscriptionMode(int, Enum):
    """Angel One subscription modes"""
    LTP = 1  # Last Traded Price
    QUOTE = 2  # Quote (OHLC)
    SNAP_QUOTE = 3  # Snap Quote (Full depth)


class AngelOneMarketData(BaseModel):
    """Angel One market data tick"""
    exchange_type: int
    token: str
    sequence_number: int
    exchange_timestamp: int
    last_traded_price: int  # Multiplied by 100
    subscription_mode: int
    last_traded_quantity: Optional[int] = None
    average_traded_price: Optional[int] = None
    volume_trade_for_the_day: Optional[int] = None
    total_buy_quantity: Optional[float] = None
    total_sell_quantity: Optional[float] = None
    open_price_of_the_day: Optional[int] = None
    high_price_of_the_day: Optional[int] = None
    low_price_of_the_day: Optional[int] = None
    closed_price: Optional[int] = None


class AngelOneOrderData(BaseModel):
    """Angel One order data"""
    variety: str
    ordertype: str
    producttype: str
    duration: str
    price: float
    triggerprice: Optional[float] = None
    quantity: int
    disclosedquantity: int
    squareoff: float
    stoploss: float
    trailingstoploss: float
    tradingsymbol: str
    transactiontype: str
    exchange: str
    symboltoken: str
    ordertag: Optional[str] = None


class AngelOneOrderResponse(BaseModel):
    """Angel One order response"""
    status: bool
    message: str
    errorcode: Optional[str] = None
    data: Optional[dict] = None


class AngelOnePosition(BaseModel):
    """Angel One position data"""
    exchange: str
    symboltoken: str
    producttype: str
    tradingsymbol: str
    symbolname: str
    instrumenttype: str
    priceden: str
    pricenum: str
    genden: str
    gennum: str
    precision: str
    multiplier: str
    boardlotsize: str
    buyqty: str
    sellqty: str
    buyamount: str
    sellamount: str
    symbolgroup: str
    strikeprice: str
    optiontype: str
    expirydate: Optional[str] = None
    lotsize: str
    cfbuyqty: str
    cfsellqty: str
    cfbuyamount: str
    cfsellamount: str
    buyavgprice: str
    sellavgprice: str
    avgnetprice: str
    netvalue: str
    netqty: str
    totalbuyvalue: str
    totalsellvalue: str
    cfbuyavgprice: str
    cfsellavgprice: str
    totalbuyavgprice: str
    totalsellavgprice: str
    netprice: str


class AngelOneHolding(BaseModel):
    """Angel One holding data"""
    tradingsymbol: str
    exchange: str
    isin: str
    t1quantity: str
    realisedquantity: str
    quantity: str
    authorisedquantity: str
    product: str
    collateralquantity: str
    collateraltype: str
    haircut: str
    averageprice: str
    ltp: str
    symboltoken: str
    close: str
    profitandloss: str
    pnlpercentage: str


class SymbolToken(BaseModel):
    """Symbol to token mapping"""
    symbol: str
    exchange: str
    token: str
    exchange_type: int
