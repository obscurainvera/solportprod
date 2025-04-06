from config.config import get_config
"""
Notification content models for structured messages
"""
from dataclasses import dataclass, field
from typing import Optional, List
from decimal import Decimal

@dataclass
class TokenNotificationContent:
    """
    Structured content for token notifications
    """
    # Required fields
    subject: str  # Notification subject
    contractAddress: str  # Contract address of the token
    symbol: str  # Token symbol
    chain: str  # Blockchain (e.g., sol, eth)
    
    # Optional fields
    tokenName: Optional[str] = None  # Full token name
    currentPrice: Optional[Decimal] = None  # Current token price
    balanceUsd: Optional[Decimal] = None  # Total balance in USD
    marketCap: Optional[Decimal] = None  # Market cap
    liquidity: Optional[Decimal] = None  # Liquidity
    fullyDilutedValue: Optional[Decimal] = None  # Fully diluted value
    holderCount: Optional[int] = None  # Number of holders/wallets
    description: Optional[str] = None  # Additional description
    changePercent1h: Optional[Decimal] = None  # 1-hour price change
    changePercent24h: Optional[Decimal] = None  # 24-hour price change
    txnChartUrl: Optional[str] = None  # Transaction chart URL
    dexScreenerUrl: Optional[str] = None  # DexScreener URL
    
    def formatTelegramMessage(self) -> str:
        """
        Format the content as a telegram message with HTML formatting
        
        Returns:
            str: Formatted message for Telegram
        """
        message = [
            "<b>PORTFOLIO ALERTS</b>\n",
            "🔔 <b>chainEdge SOL BOT</b>",
            "Portfolio Alerts\n"
        ]
        
        # Add subject
        message.append(f"💡 <b>Subject:</b> {self.subject}")
        
        # Add contract address
        message.append(f"📋 <b>CA:</b> {self.contractAddress}")
        
        # Add token name if available
        if self.tokenName:
            message.append(f"<b>{self.tokenName}</b>")
        
        # Add chain
        message.append(f"⛓ <b>Chain:</b> {self.chain}")
        
        # Add token symbol
        message.append(f"🎰 <b>Token Symbols:</b> {self.symbol}")
        
        # Add balance in USD if available
        if self.balanceUsd:
            formatted_balance = f"${self.balanceUsd:,.2f}K" if self.balanceUsd >= 1000 else f"${self.balanceUsd:,.2f}"
            message.append(f"💰 <b>Bal_USD:</b> {formatted_balance}")
        
        # Add liquidity if available
        if self.liquidity:
            formatted_liquidity = f"${self.liquidity:,.2f}K" if self.liquidity >= 1000 else f"${self.liquidity:,.2f}"
            message.append(f"💧 <b>Liquidity:</b> {formatted_liquidity}")
        
        # Add FDV if available
        if self.fullyDilutedValue:
            formatted_fdv = f"${self.fullyDilutedValue:,.2f}M" if self.fullyDilutedValue >= 1000000 else f"${self.fullyDilutedValue:,.2f}K" if self.fullyDilutedValue >= 1000 else f"${self.fullyDilutedValue:,.2f}"
            message.append(f"📈 <b>FDV:</b> {formatted_fdv}")
        
        # Add current price if available
        if self.currentPrice:
            message.append(f"💵 <b>Latest Price:</b> {self.currentPrice}")
        
        # Add transaction chart info
        message.append(f"📊 <b>Txn Chart:</b> (Click below)")
        
        # Add DexScreener info
        message.append(f"👀 <b>DexScreener:</b> (Click below)")
        
        # Add holder count if available
        if self.holderCount:
            message.append(f"💳 <b># of No of Wallets:</b> {self.holderCount}")
        
        # Join all parts with newlines
        return "\n".join(message)
        
    def getDefaultButtons(self) -> List[dict]:
        """
        Get default buttons for the notification
        
        Returns:
            List[dict]: List of button configurations
        """
        buttons = []
        
        # Add transaction chart button if URL is available
        if self.txnChartUrl:
            buttons.append({
                "text": "Txn Chart", 
                "url": self.txnChartUrl
            })
        else:
            # Use a default URL if none is provided
            buttons.append({
                "text": "Txn Chart", 
                "url": f"https://dexscreener.com/solana/{self.contractAddress}?chart=1"
            })
        
        # Add DexScreener button if URL is available
        if self.dexScreenerUrl:
            buttons.append({
                "text": "DexScreener",
                "url": self.dexScreenerUrl
            })
        else:
            # Use a default URL if none is provided
            buttons.append({
                "text": "DexScreener",
                "url": f"https://dexscreener.com/solana/{self.contractAddress}"
            })
        
        return buttons 