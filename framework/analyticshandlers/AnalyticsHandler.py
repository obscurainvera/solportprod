from config.Config import get_config
from database.operations.BaseDBHandler import BaseDBHandler
from database.operations.DatabaseConnectionManager import DatabaseConnectionManager
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime
from logs.logger import get_logger
from framework.analyticsframework.enums.ExecutionStatusEnum import ExecutionStatus
from framework.analyticsframework.enums.TradeTypeEnum import TradeType
from framework.analyticsframework.enums.PushSourceEnum import PushSource
from framework.analyticsframework.models.BaseModels import (
    ExecutionState,
    BaseStrategyConfig,
)
from framework.analyticsframework.models.StrategyModels import (
    InvestmentInstructions,
    ProfitTakingInstructions,
    RiskManagementInstructions,
)
from framework.analyticsframework.models.BaseModels import TradeLog
import json
from sqlalchemy import text
from framework.analyticsframework.models.StrategyModels import TokenConvictionEnum
from framework.analyticsframework.models.BaseModels import BaseStrategyConfig

logger = get_logger(__name__)


class AnalyticsHandler(BaseDBHandler):
    """Handles strategy analytics data operations"""

    def __init__(self, conn_manager):
        super().__init__(conn_manager)
        self._createTables()

    def _createTables(self):
        """Creates all required tables for strategy analytics"""
        with self.conn_manager.transaction() as cursor:
            config = get_config()

            # Strategy Configuration
            # status INTEGER DEFAULT 1 - to represent whether the execution monitor should try to invest again even if the initial try fails
            # active INTEGER DEFAULT 1 - to represent whether the strategy is active or not
            # superuser INTEGER DEFAULT 0 -
            if config.DB_TYPE == "postgres":
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS strategyconfig (
                        strategyid SERIAL PRIMARY KEY,
                        strategyname TEXT NOT NULL,
                        source TEXT NOT NULL,
                        description TEXT,
                        strategyentryconditions TEXT NOT NULL,
                        chartconditions TEXT,
                        investmentinstructions TEXT NOT NULL,
                        profittakinginstructions TEXT NOT NULL,
                        riskmanagementinstructions TEXT NOT NULL,
                        moonbaginstructions TEXT,
                        additionalinstructions TEXT,
                        status INTEGER DEFAULT 1,
                        active INTEGER DEFAULT 1,
                        superuser INTEGER DEFAULT 0,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Strategy execution table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS strategyexecution (
                        executionid SERIAL PRIMARY KEY,
                        strategyid INTEGER NOT NULL,
                        description TEXT,
                        tokenid TEXT NOT NULL,
                        tokenname TEXT NOT NULL,
                        avgentryprice DECIMAL,
                        remainingcoins DECIMAL,
                        allotedamount DECIMAL NOT NULL,
                        investedamount DECIMAL,
                        amounttakenout DECIMAL,
                        realizedpnl DECIMAL,
                        realizedpnlpercent DECIMAL,
                        status INTEGER NOT NULL,
                        notes TEXT,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (strategyid) REFERENCES strategyconfig(strategyid)
                    )
                """
                )

                # Trade log table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tradelog (
                        tradeid SERIAL PRIMARY KEY,
                        executionid INTEGER NOT NULL,
                        tokenid TEXT NOT NULL,
                        tokenname TEXT NOT NULL,
                        tradetype TEXT NOT NULL,
                        amount DECIMAL NOT NULL,
                        tokenprice DECIMAL NOT NULL,
                        coins DECIMAL NOT NULL,
                        description TEXT,
                        createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (executionid) REFERENCES strategyexecution(executionid)
                    )
                """
                )

            logger.info("Analytics tables created successfully")

    def createStrategy(self, strategyConfig: Dict[str, Any]) -> Optional[int]:
        """Create a new strategy configuration"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                params = (
                    strategyConfig["strategyname"],
                    strategyConfig["source"],
                    strategyConfig.get("description"),
                    strategyConfig["strategyentryconditions"],
                    strategyConfig.get("chartconditions"),
                    strategyConfig["investmentinstructions"],
                    strategyConfig["profittakinginstructions"],
                    strategyConfig["riskmanagementinstructions"],
                    strategyConfig.get("moonbaginstructions"),
                    strategyConfig.get("additionalinstructions"),
                    strategyConfig.get("status", TokenConvictionEnum.HIGH.value),
                    strategyConfig.get("active", 1),
                    1 if strategyConfig.get("superuser", False) else 0,
                    strategyConfig.get("createdat", datetime.now()),
                    strategyConfig.get("updatedat", datetime.now()),
                )

                if config.DB_TYPE == "postgres":
                    query = text(
                        """
                        INSERT INTO strategyconfig (
                            strategyname, source, description,
                            strategyentryconditions, chartconditions, investmentinstructions,
                            profittakinginstructions, riskmanagementinstructions,
                            moonbaginstructions, additionalinstructions, status, active, superuser, createdat, updatedat
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING strategyid
                    """
                    )
                    result = cursor.execute(query, params)
                    row = result.fetchone()
                    return row[0] if row else None
                else:
                    query = """
                        INSERT INTO strategyconfig (
                            strategyname, source, description,
                            strategyentryconditions, chartconditions, investmentinstructions,
                            profittakinginstructions, riskmanagementinstructions,
                            moonbaginstructions, additionalinstructions, status, active, superuser, createdat, updatedat
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(query, params)
                    return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create strategy: {str(e)}")
            return None

    def getAllActiveStrategies(self, source: str, pushSource: PushSource = PushSource.SCHEDULER) -> List[Dict]:
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                # If token was pushed via API, include only superuser strategies
                # If token was pushed via Scheduler, include only non-superuser strategies
                if (config.DB_TYPE == "postgres"):  # there is no need to add 'status' param here as we use status to identify whether we need to try again for investement if the initial entry fails
                    if pushSource == PushSource.API:
                        query = text(
                            """
                            SELECT * FROM strategyconfig 
                            WHERE source = %s AND active = 1 AND superuser = 1
                        """
                        )
                        params = (source,)
                    else:
                        query = text(
                            """
                            SELECT * FROM strategyconfig 
                            WHERE source = %s AND active = 1 AND superuser = 0
                        """
                        )
                        params = (source,)
                    cursor.execute(query, params)

                columns = [col[0] for col in cursor.description]
                strategies = []

                for row in cursor.fetchall():
                    strategy_dict = dict(zip(columns, row))
                    # Convert superuser from int to bool
                    strategy_dict["superuser"] = bool(strategy_dict["superuser"])
                    strategies.append(strategy_dict)

                return strategies
        except Exception as e:
            logger.error(f"Failed to get active strategies: {str(e)}")
            return []

    def recordExecution(self, executionData: ExecutionState) -> Optional[int]:
        """
        Record a new strategy execution

        Args:
            executionData: Execution state data

        Returns:
            Optional[int]: Execution ID if successful, None otherwise
        """
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                params = (
                    executionData.strategyid,
                    executionData.tokenid,
                    executionData.tokenname,
                    executionData.status.value,
                    str(executionData.allotedamount),
                    executionData.description,
                    (
                        str(executionData.remainingcoins)
                        if executionData.remainingcoins is not None
                        else None
                    ),
                    (
                        str(executionData.investedamount)
                        if executionData.investedamount is not None
                        else None
                    ),
                    (
                        str(executionData.avgentryprice)
                        if executionData.avgentryprice is not None
                        else None
                    ),
                    (
                        str(executionData.realizedpnl)
                        if executionData.realizedpnl is not None
                        else None
                    ),
                    (
                        str(executionData.realizedpnlpercent)
                        if executionData.realizedpnlpercent is not None
                        else None
                    ),
                    executionData.notes,
                    executionData.createdat,
                    executionData.updatedat,
                )

                if config.DB_TYPE == "postgres":
                    query = text(
                        """
                        INSERT INTO strategyexecution (
                            strategyid, tokenid, tokenname, status, allotedamount,
                            description, remainingcoins, investedamount, avgentryprice,
                            realizedpnl, realizedpnlpercent, notes, createdat, updatedat
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING executionid
                    """
                    )
                    result = cursor.execute(query, params)
                    row = result.fetchone()
                    executionId = row[0] if row else None
                else:
                    query = """
                        INSERT INTO strategyexecution (
                            strategyid, tokenid, tokenname, status, allotedamount,
                            description, remainingcoins, investedamount, avgentryprice,
                            realizedpnl, realizedpnlpercent, notes, createdat, updatedat
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(query, params)
                    executionId = cursor.lastrowid

                logger.info(f"Recorded execution with ID: {executionId}")
                return executionId

        except Exception as e:
            logger.error(f"Failed to record execution: {str(e)}")
            return None

    def logTrade(self, tradeData: TradeLog) -> Optional[int]:
        """
        Log a trade for an execution

        Args:
            tradeData: Trade log data

        Returns:
            Optional[int]: Trade ID if successful, None otherwise
        """
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                params = (
                    tradeData.executionid,
                    tradeData.tokenid,
                    tradeData.tokenname,
                    tradeData.tradetype,
                    str(tradeData.amount),
                    str(tradeData.tokenprice),
                    str(tradeData.coins),
                    tradeData.description,
                    datetime.now(),
                    datetime.now(),
                )

                if config.DB_TYPE == "postgres":
                    query = text(
                        """
                        INSERT INTO tradelog (
                            executionid, tokenid, tokenname, tradetype,
                            amount, tokenprice, coins, description,
                            createdat, updatedat
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING tradeid
                    """
                    )
                    result = cursor.execute(query, params)
                    row = result.fetchone()
                    tradeId = row[0] if row else None
                else:
                    query = """
                        INSERT INTO tradelog (
                            executionid, tokenid, tokenname, tradetype,
                            amount, tokenprice, coins, description,
                            createdat, updatedat
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    cursor.execute(query, params)
                    tradeId = cursor.lastrowid

                logger.info(f"Logged trade with ID: {tradeId}")
                return tradeId

        except Exception as e:
            logger.error(f"Failed to log trade: {str(e)}")
            return None

    def getStrategyExecutions(self, strategyId: int) -> List[Dict]:
        """Get all executions for a strategy"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == "postgres":
                    query = text(
                        "SELECT * FROM strategyexecution WHERE strategyid = %s"
                    )
                    params = (strategyId,)
                    cursor.execute(query, params)
                else:
                    query = "SELECT * FROM strategyexecution WHERE strategyid = ?"
                    params = (strategyId,)
                    cursor.execute(query, params)

                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get strategy executions: {str(e)}")
            return []

    def getExecutionTrades(self, executionId: int) -> List[Dict]:
        """Get all trades for an execution"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == "postgres":
                    query = text(
                        "SELECT * FROM tradelog WHERE executionid = %s ORDER BY createdat ASC"
                    )
                    params = (executionId,)
                    cursor.execute(query, params)
                else:
                    query = "SELECT * FROM tradelog WHERE executionid = ? ORDER BY createdat ASC"
                    params = (executionId,)
                    cursor.execute(query, params)

                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get execution trades: {str(e)}")
            return []

    def updateExecutionPnl(
        self, executionId: int, realizedPnl: Decimal, realizedPnlPct: Decimal
    ) -> bool:
        """Update realized PNL for an execution"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                params = (
                    str(realizedPnl),
                    str(realizedPnlPct),
                    datetime.now(),
                    executionId,
                )
                if config.DB_TYPE == "postgres":
                    query = text(
                        """
                        UPDATE strategyexecution SET 
                        realizedpnl = %s, 
                        realizedpnlpercent = %s,
                        updatedat = %s 
                        WHERE executionid = %s
                    """
                    )
                    cursor.execute(query, params)
                else:
                    query = """
                        UPDATE strategyexecution SET 
                        realizedpnl = ?, 
                        realizedpnlpercent = ?,
                        updatedat = ? 
                        WHERE executionid = ?    
                    """
                    cursor.execute(query, params)
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update execution PNL: {str(e)}")
            return False

    def updateStrategy(self, strategyId: int, updateData: Dict[str, Any]) -> bool:
        """Update a strategy configuration"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                setClauses = []
                params = []

                for key, value in updateData.items():
                    if key in ["strategyid", "createdat"]:  # Skip immutable fields
                        continue
                    # Handle boolean conversion for superuser if needed
                    if key == "superuser":
                        value = 1 if value else 0

                    if config.DB_TYPE == "postgres":
                        setClauses.append(f"{key} = %s")
                    else:
                        setClauses.append(f"{key} = ?")
                    params.append(value)

                if not setClauses:
                    logger.warning("No valid fields provided for strategy update")
                    return False

                params.append(datetime.now())  # Add updatedat timestamp
                params.append(strategyId)  # Add strategyId for WHERE clause

                if config.DB_TYPE == "postgres":
                    setClauseStr = ", ".join(setClauses)
                    query = text(
                        f"""
                        UPDATE strategyconfig 
                        SET {setClauseStr}, updatedat = %s 
                        WHERE strategyid = %s
                    """
                    )
                else:
                    setClauseStr = ", ".join(setClauses)
                    query = f"""
                        UPDATE strategyconfig 
                        SET {setClauseStr}, updatedat = ? 
                        WHERE strategyid = ?
                    """

                cursor.execute(query, tuple(params))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update strategy {strategyId}: {str(e)}")
            return False

    def updateExecutionStatus(self, executionId: int, status: ExecutionStatus) -> bool:
        """Update the status of an execution"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                params = (status.value, datetime.now(), executionId)
                if config.DB_TYPE == "postgres":
                    query = text(
                        """
                        UPDATE strategyexecution SET 
                        status = %s, 
                        updatedat = %s 
                        WHERE executionid = %s
                    """
                    )
                    cursor.execute(query, params)
                else:
                    query = """
                        UPDATE strategyexecution SET 
                        status = ?, 
                        updatedat = ? 
                        WHERE executionid = ?
                    """
                    cursor.execute(query, params)
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update execution status: {str(e)}")
            return False

    def updateExecution(
        self,
        executionId: int,
        investedAmount: Decimal = None,
        remainingCoins: Decimal = None,
        avgEntryPrice: Decimal = None,
        status: ExecutionStatus = None,
        amountTakenOut: Decimal = None,
    ) -> bool:
        """
        Update multiple fields of an execution record.
        Only updates fields that are provided (not None).

        Args:
            executionId: ID of the execution to update
            investedAmount: New total invested amount
            remainingCoins: New remaining coin quantity
            avgEntryPrice: New average entry price
            status: New execution status
            amountTakenOut: New amount taken out

        Returns:
            bool: Success status
        """
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                setClauses = []
                params = []

                if investedAmount is not None:
                    if config.DB_TYPE == "postgres":
                        setClauses.append("investedamount = %s")
                    else:
                        setClauses.append("investedamount = ?")
                    params.append(str(investedAmount))
                if remainingCoins is not None:
                    if config.DB_TYPE == "postgres":
                        setClauses.append("remainingcoins = %s")
                    else:
                        setClauses.append("remainingcoins = ?")
                    params.append(str(remainingCoins))
                if avgEntryPrice is not None:
                    if config.DB_TYPE == "postgres":
                        setClauses.append("avgentryprice = %s")
                    else:
                        setClauses.append("avgentryprice = ?")
                    params.append(str(avgEntryPrice))
                if status is not None:
                    if config.DB_TYPE == "postgres":
                        setClauses.append("status = %s")
                    else:
                        setClauses.append("status = ?")
                    params.append(status.value)
                if amountTakenOut is not None:
                    if config.DB_TYPE == "postgres":
                        setClauses.append("amounttakenout = %s")
                    else:
                        setClauses.append("amounttakenout = ?")
                    params.append(str(amountTakenOut))

                if not setClauses:
                    logger.warning("No fields provided to update execution")
                    return False

                setClauses.append(
                    "updatedat = %s"
                    if config.DB_TYPE == "postgres"
                    else "updatedat = ?"
                )
                params.append(datetime.now())
                params.append(executionId)

                setClauseStr = ", ".join(setClauses)
                whereClause = (
                    "executionid = %s"
                    if config.DB_TYPE == "postgres"
                    else "executionid = ?"
                )

                query = (
                    f"UPDATE strategyexecution SET {setClauseStr} WHERE {whereClause}"
                )

                if config.DB_TYPE == "postgres":
                    cursor.execute(text(query), tuple(params))
                else:
                    cursor.execute(query, tuple(params))

                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update execution {executionId}: {str(e)}")
            return False

    def getActiveExecutionsWithConfig(
        self,
    ) -> List[Tuple[ExecutionState, BaseStrategyConfig]]:
        """Get all active executions along with their strategy configurations"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                if config.DB_TYPE == "postgres":
                    query = text(
                        """
                        SELECT 
                            se.*, sc.*
                        FROM strategyexecution se
                        JOIN strategyconfig sc ON se.strategyid = sc.strategyid
                        WHERE se.status IN (%s, %s)
                    """
                    )
                    params = (
                        ExecutionStatus.ACTIVE.value,
                        ExecutionStatus.INVESTED.value,
                    )
                    cursor.execute(query, params)
                else:
                    query = """
                        SELECT 
                            se.*, sc.*
                        FROM strategyexecution se
                        JOIN strategyconfig sc ON se.strategyid = sc.strategyid
                        WHERE se.status IN (?, ?)
                    """
                    params = (
                        ExecutionStatus.ACTIVE.value,
                        ExecutionStatus.INVESTED.value,
                    )
                    cursor.execute(query, params)

                columns = [col[0] for col in cursor.description]
                results = []

                for row in cursor.fetchall():
                    row_dict = dict(zip(columns, row))

                    # Split row into execution and config parts
                    execution_data = {}
                    config_data = {}

                    for key, value in row_dict.items():
                        # Determine if key belongs to execution or config based on prefixes or known fields
                        # This is a simplification; a better approach might use column aliases or table prefixes
                        if key in [
                            "executionid",
                            "tokenid",
                            "tokenname",
                            "avgentryprice",
                            "remainingcoins",
                            "allotedamount",
                            "investedamount",
                            "amounttakenout",
                            "realizedpnl",
                            "realizedpnlpercent",
                            "notes",
                        ] or key.startswith("execution_"):
                            execution_data[key] = value
                        else:
                            config_data[key] = value

                    # Add missing necessary fields if needed (adjust based on actual schema)
                    if (
                        "strategyid" not in execution_data
                        and "strategyid" in config_data
                    ):
                        execution_data["strategyid"] = config_data["strategyid"]
                    if "status" not in execution_data and "status" in config_data:
                        # This assumes status in config is strategy status, execution needs its own
                        # Find the execution status column (e.g., se.status)
                        # Find the correct key for execution status in row_dict
                        # This part needs refinement based on exact column names returned
                        pass  # Placeholder: Need to map execution status correctly

                    # Create ExecutionState object
                    # Convert relevant fields to Decimal/Enum
                    execution_data["status"] = ExecutionStatus(execution_data["status"])
                    execution_data["allotedamount"] = Decimal(
                        str(execution_data["allotedamount"])
                    )
                    # Add other Decimal conversions as needed...

                    execution_state = ExecutionState(**execution_data)

                    # Create BaseStrategyConfig object
                    # Convert JSON strings back to objects
                    config_data["strategyentryconditions"] = json.loads(
                        config_data["strategyentryconditions"]
                    )
                    if config_data.get("chartconditions"):
                        config_data["chartconditions"] = json.loads(
                            config_data["chartconditions"]
                        )
                    config_data["investmentinstructions"] = json.loads(
                        config_data["investmentinstructions"]
                    )
                    config_data["profittakinginstructions"] = json.loads(
                        config_data["profittakinginstructions"]
                    )
                    config_data["riskmanagementinstructions"] = json.loads(
                        config_data["riskmanagementinstructions"]
                    )
                    if config_data.get("moonbaginstructions"):
                        config_data["moonbaginstructions"] = json.loads(
                            config_data["moonbaginstructions"]
                        )
                    if config_data.get("additionalinstructions"):
                        config_data["additionalinstructions"] = json.loads(
                            config_data["additionalinstructions"]
                        )

                    config_data["status"] = config_data["status"]
                    config_data["active"] = config_data["active"]
                    config_data["superuser"] = config_data["superuser"]

                    strategy_config = BaseStrategyConfig(**config_data)

                    results.append((execution_state, strategy_config))

                return results
        except Exception as e:
            logger.error(f"Failed to get active executions with config: {str(e)}")
            return []

    def getActiveStrategiesForSource(self, source: str) -> List[Dict]:
        """Get all active strategies for a given source (Simplified)"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                params = (source,)
                if config.DB_TYPE == "postgres":
                    query = text(
                        """
                        SELECT * FROM strategyconfig 
                        WHERE source = %s AND active = 1
                    """
                    )
                    cursor.execute(query, params)
                else:
                    query = """
                        SELECT * FROM strategyconfig 
                        WHERE source = ? AND active = 1
                    """
                    cursor.execute(query, params)

                columns = [col[0] for col in cursor.description]
                strategies = []
                for row in cursor.fetchall():
                    strategy_dict = dict(zip(columns, row))
                    # Convert bools stored as ints
                    strategy_dict["active"] = bool(strategy_dict["active"])
                    strategy_dict["superuser"] = bool(strategy_dict["superuser"])
                    strategies.append(strategy_dict)
                return strategies
        except Exception as e:
            logger.error(
                f"Failed to get active strategies for source {source}: {str(e)}"
            )
            return []

    def getStrategyById(self, strategyId: int) -> Optional[Dict]:
        """Get a strategy configuration by its ID"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                params = (strategyId,)
                if config.DB_TYPE == "postgres":
                    query = text("SELECT * FROM strategyconfig WHERE strategyid = %s")
                    cursor.execute(query, params)
                else:
                    query = "SELECT * FROM strategyconfig WHERE strategyid = ?"
                    cursor.execute(query, params)

                row = cursor.fetchone()
                if row:
                    columns = [col[0] for col in cursor.description]
                    strategy_dict = dict(zip(columns, row))
                    strategy_dict["active"] = bool(strategy_dict["active"])
                    strategy_dict["superuser"] = bool(strategy_dict["superuser"])
                    return strategy_dict
                return None
        except Exception as e:
            logger.error(f"Failed to get strategy by ID {strategyId}: {str(e)}")
            return None

    def getExecutionById(self, executionId: int) -> Optional[Dict]:
        """Get an execution record by its ID"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                params = (executionId,)
                if config.DB_TYPE == "postgres":
                    query = text(
                        "SELECT * FROM strategyexecution WHERE executionid = %s"
                    )
                    cursor.execute(query, params)
                else:
                    query = "SELECT * FROM strategyexecution WHERE executionid = ?"
                    cursor.execute(query, params)

                row = cursor.fetchone()
                if row:
                    columns = [col[0] for col in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            logger.error(f"Failed to get execution by ID {executionId}: {str(e)}")
            return None

    def getExecutionsForTokenAndStrategy(
        self, tokenId: str, strategyId: int
    ) -> List[Dict]:
        """Get executions for a specific token and strategy"""
        try:
            config = get_config()
            with self.conn_manager.transaction() as cursor:
                params = (tokenId, strategyId)
                if config.DB_TYPE == "postgres":
                    query = text(
                        """
                        SELECT * FROM strategyexecution 
                        WHERE tokenid = %s AND strategyid = %s
                        ORDER BY createdat DESC
                    """
                    )
                    cursor.execute(query, params)
                else:
                    query = """
                        SELECT * FROM strategyexecution 
                        WHERE tokenid = ? AND strategyid = ?
                        ORDER BY createdat DESC
                    """
                    cursor.execute(query, params)

                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(
                f"Failed to get executions for token {tokenId} and strategy {strategyId}: {str(e)}"
            )
            return []
