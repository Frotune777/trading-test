import pytest
import pytest_asyncio
from app.brokers.mock_adapter import MockBrokerAdapter
from app.brokers.base_adapter import Order, BrokerHealth

@pytest.mark.asyncio
async def test_mock_broker_connection():
    broker = MockBrokerAdapter()
    assert broker.connected is False
    
    connected = await broker.connect()
    assert connected is True
    assert broker.connected is True
    
    health = await broker.get_health()
    assert health.is_connected is True
    assert health.details["mode"] == "MOCK"

@pytest.mark.asyncio
async def test_mock_broker_order_placement_cycle():
    broker = MockBrokerAdapter()
    await broker.connect()
    
    # 1. Place BUY Order
    order_buy = Order(
        symbol="INFY",
        exchange="NSE",
        transaction_type="BUY",
        quantity=10,
        price=1500.0,
        product_type="MIS",
        order_type="LIMIT"
    )
    
    resp_buy = await broker.place_order(order_buy)
    assert resp_buy["status"] == "COMPLETE"
    assert "mock-" in resp_buy["order_id"]
    
    # Verify Position Update
    positions = await broker.get_positions()
    assert len(positions) == 1
    assert positions[0].symbol == "INFY"
    assert positions[0].quantity == 10
    assert positions[0].average_price == 1500.0
    
    # 2. Place SELL Order (Partial)
    order_sell = Order(
        symbol="INFY",
        exchange="NSE",
        transaction_type="SELL",
        quantity=4,
        price=1550.0,
        order_type="LIMIT",
        product_type="MIS"
    )
    
    resp_sell = await broker.place_order(order_sell)
    assert resp_sell["status"] == "COMPLETE"
    
    # Verify Position Update (10 - 4 = 6)
    positions = await broker.get_positions()
    assert len(positions) == 1
    assert positions[0].quantity == 6
    # Avg price shouldn't change on Sell for straightforward implementation (FIFO/Avg logic usually simpler in mock)
    # The mock impl kept avg price same.
    assert positions[0].average_price == 1500.0

@pytest.mark.asyncio
async def test_mock_broker_order_book():
    broker = MockBrokerAdapter()
    await broker.connect()
    
    order = Order(
        symbol="TCS",
        exchange="NSE",
        transaction_type="BUY",
        quantity=5,
        price=3000.0,
        product_type="CNC",
        order_type="MARKET"
    )
    
    await broker.place_order(order)
    
    book = await broker.get_order_book()
    assert len(book) == 1
    assert book[0].symbol == "TCS"
    assert book[0].status == "COMPLETE"
