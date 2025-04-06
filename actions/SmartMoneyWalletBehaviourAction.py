from config.Config import get_config
# actions/smwallet_behaviour_action.py
from database.operations.PortfolioDB import PortfolioDB
from database.smwalletsbehaviour.SmartMoneyWalletBehaviourHandler import SmartMoneyWalletBehaviourHandler
from database.operations.schema import SmartMoneyWalletBehaviour
from actions.DexscrennerAction import DexScreenerAction
from utils.constants import SOL_TOKEN_ID, DEFAULT_TOKEN_IDS
from logs.logger import get_logger
from datetime import datetime
import pandas as pd
from sklearn.cluster import KMeans
from typing import List, Optional, Dict

logger = get_logger(__name__)

class SmartMoneyWalletBehaviourAction:
    """Handles SM wallet investment behavior analysis workflow"""
    
    def __init__(self, db: PortfolioDB):
        self.db = db
        self.handler = SmartMoneyWalletBehaviourHandler(db.conn_manager)
        self.dexscreener = DexScreenerAction()

    def analyzeWalletBehaviour(self, walletAddress: Optional[str] = None) -> bool:
        """Execute wallet behavior analysis, optionally for a specific wallet"""
        try:
            logger.info(f"Starting Smart Money Wallet Behaviour analysis{' for wallet ' + walletAddress if walletAddress else ' for all wallets'}")
            # Pass DEFAULT_TOKEN_IDS list to always include SOL token in the analysis
            df = self.handler.getWalletInvestmentData(walletAddress, DEFAULT_TOKEN_IDS)
            if df.empty:
                logger.warning("No data available for analysis")
                return False

            # Prepare data for clustering
            df = self._prepareData(df)
            if df.empty:
                logger.warning("No valid investment data after preparation")
                return False

            # Perform K-means clustering
            df = self._applyKMeansClustering(df)

            # Compute metrics and build analysis objects 
            analysisList = self._computeMetrics(df)
            if not analysisList:
                logger.warning("No analysis results generated")
                return False

            # Store results with history preservation
            self.handler.storeAnalysisResults(analysisList)
            logger.info(f"Smart Money Wallet Behaviour analysis completed successfully for {len(analysisList)} wallets")
            return True

        except Exception as e:
            logger.error(f"Smart Money Wallet Behaviour analysis failed: {str(e)}")
            return False

    def _prepareData(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data: calculate realized PNL and fetch token prices"""
        df['amounttakenout'] = df['amounttakenout'].fillna(0)
        df['remainingcoins'] = df['remainingcoins'].fillna(0)

        # Calculate realized PNL
        df['realizedPnl'] = df['amounttakenout'] - df['amountinvested']

        # Fetch token prices for tokens with remainingcoins != 0 using DexscrennerAction
        tokenIdsWithCoins = df[df['remainingcoins'] != 0]['tokenid'].unique().tolist()
        if tokenIdsWithCoins:
            logger.info(f"Fetching prices for {len(tokenIdsWithCoins)} tokens using DexScreener batch API")
            
            # Get batch token prices
            tokenPrices = self.dexscreener.getBatchTokenPrices(tokenIdsWithCoins)
            
            # Create price mapping dictionary
            priceMap = {}
            for tokenId, priceData in tokenPrices.items():
                if priceData is not None:
                    priceMap[tokenId] = priceData.price
                else:
                    priceMap[tokenId] = 0
            
            # Map prices to dataframe
            df['tokenPrice'] = df['tokenid'].map(priceMap).fillna(0)
            df['unrealizedPnl'] = df['remainingcoins'] * df['tokenPrice']
            
            logger.info(f"Successfully mapped prices for {sum(1 for p in priceMap.values() if p > 0)} tokens")
        else:
            df['tokenPrice'] = 0
            df['unrealizedPnl'] = 0
            logger.info("No tokens with remaining coins to fetch prices for")

        # Calculate total PNL
        df['totalPnl'] = df['realizedPnl'] + df['unrealizedPnl']
        return df

    def _applyKMeansClustering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply K-means clustering to categorize investments into 3 clusters"""
        X = df[['amountinvested']].values
        kmeans = KMeans(n_clusters=3, random_state=42)
        df['cluster'] = kmeans.fit_predict(X)

        # Assign clusters to high, medium, low based on centroid means
        centroids = kmeans.cluster_centers_.flatten()
        cluster_map = {i: rank for i, rank in enumerate(sorted(range(3), key=lambda x: centroids[x], reverse=True))}
        df['convictionLevel'] = df['cluster'].map({cluster_map[0]: 'high', cluster_map[1]: 'medium', cluster_map[2]: 'low'})
        return df

    def _computeMetrics(self, df: pd.DataFrame) -> List[SmartMoneyWalletBehaviour]:
        """Compute investment metrics for all wallets"""
        analysisList = []
        for walletAddress, group in df.groupby('walletaddress'):
            totalInvestment = group['amountinvested'].sum()
            numTokens = len(group)
            if numTokens == 0 or totalInvestment == 0:
                analysisList.append(SmartMoneyWalletBehaviour(
                    walletaddress=walletAddress,
                    totalinvestment=0,
                    numtokens=0,
                    avginvestmentpertoken=0,
                    highconvictionnumtokens=0,
                    highconvictionavginvestment=0,
                    highconvictionwinrate=0,
                    highconvictiontotalinvested=0,
                    highconvictiontotaltakenout=0,
                    highconvictionpercentagereturn=0,
                    mediumconvictionnumtokens=0,
                    mediumconvictionavginvestment=0,
                    mediumconvictionwinrate=0,
                    mediumconvictiontotalinvested=0,
                    mediumconvictiontotaltakenout=0,
                    mediumconvictionpercentagereturn=0,
                    lowconvictionnumtokens=0,
                    lowconvictionavginvestment=0,
                    lowconvictionwinrate=0,
                    lowconvictiontotalinvested=0,
                    lowconvictiontotaltakenout=0,
                    lowconvictionpercentagereturn=0,
                    analysistime=datetime.now()
                ))
                continue

            avgInvestmentPerToken = totalInvestment / numTokens

            # Group by conviction level
            highGroup = group[group['convictionLevel'] == 'high']
            medGroup = group[group['convictionLevel'] == 'medium']
            lowGroup = group[group['convictionLevel'] == 'low']

            # Compute metrics per cluster
            def computeClusterMetrics(clusterDf):
                if clusterDf.empty:
                    return {
                        'numTokens': 0,
                        'avgInvestment': 0,
                        'winRate': 0,
                        'totalInvested': 0,
                        'totalTakenOut': 0,
                        'percentageReturn': 0
                    }
                numTokens = len(clusterDf)
                avgInvestment = clusterDf['amountinvested'].mean() or 0
                winRate = (clusterDf['realizedPnl'] > 0).mean() * 100 if numTokens > 0 else 0
                totalInvested = clusterDf['amountinvested'].sum()
                totalTakenOut = clusterDf['amounttakenout'].sum()
                percentageReturn = ((totalTakenOut - totalInvested) / totalInvested * 100) if totalInvested > 0 else 0
                return {
                    'numTokens': numTokens,
                    'avgInvestment': avgInvestment,
                    'winRate': winRate,
                    'totalInvested': totalInvested,
                    'totalTakenOut': totalTakenOut,
                    'percentageReturn': percentageReturn
                }

            highMetrics = computeClusterMetrics(highGroup)
            medMetrics = computeClusterMetrics(medGroup)
            lowMetrics = computeClusterMetrics(lowGroup)

            analysisList.append(SmartMoneyWalletBehaviour(
                walletaddress=walletAddress,
                totalinvestment=totalInvestment,
                numtokens=numTokens,
                avginvestmentpertoken=avgInvestmentPerToken,
                highconvictionnumtokens=highMetrics['numTokens'],
                highconvictionavginvestment=highMetrics['avgInvestment'],
                highconvictionwinrate=highMetrics['winRate'],
                highconvictiontotalinvested=highMetrics['totalInvested'],
                highconvictiontotaltakenout=highMetrics['totalTakenOut'],
                highconvictionpercentagereturn=highMetrics['percentageReturn'],
                mediumconvictionnumtokens=medMetrics['numTokens'],
                mediumconvictionavginvestment=medMetrics['avgInvestment'],
                mediumconvictionwinrate=medMetrics['winRate'],
                mediumconvictiontotalinvested=medMetrics['totalInvested'],
                mediumconvictiontotaltakenout=medMetrics['totalTakenOut'],
                mediumconvictionpercentagereturn=medMetrics['percentageReturn'],
                lowconvictionnumtokens=lowMetrics['numTokens'],
                lowconvictionavginvestment=lowMetrics['avgInvestment'],
                lowconvictionwinrate=lowMetrics['winRate'],
                lowconvictiontotalinvested=lowMetrics['totalInvested'],
                lowconvictiontotaltakenout=lowMetrics['totalTakenOut'],
                lowconvictionpercentagereturn=lowMetrics['percentageReturn'],
                analysistime=datetime.now()
            ))
        return analysisList