"""
Security-sensitive configurations
- Cookie management
- Authentication tokens
- Rate limiting settings
- Service credentials
"""

from datetime import datetime
import json
from typing import Dict, Tuple, List

# Auth Token Configuration
ACCESS_TOKEN_EXPIRY_MINUTES = 15
REFRESH_TOKEN_EXPIRY_HOURS = 12
TOKEN_REFRESH_BUFFER_MINUTES = 1
RELOGIN_BUFFER_MINUTES = 5

# Define the Chainedge cookie
CHAINEDGE_COOKIE = "_ga=GA1.1.60016713.1730025993; __stripe_mid=86d76ae8-5f87-4e05-8e8e-c5eaf0b99f8895f778; _ga_D6FYDK42KW=deleted; csrftoken=hYmCo1WCSpQDePpsXUow4OdGZlbRA68J; sessionid=mq4r2ca9mhue1zizs3fzvjnph7oueonb; _ga_30LVG9BH2W=GS1.1.1743701733.283.1.1743702497.0.0.0; _ga_BRMXHSC2T7=GS1.1.1743701733.243.1.1743702497.0.0.0; _ga_QSLT10C1WE=GS1.1.1743701733.116.1.1743702497.0.0.0; _ga_D6FYDK42KW=GS1.1.1743762563.630.1.1743762565.0.0.0"
SOLSCAN_COOKIE = "_ga=GA1.1.1697493596.1730686033; cf_clearance=b2ngjmgI099YEdPvKkW0BvTaKMPPjPnHGudcFmmkgmo-1743851550-1.2.1.1-daq6DH_oiFRWjs.Aztj43jc7DoLEj.WeQ4q0NoeMtFzeJvazTKkDuuyJsFexZiPfHm8SiuYJIFCnLKX7plY2EpL80j6sm0VJ9YshwaYcktk6xwRH2pnVaRvGhcM.4IBXXkpOxpPBaFeBpVNGA9gmdJ97p.SqIaQQHRyLE4Eg5dr1wBRcB.ZV0xBtXA_3ZmmDg7jm5zKF4rDWiHrY.MHggDYrnMSO8jg22fFueni2qWZBZR0OTgHqP_xS1sflpY4gJ1WWBwvVGMXBVvO2Z_D3DXywAM2eutfoohh_IbW_Bz4wjfFKLzFi_FbeQgtiVc.8d67InwXxvgWoVeCDnawIlsKbW1oi8XOnvI67mjcaOPeXErQ9Y3qNOibSMD03bVQU; _ga_PS3V7B7KV0=GS1.1.1743851550.246.0.1743851550.0.0.0"
TRADING_TERMINAL_COOKIE = "_ga=GA1.1.60016713.1730025993; _ga_30LVG9BH2W=deleted; _ga_QSLT10C1WE=deleted; wallet_created=true; wallet_exported=true; passkey_wallet=true; refreshToken=undefined; _ga_D6FYDK42KW=GS1.1.1743506365.611.1.1743506835.0.0.0; accessToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQzNTA3ODQ5LCJpYXQiOjE3NDMzMTIwODksImp0aSI6Ijg4NThlMGRiODM2NDQ4YTE4ZGYzZTcxYWUyMThmZWQwIiwidXNlcl9pZCI6MTQ2MCwid2FsbGV0X2NyZWF0ZWQiOnRydWUsIndhbGxldF9leHBvcnRlZCI6dHJ1ZSwicGFzc2tleV93YWxsZXQiOnRydWUsInJlZmVycmVyX2xpbmsiOiIiLCJyZWZlcnJlcl92YWxpZCI6ZmFsc2V9.rEnYGufiUsV2R8-yP_MBVNxTevtNk2Wc_AczMxRUAKE; _ga_30LVG9BH2W=GS1.1.1743506945.272.1.1743506952.0.0.0; _ga_BRMXHSC2T7=GS1.1.1743506945.232.1.1743506952.0.0.0; _ga_QSLT10C1WE=GS1.1.1743506945.105.1.1743506952.0.0.0"


COOKIE_MAP = {
    # Action-specific cookies
    "portfolio": {CHAINEDGE_COOKIE: {"expiry": datetime(2025, 4, 6)}},
    "walletsinvested": {CHAINEDGE_COOKIE: {"expiry": datetime(2025, 4, 6)}},
    "solscan": {SOLSCAN_COOKIE: {"expiry": datetime(2025, 4, 6)}},
    "smartmoneywallets": {CHAINEDGE_COOKIE: {"expiry": datetime(2025, 4, 5)}},
    "smwallettoppnltoken": {CHAINEDGE_COOKIE: {"expiry": datetime(2025, 4, 4)}},
    "attention": {CHAINEDGE_COOKIE: {"expiry": datetime(2025, 4, 6)}},
    "volumebot": {
        TRADING_TERMINAL_COOKIE: {"expiry": datetime(2025, 3, 28)},
    },
    "pumpfun": {TRADING_TERMINAL_COOKIE: {"expiry": datetime(2025, 3, 28)}},
}


def isValidCookie(cookie_value: str, required_action: str = None) -> bool:
    """Validate cookie in 3 steps:
    1. Check cookie exists for the required action
    2. Verify not expired
    3. Return True if all checks pass"""

    # 1. Check cookie exists for the action
    service = COOKIE_MAP.get(required_action, {}) if required_action else None
    if not service or cookie_value not in service:
        return False

    cookie_data = service[cookie_value]

    # 2. Check expiry time
    if datetime.now() > cookie_data.get("expiry", datetime.min):
        return False

    # 3. All checks passed
    return True


def isCookieExpired(cookie_expiry_time: str) -> bool:
    """Check if a cookie is expired by comparing with current datetime
    Args:
        cookie_expiry_time (str): Date string in format 'YYYY-MM-DD'
    Returns:
        bool: True if cookie is expired, False otherwise
    """

    expiry_date = datetime.strptime(cookie_expiry_time, "%Y-%m-%d")
    return datetime.now() > expiry_date
