from config.Config import get_config
"""
Notification content models for structured messages
"""
from dataclasses import dataclass, field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


@dataclass
class TokenNotificationContent:
    """
    Structured content for token notifications
    """
    """
    Structured content for token notifications, aligned with OnchainInfo plus DexScreener URL
    """
    # Required fields from OnchainInfo
    subject: str  # Notification subject
    tokenid: str
    name: str
    chain: str
    price: Decimal
    marketcap: Decimal
    liquidity: Decimal
    makers: int
    rank: int
    
    # Optional fields from OnchainInfo
    id: Optional[int] = None
    onchaininfoid: Optional[int] = None
    age: Optional[str] = None
    count: int = 1
    createdat: Optional[datetime] = None
    updatedat: Optional[datetime] = None
    
    # DexScreener URL from original TokenNotificationContent
    dexScreenerUrl: Optional[str] = None
    
    def formatTelegramMessageForOnchain(self) -> str:
        """
        Format the content as a telegram message with HTML formatting
        
        Returns:
            str: Formatted message for Telegram
        """
        message = [
            "<b>ONCHAIN ALERTS</b>\n"
        ]
        
        # Add subject
        message.append(f"💡 <b>Subject:</b> {self.subject}")
        
        # Add contract address
        message.append(f"📋 <b>Contract Address:</b> {self.tokenid}")
        
        # Add token name if available
        if self.name:
            message.append(f"<b>Name :</b> {self.name}")
            
        # Add rank
        message.append(f"🏅 <b>Rank:</b> {self.rank}")
    
        # Add age if available
        if self.age:
            message.append(f"⏳ <b>Token Age:</b> {self.age}")
    
        # Add count
        message.append(f"🔢 <b>Count:</b> {self.count}")
        
        # Add price
        message.append(f"💵 <b>Price:</b> ${self.price}")
        
        # Add liquidity
        formatted_liquidity = f"${self.liquidity:,.2f}K" if self.liquidity >= 1000 else f"${self.liquidity:,.2f}"
        message.append(f"💧 <b>Liquidity:</b> {formatted_liquidity}")
    
        # Add makers (as holder count)
        message.append(f"💳 <b>Number of Makers:</b> {self.makers}")
        
        # Join all parts with newlines
        return "\n".join(message)
        
    def getDefaultButtons(self) -> List[dict]:
        """
        Get default buttons for the notification
        
        Returns:
            List[dict]: List of button configurations
        """
        buttons = []
        
        # Add DexScreener button if URL is available
        if self.dexScreenerUrl:
            buttons.append({
                "text": "DexScreener",
                "url": self.dexScreenerUrl
            })
        else:
            # Use a default URL if none is provided
            buttons.append({
                "text": f"DexScreener = {self.name}",
                "url": f"https://dexscreener.com/solana/{self.tokenid}"
            })
            
        buttons.append({
            "text": f"Chainedge = {self.name}",
            "url": f"https://app.chainedge.io/solana/?search={self.tokenid}"
        })
        
        return buttons 