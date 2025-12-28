"""
Subscription Manager
Manages client subscriptions with O(1) lookup
"""

import logging
from typing import Dict, Set, List
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)

class SubscriptionManager:
    """Manages WebSocket client subscriptions"""
    
    def __init__(self):
        # symbol -> mode -> set of clients
        self.subscriptions: Dict[str, Dict[str, Set[WebSocketServerProtocol]]] = {}
        # client -> set of (symbol, mode) tuples
        self.client_subscriptions: Dict[WebSocketServerProtocol, Set[tuple]] = {}
    
    def add_subscription(self, symbol: str, mode: str, client: WebSocketServerProtocol):
        """Add a subscription (O(1))"""
        # Initialize structures if needed
        if symbol not in self.subscriptions:
            self.subscriptions[symbol] = {}
        if mode not in self.subscriptions[symbol]:
            self.subscriptions[symbol][mode] = set()
        if client not in self.client_subscriptions:
            self.client_subscriptions[client] = set()
        
        # Add subscription
        self.subscriptions[symbol][mode].add(client)
        self.client_subscriptions[client].add((symbol, mode))
        
        logger.debug(f"Added subscription: {symbol} ({mode}) for client {id(client)}")
    
    def remove_subscription(self, symbol: str, client: WebSocketServerProtocol):
        """Remove a subscription for all modes"""
        if symbol not in self.subscriptions:
            return
        
        # Remove from all modes
        for mode in list(self.subscriptions[symbol].keys()):
            if client in self.subscriptions[symbol][mode]:
                self.subscriptions[symbol][mode].remove(client)
                
                # Clean up empty sets
                if not self.subscriptions[symbol][mode]:
                    del self.subscriptions[symbol][mode]
        
        # Clean up empty symbol
        if not self.subscriptions[symbol]:
            del self.subscriptions[symbol]
        
        # Remove from client subscriptions
        if client in self.client_subscriptions:
            self.client_subscriptions[client] = {
                (s, m) for s, m in self.client_subscriptions[client] if s != symbol
            }
        
        logger.debug(f"Removed subscription: {symbol} for client {id(client)}")
    
    def remove_all_subscriptions(self, client: WebSocketServerProtocol):
        """Remove all subscriptions for a client"""
        if client not in self.client_subscriptions:
            return
        
        # Get all subscriptions for this client
        client_subs = self.client_subscriptions[client].copy()
        
        # Remove each subscription
        for symbol, mode in client_subs:
            if symbol in self.subscriptions and mode in self.subscriptions[symbol]:
                self.subscriptions[symbol][mode].discard(client)
                
                # Clean up empty sets
                if not self.subscriptions[symbol][mode]:
                    del self.subscriptions[symbol][mode]
                if not self.subscriptions[symbol]:
                    del self.subscriptions[symbol]
        
        # Remove client entry
        del self.client_subscriptions[client]
        
        logger.debug(f"Removed all subscriptions for client {id(client)}")
    
    def get_subscribers(self, symbol: str, mode: str = "ltp") -> Set[WebSocketServerProtocol]:
        """Get all clients subscribed to a symbol (O(1))"""
        if symbol not in self.subscriptions:
            return set()
        if mode not in self.subscriptions[symbol]:
            return set()
        return self.subscriptions[symbol][mode].copy()
    
    def get_subscription_count(self, symbol: str) -> int:
        """Get total number of subscriptions for a symbol"""
        if symbol not in self.subscriptions:
            return 0
        return sum(len(clients) for clients in self.subscriptions[symbol].values())
    
    def get_all_subscribed_symbols(self) -> List[str]:
        """Get list of all symbols with active subscriptions"""
        return list(self.subscriptions.keys())
    
    def get_client_subscriptions(self, client: WebSocketServerProtocol) -> List[tuple]:
        """Get all subscriptions for a specific client"""
        if client not in self.client_subscriptions:
            return []
        return list(self.client_subscriptions[client])
    
    def get_stats(self) -> Dict:
        """Get subscription statistics"""
        total_subscriptions = sum(
            sum(len(clients) for clients in modes.values())
            for modes in self.subscriptions.values()
        )
        
        return {
            "total_symbols": len(self.subscriptions),
            "total_clients": len(self.client_subscriptions),
            "total_subscriptions": total_subscriptions,
            "symbols": {
                symbol: self.get_subscription_count(symbol)
                for symbol in self.subscriptions.keys()
            }
        }
