from config.Config import get_config
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from database.operations.BaseDBHandler import BaseDBHandler
from typing import List, Optional
from datetime import datetime
from logs.logger import get_logger
import pandas as pd
from database.operations.schema import SmartMoneyWalletBehaviour

logger = get_logger(__name__)

class SmartMoneyWalletBehaviourHandler(BaseDBHandler):
    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = DatabaseConnectionManager()
        super().__init__(conn_manager)
        self._createTables()

    def _createTables(self):
        """Create the smartmoneywalletbehaviour and history tables"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute('''
                create table if not exists smartmoneywalletbehaviour (
                    walletaddress text primary key,
                    totalinvestment decimal,
                    numtokens integer,
                    avginvestmentpertoken decimal,
                    highconvictionnumtokens integer,
                    highconvictionavginvestment decimal,
                    highconvictionwinrate decimal,
                    highconvictiontotalinvested decimal,
                    highconvictiontotaltakenout decimal,
                    highconvictionpercentagereturn decimal,
                    mediumconvictionnumtokens integer,
                    mediumconvictionavginvestment decimal,
                    mediumconvictionwinrate decimal,
                    mediumconvictiontotalinvested decimal,
                    mediumconvictiontotaltakenout decimal,
                    mediumconvictionpercentagereturn decimal,
                    lowconvictionnumtokens integer,
                    lowconvictionavginvestment decimal,
                    lowconvictionwinrate decimal,
                    lowconvictiontotalinvested decimal,
                    lowconvictiontotaltakenout decimal,
                    lowconvictionpercentagereturn decimal,
                    createdtime timestamp default current_timestamp,
                    analysistime timestamp
                )
            ''')
            cursor.execute('''
                create table if not exists smartmoneywalletbehaviourhistory (
                    historyid integer primary key autoincrement,
                    walletaddress text,
                    totalinvestment decimal,
                    numtokens integer,
                    avginvestmentpertoken decimal,
                    highconvictionnumtokens integer,
                    highconvictionavginvestment decimal,
                    highconvictionwinrate decimal,
                    highconvictiontotalinvested decimal,
                    highconvictiontotaltakenout decimal,
                    highconvictionpercentagereturn decimal,
                    mediumconvictionnumtokens integer,
                    mediumconvictionavginvestment decimal,
                    mediumconvictionwinrate decimal,
                    mediumconvictiontotalinvested decimal,
                    mediumconvictiontotaltakenout decimal,
                    mediumconvictionpercentagereturn decimal,
                    lowconvictionnumtokens integer,
                    lowconvictionavginvestment decimal,
                    lowconvictionwinrate decimal,
                    lowconvictiontotalinvested decimal,
                    lowconvictiontotaltakenout decimal,
                    lowconvictionpercentagereturn decimal,
                    createdtime timestamp,
                    analysistime timestamp,
                    archivedtime timestamp default current_timestamp
                )
            ''')
            logger.info("SMWallet behaviour tables ensured")

    def getWalletInvestmentData(self, walletAddress: Optional[str] = None, tokensToBeExcluded: Optional[List[str]] = None) -> pd.DataFrame:
        """Fetch investment data from smwallettoppnltoken, optionally for a specific wallet and excluding specified tokens"""
        try:
            # Build the base query
            query = """
                SELECT walletaddress, tokenid, amountinvested, amounttakenout, remainingcoins
                FROM smwallettoppnltoken
                WHERE amountinvested > 0
            """
            
            # Initialize params list
            params = []
            
            # Add wallet address filter if provided
            if walletAddress:
                query += " AND walletaddress = ?"
                params.append(walletAddress)
            
            # Add token exclusion if provided
            if tokensToBeExcluded and len(tokensToBeExcluded) > 0:
                # Create placeholders for each token to exclude
                placeholders = ','.join(['?' for _ in tokensToBeExcluded])
                query += f" AND tokenid NOT IN ({placeholders})"
                # Add token IDs to params
                params.extend(tokensToBeExcluded)
            
            logger.info(f"Executing query: {query}")
            logger.info(f"With params: {params}")
            
            with self.conn_manager.transaction() as cursor:
                cursor.execute(query, params)
                
                # Fetch all rows as a list of dictionaries
                columns = ['walletaddress', 'tokenid', 'amountinvested', 'amounttakenout', 'remainingcoins']
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Convert to DataFrame
                df = pd.DataFrame(rows)
                
                exclusion_info = ""
                if tokensToBeExcluded and len(tokensToBeExcluded) > 0:
                    exclusion_info = f" (excluding {len(tokensToBeExcluded)} tokens)"
                
                logger.info(f"Fetched {len(df)} records from smwallettoppnltoken for {'wallet ' + walletAddress if walletAddress else 'all wallets'}{exclusion_info}")
                return df if not df.empty else pd.DataFrame(columns=columns)
        except Exception as e:
            logger.error(f"Failed to fetch wallet investment data: {str(e)}")
            raise

    def getExistingAnalysis(self, walletAddress: str) -> Optional[tuple]:
        """Fetch existing analysis record for a wallet"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    SELECT *
                    FROM smartmoneywalletbehaviour
                    WHERE walletaddress = ?
                ''', (walletAddress,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Failed to fetch existing analysis for {walletAddress}: {str(e)}")
            return None

    def archiveExistingAnalysis(self, existingRecord: tuple):
        """Move existing analysis record to history table before update"""
        if not existingRecord:
            return
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    INSERT INTO smartmoneywalletbehaviourhistory (
                        walletaddress, totalinvestment, numtokens, avginvestmentpertoken,
                        highconvictionnumtokens, highconvictionavginvestment, highconvictionwinrate,
                        highconvictiontotalinvested, highconvictiontotaltakenout, highconvictionpercentagereturn,
                        mediumconvictionnumtokens, mediumconvictionavginvestment, mediumconvictionwinrate,
                        mediumconvictiontotalinvested, mediumconvictiontotaltakenout, mediumconvictionpercentagereturn,
                        lowconvictionnumtokens, lowconvictionavginvestment, lowconvictionwinrate,
                        lowconvictiontotalinvested, lowconvictiontotaltakenout, lowconvictionpercentagereturn,
                        createdtime, analysistime
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', existingRecord[0:])  # Exclude rowid if present
            logger.info(f"Archived existing analysis for wallet {existingRecord[0]}")
        except Exception as e:
            logger.error(f"Failed to archive analysis for {existingRecord[0]}: {str(e)}")
            raise

    def storeAnalysisResults(self, analyses: List[SmartMoneyWalletBehaviour]):
        """Store or update analysis results in the database, preserving createdtime for existing records"""
        try:
            with self.conn_manager.transaction() as cursor:
                for analysis in analyses:
                    # Check if record already exists
                    existing = self.getExistingAnalysis(analysis.walletaddress)
                    if existing:
                        # For existing records, preserve the original created time
                        # Archive the existing record first
                        self.archiveExistingAnalysis(existing)
                        
                        # Get the original created time (index 22)
                        createdTime = existing[22]
                        logger.info(f"Updating existing record for wallet {analysis.walletaddress}, preserving created time: {createdTime}")
                    else:
                        # For new records, set the created time to now
                        createdTime = datetime.now()
                        logger.info(f"Creating new record for wallet {analysis.walletaddress} with created time: {createdTime}")

                    # Always set analysis time to now, as this represents when the analysis was performed
                    analysisTime = datetime.now()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO smartmoneywalletbehaviour (
                            walletaddress, totalinvestment, numtokens, avginvestmentpertoken,
                            highconvictionnumtokens, highconvictionavginvestment, highconvictionwinrate,
                            highconvictiontotalinvested, highconvictiontotaltakenout, highconvictionpercentagereturn,
                            mediumconvictionnumtokens, mediumconvictionavginvestment, mediumconvictionwinrate,
                            mediumconvictiontotalinvested, mediumconvictiontotaltakenout, mediumconvictionpercentagereturn,
                            lowconvictionnumtokens, lowconvictionavginvestment, lowconvictionwinrate,
                            lowconvictiontotalinvested, lowconvictiontotaltakenout, lowconvictionpercentagereturn,
                            createdtime, analysistime
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        analysis.walletaddress, analysis.totalinvestment, analysis.numtokens,
                        analysis.avginvestmentpertoken, analysis.highconvictionnumtokens,
                        analysis.highconvictionavginvestment, analysis.highconvictionwinrate,
                        analysis.highconvictiontotalinvested, analysis.highconvictiontotaltakenout,
                        analysis.highconvictionpercentagereturn, analysis.mediumconvictionnumtokens,
                        analysis.mediumconvictionavginvestment, analysis.mediumconvictionwinrate,
                        analysis.mediumconvictiontotalinvested, analysis.mediumconvictiontotaltakenout,
                        analysis.mediumconvictionpercentagereturn, analysis.lowconvictionnumtokens,
                        analysis.lowconvictionavginvestment, analysis.lowconvictionwinrate,
                        analysis.lowconvictiontotalinvested, analysis.lowconvictiontotaltakenout,
                        analysis.lowconvictionpercentagereturn, createdTime, analysisTime
                    ))
            logger.info(f"Stored/updated analysis for {len(analyses)} wallets")
        except Exception as e:
            logger.error(f"Failed to store analysis results: {str(e)}")
            raise