from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from typing import List, Dict, Optional, Any
from datetime import datetime
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from logs.logger import get_logger
import pandas as pd
import json

logger = get_logger(__name__)

class SmartMoneyWalletBehaviourReportHandler(BaseDBHandler):
    """Handler for retrieving wallet behaviour reports from smartmoneywalletbehaviour table"""
    
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        super().__init__(conn_manager)
    
    def getWalletBehaviourReport(self, walletAddress: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the behaviour report for a specific wallet
        
        Args:
            walletAddress: Wallet address to fetch report for
            
        Returns:
            Dictionary containing wallet behaviour data or None if not found
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    SELECT 
                        walletaddress, totalinvestment, numtokens, avginvestmentpertoken,
                        highconvictionnumtokens, highconvictionavginvestment, highconvictionwinrate,
                        highconvictiontotalinvested, highconvictiontotaltakenout, highconvictionpercentagereturn,
                        mediumconvictionnumtokens, mediumconvictionavginvestment, mediumconvictionwinrate,
                        mediumconvictiontotalinvested, mediumconvictiontotaltakenout, mediumconvictionpercentagereturn,
                        lowconvictionnumtokens, lowconvictionavginvestment, lowconvictionwinrate,
                        lowconvictiontotalinvested, lowconvictiontotaltakenout, lowconvictionpercentagereturn,
                        createdtime, analysistime
                    FROM smartmoneywalletbehaviour
                    WHERE walletaddress = ?
                ''', (walletAddress,))
                
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"No behaviour report found for wallet: {walletAddress}")
                    return None
                
                # Convert the row to a dictionary
                columns = [
                    'walletaddress', 'totalinvestment', 'numtokens', 'avginvestmentpertoken',
                    'highconvictionnumtokens', 'highconvictionavginvestment', 'highconvictionwinrate',
                    'highconvictiontotalinvested', 'highconvictiontotaltakenout', 'highconvictionpercentagereturn',
                    'mediumconvictionnumtokens', 'mediumconvictionavginvestment', 'mediumconvictionwinrate',
                    'mediumconvictiontotalinvested', 'mediumconvictiontotaltakenout', 'mediumconvictionpercentagereturn',
                    'lowconvictionnumtokens', 'lowconvictionavginvestment', 'lowconvictionwinrate',
                    'lowconvictiontotalinvested', 'lowconvictiontotaltakenout', 'lowconvictionpercentagereturn',
                    'createdtime', 'analysistime'
                ]
                
                result = dict(zip(columns, row))
                
                # Format the report with additional sections for better organization
                formatted_report = {
                    'walletAddress': result['walletaddress'],
                    'summary': {
                        'totalInvestment': float(result['totalinvestment']),
                        'numTokens': int(result['numtokens']),
                        'avgInvestmentPerToken': float(result['avginvestmentpertoken'])
                    },
                    'highConviction': {
                        'numTokens': int(result['highconvictionnumtokens']),
                        'avgInvestment': float(result['highconvictionavginvestment']),
                        'winRate': float(result['highconvictionwinrate']),
                        'totalInvested': float(result['highconvictiontotalinvested']),
                        'totalTakenOut': float(result['highconvictiontotaltakenout']),
                        'percentageReturn': float(result['highconvictionpercentagereturn'])
                    },
                    'mediumConviction': {
                        'numTokens': int(result['mediumconvictionnumtokens']),
                        'avgInvestment': float(result['mediumconvictionavginvestment']),
                        'winRate': float(result['mediumconvictionwinrate']),
                        'totalInvested': float(result['mediumconvictiontotalinvested']),
                        'totalTakenOut': float(result['mediumconvictiontotaltakenout']),
                        'percentageReturn': float(result['mediumconvictionpercentagereturn'])
                    },
                    'lowConviction': {
                        'numTokens': int(result['lowconvictionnumtokens']),
                        'avgInvestment': float(result['lowconvictionavginvestment']),
                        'winRate': float(result['lowconvictionwinrate']),
                        'totalInvested': float(result['lowconvictiontotalinvested']),
                        'totalTakenOut': float(result['lowconvictiontotaltakenout']),
                        'percentageReturn': float(result['lowconvictionpercentagereturn'])
                    },
                    'timestamps': {
                        'created': result['createdtime'],
                        'lastAnalysis': result['analysistime']
                    }
                }
                
                logger.info(f"Successfully fetched behaviour report for wallet: {walletAddress}")
                return formatted_report
                
        except Exception as e:
            logger.error(f"Failed to fetch wallet behaviour report for {walletAddress}: {str(e)}")
            raise
    
    def getAllWalletsBehaviourSummary(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Retrieve a summary of behaviour reports for all wallets
        
        Args:
            limit: Maximum number of wallets to return
            offset: Number of wallets to skip for pagination
            
        Returns:
            List of dictionaries containing wallet behaviour summaries
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    SELECT 
                        walletaddress, totalinvestment, numtokens, avginvestmentpertoken,
                        highconvictionwinrate, mediumconvictionwinrate, lowconvictionwinrate,
                        highconvictionpercentagereturn, mediumconvictionpercentagereturn, lowconvictionpercentagereturn,
                        analysistime
                    FROM smartmoneywalletbehaviour
                    ORDER BY totalinvestment DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                rows = cursor.fetchall()
                
                # Convert rows to dictionaries with formatted data
                summaries = []
                for row in rows:
                    summary = {
                        'walletAddress': row[0],
                        'totalInvestment': float(row[1]),
                        'numTokens': int(row[2]),
                        'avgInvestmentPerToken': float(row[3]),
                        'winRates': {
                            'high': float(row[4]),
                            'medium': float(row[5]),
                            'low': float(row[6])
                        },
                        'returns': {
                            'high': float(row[7]),
                            'medium': float(row[8]),
                            'low': float(row[9])
                        },
                        'lastAnalysis': row[10]
                    }
                    summaries.append(summary)
                
                logger.info(f"Successfully fetched {len(summaries)} wallet behaviour summaries")
                return summaries
                
        except Exception as e:
            logger.error(f"Failed to fetch wallet behaviour summaries: {str(e)}")
            raise
    
    def getWalletBehaviourHistory(self, walletAddress: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve historical behaviour reports for a specific wallet
        
        Args:
            walletAddress: Wallet address to fetch history for
            limit: Maximum number of historical records to return
            
        Returns:
            List of dictionaries containing historical wallet behaviour data
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    SELECT 
                        walletaddress, totalinvestment, numtokens, 
                        highconvictionwinrate, highconvictionpercentagereturn,
                        mediumconvictionwinrate, mediumconvictionpercentagereturn,
                        lowconvictionwinrate, lowconvictionpercentagereturn,
                        analysistime, archivedtime
                    FROM smartmoneywalletbehaviourhistory
                    WHERE walletaddress = ?
                    ORDER BY archivedtime DESC
                    LIMIT ?
                ''', (walletAddress, limit))
                
                rows = cursor.fetchall()
                
                # Convert rows to dictionaries with formatted data
                history = []
                for row in rows:
                    record = {
                        'walletAddress': row[0],
                        'totalInvestment': float(row[1]),
                        'numTokens': int(row[2]),
                        'highConviction': {
                            'winRate': float(row[3]),
                            'percentageReturn': float(row[4])
                        },
                        'mediumConviction': {
                            'winRate': float(row[5]),
                            'percentageReturn': float(row[6])
                        },
                        'lowConviction': {
                            'winRate': float(row[7]),
                            'percentageReturn': float(row[8])
                        },
                        'analysisTime': row[9],
                        'archivedTime': row[10]
                    }
                    history.append(record)
                
                logger.info(f"Successfully fetched {len(history)} historical records for wallet: {walletAddress}")
                return history
                
        except Exception as e:
            logger.error(f"Failed to fetch wallet behaviour history for {walletAddress}: {str(e)}")
            raise 