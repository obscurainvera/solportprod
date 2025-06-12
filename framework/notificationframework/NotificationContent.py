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
                "text": f"DS = {self.name}",
                "url": self.dexScreenerUrl
            })
        else:
            # Use a default URL if none is provided
            buttons.append({
                "text": f"DS = {self.name}",
                "url": f"https://dexscreener.com/solana/{self.tokenid}"
            })
            
        buttons.append({
            "text": f"CE = {self.name}",
            "url": f"https://app.chainedge.io/solana/?search={self.tokenid}"
        })
        
        return buttons 
    
    def formatTelegramMessageForOnchainNeweefefef(self) -> str:
        """
        Format the content as a telegram message with HTML table formatting
    
        Returns:
        str: Formatted message for Telegram
        """
        # Define column widths for alignment
        label_width = 20  # Width for labels (e.g., "Subject", "Price")
        value_width = 30  # Width for values (e.g., tokenid, price)

        # Initialize message with header
        message = ["<b>ONCHAIN ALERTS</b>\n", "<pre>"]

        # Table header with borders
        message.append("┌" + "─" * (label_width + value_width + 3) + "┐")
        message.append(f"│ {'Field':<{label_width}}│ {'Value':<{value_width}}│")
        message.append("├" + "─" * (label_width + value_width + 3) + "┤")

        # Add subject
        message.append(f"│ 💡 {'Subject':<{label_width-2}}│ {self.subject:<{value_width}}│")

        # Add contract address
        message.append(f"│ 📋 {'Contract Address':<{label_width-2}}│ {self.tokenid:<{value_width}}│")

        # Add token name if available
        if self.name:
            message.append(f"│ {'Name':<{label_width}}│ {self.name:<{value_width}}│")

        # Add rank
        message.append(f"│ 🏅 {'Rank':<{label_width-2}}│ {self.rank:<{value_width}}│")

        # Add age if available
        if self.age:
            message.append(f"│ ⏳ {'Token Age':<{label_width-2}}│ {self.age:<{value_width}}│")

        # Add count
        message.append(f"│ 🔢 {'Count':<{label_width-2}}│ {self.count:<{value_width}}│")

        # Add price
        formatted_price = f"${self.price:,.4f}".rstrip('0').rstrip('.')
        message.append(f"│ 💵 {'Price':<{label_width-2}}│ {formatted_price:<{value_width}}│")

        # Add liquidity
        formatted_liquidity = f"${self.liquidity:,.2f}K" if self.liquidity >= 1000 else f"${self.liquidity:.4f}".rstrip('0').rstrip('.')
        message.append(f"│ 💧 {'Liquidity':<{label_width-2}}│ {formatted_liquidity:<{value_width}}│")

        # Add makers (as holder count)
        message.append(f"│ 💳 {'Number of Makers':<{label_width-2}}│ {self.makers:<{value_width}}│")

        # Table footer
        message.append("└" + "─" * (label_width + value_width + 3) + "┘")
        message.append("</pre>")

        # Join all parts with newlines
        return "\n".join(message)
    
    
    def formatTelegramMessageForOnchainNew(self) -> str:
        # Define column widths for alignment, reduced for iPhone compatibility
        label_width = 18  # Width for labels
        value_width = 25  # Width for values to fit smaller screens

        # Initialize message with header
        message = ["<b>ONCHAIN ALERTS</b>\n", "<pre>"]

        # Simple table header with minimal borders
        separator = "├" + "─" * (label_width + value_width + 3) + "┤"
        message.append("┌" + "─" * (label_width + value_width + 3) + "┐")
        message.append(f"│ {'Field':<{label_width}}│ {'Value':<{value_width}}│")
        message.append(separator)

        # Add subject (coerce to string and truncate if too long)
        subject_str = str(self.subject) if self.subject is not None else ''
        display_subject = subject_str if len(subject_str) <= value_width else subject_str[:value_width-3] + '...'
        message.append(f"│ 💡 {'Subject':<{label_width-2}}│ {display_subject:<{value_width}}│")
        message.append(separator)

        # Add contract address (tokenid) with <code>, showing first 4 and last 4
        tokenid_str = str(self.tokenid) if self.tokenid is not None else ''
        if tokenid_str and len(tokenid_str) > 8:
            display_tokenid = f"{tokenid_str[:4]}...{tokenid_str[-4:]}"
        else:
            display_tokenid = tokenid_str
        message.append(f"│ 📋 {'Contract Address':<{label_width-2}}│ <code>{tokenid_str}</code>{' ' * (value_width - len(display_tokenid))}│")
        message.append(separator)

        # Add token name if available (coerce to string and truncate if too long)
        if self.name:
            name_str = str(self.name) if self.name is not None else ''
            display_name = name_str if len(name_str) <= value_width else name_str[:value_width-3] + '...'
            message.append(f"│ {'Name':<{label_width}}│ {display_name:<{value_width}}│")
            message.append(separator)

        # Add rank
        message.append(f"│ 🏅 {'Rank':<{label_width-2}}│ {self.rank:<{value_width}}│")
        message.append(separator)

        # Add age if available (coerce to string and truncate if too long)
        if self.age:
            age_str = str(self.age) if self.age is not None else ''
            display_age = age_str if len(age_str) <= value_width else age_str[:value_width-3] + '...'
            message.append(f"│ ⏳ {'Token Age':<{label_width-2}}│ {display_age:<{value_width}}│")
            message.append(separator)

        # Add count
        message.append(f"│ 🔢 {'Count':<{label_width-2}}│ {self.count:<{value_width}}│")
        message.append(separator)

        # Add price
        formatted_price = f"${self.price:,.4f}".rstrip('0').rstrip('.')
        message.append(f"│ 💵 {'Price':<{label_width-2}}│ {formatted_price:<{value_width}}│")
        message.append(separator)

        # Add liquidity
        formatted_liquidity = f"${self.liquidity:,.2f}K" if self.liquidity >= 1000 else f"${self.liquidity:.4f}".rstrip('0').rstrip('.')
        message.append(f"│ 💧 {'Liquidity':<{label_width-2}}│ {formatted_liquidity:<{value_width}}│")
        message.append(separator)

        # Add makers (as holder count)
        message.append(f"│ 💳 {'Number of Makers':<{label_width-2}}│ {self.makers:<{value_width}}│")
        message.append("└" + "─" * (label_width + value_width + 3) + "┘")
        message.append("</pre>")

        # Join all parts with newlines
        return "\n".join(message)