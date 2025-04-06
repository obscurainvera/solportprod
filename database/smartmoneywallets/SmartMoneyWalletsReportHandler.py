from config.Config import get_config
from typing import List, Dict, Any, Optional
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from logs.logger import get_logger
import json
import sqlite3
import requests
from actions.DexscrennerAction import DexScreenerAction


logger = get_logger(__name__)

class SmartMoneyWalletsReportHandler(BaseDBHandler):
    """
    Handler for smart money wallet report operations.
    Provides methods to query wallet PNL data and token details for reporting.
    """
    
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        """
        Initialize the handler with a connection manager.
        
        Args:
            conn_manager: Database connection manager instance
        """
        super().__init__(conn_manager)
        self.dex_screener = DexScreenerAction()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """
        Execute a SQL query and return the results.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            List of tuples containing the query results
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Database error executing query: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def fetch_token_prices(self, token_ids: List[str]) -> Dict[str, float]:
        """
        Fetch current prices for tokens from Dexscreener API using batch request
        
        Args:
            token_ids: List of token IDs to fetch prices for
            
        Returns:
            Dictionary mapping token IDs to their current prices
        """
        prices = {}
        
        try:
            logger.info(f"Fetching prices for {len(token_ids)} tokens in batch")
            
            # Use the DexscreennerAction to get batch token prices
            token_price_data = self.dex_screener.getBatchTokenPrices(token_ids, "solana")
            
            # Convert TokenPrice objects to simple price values
            for token_id, token_price in token_price_data.items():
                if token_price is not None:
                    prices[token_id] = token_price.price
                else:
                    prices[token_id] = 0
                    logger.warning(f"No price data found for token: {token_id}")
            
            logger.info(f"Successfully fetched prices for {len(prices)} tokens")
            
        except Exception as e:
            logger.error(f"Error fetching batch token prices: {str(e)}")
        
        return prices
    
    def getSmartMoneyWalletReport(self, 
                                 walletAddress: str,
                                 sortBy: str = "profitandloss",
                                 sortOrder: str = "desc") -> Dict[str, Any]:
        """
        Get smart money wallet report data for a specific wallet.
        Performs an inner join between smartmoneywallets and smwallettoppnltoken tables
        to get the wallet PNL and token-specific investment details.
        
        Args:
            walletAddress: The wallet address to get details for
            sortBy: Field to sort tokens by (default: profitandloss)
            sortOrder: Sort order (asc or desc)
            
        Returns:
            Dictionary containing wallet PNL data and token details
        """
        try:
            # Validate sort parameters
            valid_sort_fields = ["profitandloss", "tokenname", "amountinvested", "amounttakenout", 
                                "remainingamount", "realizedpnl"]
            if sortBy not in valid_sort_fields:
                sortBy = "profitandloss"
                
            if sortOrder.lower() not in ["asc", "desc"]:
                sortOrder = "desc"
            
            # Map frontend sort field names to database column names
            sort_field_map = {
                "profitandloss": "t.unprocessedpnl",  # Total PNL will be calculated after fetching data
                "tokenname": "t.name",
                "amountinvested": "t.amountinvested",
                "amounttakenout": "t.amounttakenout",
                "remainingamount": "t.remainingcoins",  # Sort by remaining coins initially
                "realizedpnl": "CAST(t.amounttakenout AS DECIMAL) - CAST(t.amountinvested AS DECIMAL)"  # Calculate realized PNL
            }
            
            db_sort_field = sort_field_map.get(sortBy, "t.unprocessedpnl")
            
            # First, get the wallet data from smartmoneywallets table
            wallet_query = """
            SELECT 
                walletaddress,
                walletaddress as walletname,
                profitandloss
            FROM smartmoneywallets
            WHERE walletaddress = ?
            """
            
            wallet_params = (walletAddress,)
            wallet_result = self.execute_query(wallet_query, wallet_params)
            
            if not wallet_result:
                logger.warning(f"No wallet data found for address: {walletAddress}")
                return {"wallet": None, "tokens": []}
            
            # Create wallet data dictionary
            wallet_data = {
                "walletAddress": wallet_result[0][0],
                "walletName": wallet_result[0][1],
                "profitAndLoss": wallet_result[0][2]
            }
            
            # Now get the token data from smwallettoppnltoken table with additional columns
            tokens_query = f"""
            SELECT 
                t.tokenid,
                t.name as tokenname,
                t.amountinvested,
                t.amounttakenout,
                t.unprocessedpnl as profitandloss,
                t.remainingcoins,
                t.unprocessedroi
            FROM smwallettoppnltoken t
            WHERE t.walletaddress = ?
            ORDER BY {db_sort_field} {sortOrder}
            """
            
            tokens_params = (walletAddress,)
            tokens_results = self.execute_query(tokens_query, tokens_params)
            
            # Filter tokens with remaining coins > 0
            tokens_with_remaining = []
            token_ids = []
            
            for row in tokens_results:
                token_id = row[0]
                token_name = row[1]
                amount_invested = float(row[2]) if row[2] is not None else 0
                amount_taken_out = float(row[3]) if row[3] is not None else 0
                profit_and_loss = float(row[4]) if row[4] is not None else 0
                remaining_coins = float(row[5]) if row[5] is not None else 0
                
                # Add token to list regardless of remaining coins
                token = {
                    "tokenId": token_id,
                    "tokenName": token_name,
                    "amountInvested": amount_invested,
                    "amountTakenOut": amount_taken_out,
                    "profitAndLoss": profit_and_loss,
                    "remainingCoins": remaining_coins,
                    "currentPrice": 0,  # Will be updated later for tokens with remaining coins
                    "remainingAmount": 0,  # Will be calculated
                    "realizedPnl": amount_taken_out - amount_invested,  # Calculate realized PNL
                    "roi": float(row[6]) if row[6] is not None else 0  # Add ROI from database
                }
                
                tokens_with_remaining.append(token)
                
                # Only fetch prices for tokens with remaining coins
                if remaining_coins > 0:
                    token_ids.append(token_id)
            
            # Fetch current prices for tokens with remaining coins in batch
            token_prices = {}
            if token_ids:
                try:
                    token_prices = self.fetch_token_prices(token_ids)
                except Exception as e:
                    logger.error(f"Error fetching token prices: {str(e)}")
            
            # Calculate remaining amount and update total PNL
            tokens = []
            for token in tokens_with_remaining:
                token_id = token["tokenId"]
                remaining_coins = token["remainingCoins"]
                
                # Get current price if available
                current_price = token_prices.get(token_id, 0)
                token["currentPrice"] = current_price
                
                # Calculate remaining amount
                remaining_amount = remaining_coins * current_price
                token["remainingAmount"] = remaining_amount
                
                # Update total PNL (realized PNL + remaining amount)
                token["profitAndLoss"] = token["realizedPnl"] + remaining_amount
                
                tokens.append(token)
            
            # Sort tokens based on the requested sort field
            # Since we've calculated values that weren't in the DB, we need to sort here if certain fields were requested
            if sortBy in ["remainingamount", "realizedpnl", "profitandloss"]:
                sort_field_client = {
                    "remainingamount": "remainingAmount",
                    "realizedpnl": "realizedPnl",
                    "profitandloss": "profitAndLoss"
                }.get(sortBy)
                
                tokens = sorted(tokens, key=lambda x: x[sort_field_client], reverse=(sortOrder.lower() == "desc"))
            
            # Return combined data
            return {
                "wallet": wallet_data,
                "tokens": tokens
            }
            
        except Exception as e:
            logger.error(f"Error getting smart money wallet report: {str(e)}")
            return {"wallet": None, "tokens": [], "error": str(e)}
            
    def getTopSmartMoneyWallets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top smart money wallets by PNL.
        
        Args:
            limit: Maximum number of wallets to return
            
        Returns:
            List of dictionaries containing wallet data
        """
        try:
            query = """
            SELECT 
                walletaddress,
                walletaddress as walletname,
                profitandloss
            FROM smartmoneywallets
            ORDER BY CAST(profitandloss AS DECIMAL) DESC
            LIMIT ?
            """
            
            params = (limit,)
            results = self.execute_query(query, params)
            
            wallets = []
            for row in results:
                wallet = {
                    "walletAddress": row[0],
                    "walletName": row[1],
                    "profitAndLoss": row[2]
                }
                wallets.append(wallet)
                
            return wallets
            
        except Exception as e:
            logger.error(f"Error getting top smart money wallets: {str(e)}")
            return [] 