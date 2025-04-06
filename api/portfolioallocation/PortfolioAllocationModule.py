from config.Config import get_config
from math import pow
from typing import Dict, List, Any, Tuple, Optional
from logs.logger import get_logger

logger = get_logger(__name__)

def calculateRequiredCagr(currentPortfolio: float, targetPortfolio: float, timeHorizon: int) -> float:
    """
    Calculate the required Compound Annual Growth Rate (CAGR) to reach target portfolio value.
    
    Args:
        currentPortfolio: Current portfolio value in USD
        targetPortfolio: Target portfolio value in USD
        timeHorizon: Time horizon in years
        
    Returns:
        Required CAGR as a decimal (e.g., 0.25 for 25%)
    """
    if currentPortfolio <= 0 or targetPortfolio <= 0 or timeHorizon <= 0:
        raise ValueError("Portfolio values must be positive and time horizon must be greater than zero")
        
    return pow(targetPortfolio / currentPortfolio, 1 / timeHorizon) - 1

def determineStrategy(requiredCagr: float) -> str:
    """
    Determine the investment strategy based on required CAGR.
    
    Args:
        requiredCagr: Required CAGR as a decimal
        
    Returns:
        Strategy as a string: "conservative", "moderate", or "aggressive"
    """
    if requiredCagr <= 0.15:
        return "conservative"
    elif requiredCagr <= 0.30:
        return "moderate"
    else:
        return "aggressive"

def getBaseAllocations(strategy: str) -> Dict[str, float]:
    """
    Get base allocations based on strategy.
    
    Args:
        strategy: Investment strategy ("conservative", "moderate", or "aggressive")
        
    Returns:
        Dictionary with base allocations for each conviction level
    """
    if strategy == "conservative":
        return {"high": 30, "medium": 20, "low": 0, "stablecoins": 50}
    elif strategy == "moderate":
        return {"high": 50, "medium": 30, "low": 10, "stablecoins": 10}
    elif strategy == "aggressive":
        return {"high": 70, "medium": 20, "low": 10, "stablecoins": 0}
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

def adjustAllocationsByFocus(baseAllocations: Dict[str, float], investmentFocus: str) -> Dict[str, float]:
    """
    Adjust base allocations based on investment focus.
    
    Args:
        baseAllocations: Base allocations by conviction level
        investmentFocus: Investment focus ("High Conviction Only", "Medium Conviction Only", 
                         "Low Conviction Only", or "Mixed")
        
    Returns:
        Adjusted allocations
    """
    adjustedAllocations = baseAllocations.copy()
    
    if investmentFocus == "High Conviction Only":
        # Move all allocations to high conviction
        nonHighAllocation = sum(v for k, v in baseAllocations.items() if k != "high")
        adjustedAllocations["high"] = baseAllocations.get("high", 0) + nonHighAllocation
        adjustedAllocations["medium"] = 0
        adjustedAllocations["low"] = 0
        adjustedAllocations["stablecoins"] = 0
    elif investmentFocus == "Medium Conviction Only":
        # Move all allocations to medium conviction
        nonMediumAllocation = sum(v for k, v in baseAllocations.items() if k != "medium")
        adjustedAllocations["high"] = 0
        adjustedAllocations["medium"] = baseAllocations.get("medium", 0) + nonMediumAllocation
        adjustedAllocations["low"] = 0
        adjustedAllocations["stablecoins"] = 0
    elif investmentFocus == "Low Conviction Only":
        # Move all allocations to low conviction
        nonLowAllocation = sum(v for k, v in baseAllocations.items() if k != "low" and k != "stablecoins")
        adjustedAllocations["high"] = 0
        adjustedAllocations["medium"] = 0
        adjustedAllocations["low"] = baseAllocations.get("low", 0) + nonLowAllocation
        adjustedAllocations["stablecoins"] = baseAllocations.get("stablecoins", 0)
    # For "Mixed", keep the original allocations
    
    return adjustedAllocations

def calculatePositionSizes(adjustedAllocations: Dict[str, float], currentPortfolio: float, 
                          tokens: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Calculate position sizes for each token based on allocations.
    
    Args:
        adjustedAllocations: Adjusted allocations by conviction level
        currentPortfolio: Current portfolio value in USD
        tokens: List of token dictionaries with name and conviction level
        
    Returns:
        List of dictionaries with token name and position size
    """
    # Count tokens by conviction level
    tokenCounts = {"high": 0, "medium": 0, "low": 0}
    for token in tokens:
        conviction = token["conviction"].lower()
        if conviction in tokenCounts:
            tokenCounts[conviction] += 1
    
    # Initialize position sizes
    positionSizes = []
    
    # Calculate position size for each token
    for token in tokens:
        conviction = token["conviction"].lower()
        count = tokenCounts.get(conviction, 0)
        
        if count > 0 and conviction in adjustedAllocations:
            # Calculate the allocation amount for this conviction level
            allocationAmount = (adjustedAllocations[conviction] / 100) * currentPortfolio
            
            # Divide equally among tokens of this conviction level
            positionSize = allocationAmount / count
            
            positionSizes.append({
                "name": token["name"],
                "conviction": conviction,
                "positionSize": positionSize
            })
        else:
            positionSizes.append({
                "name": token["name"],
                "conviction": conviction,
                "positionSize": 0
            })
    
    return positionSizes

def calculateRiskLevels(strategy: str, maxLoss: float, currentPortfolio: float, 
                       positionSizes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate dynamic stop-loss and take-profit levels for each token.
    
    Args:
        strategy: Investment strategy ("conservative", "moderate", or "aggressive")
        maxLoss: Maximum acceptable loss in USD
        currentPortfolio: Current portfolio value in USD
        positionSizes: List of dictionaries with token name, conviction, and position size
        
    Returns:
        List of dictionaries with token name, stop-loss, and take-profit levels
    """
    # Calculate base risk factor
    baseRiskFactor = maxLoss / currentPortfolio
    
    # Set volatility factor based on strategy
    volatilityFactor = 0.5  # conservative
    if strategy == "moderate":
        volatilityFactor = 1.0
    elif strategy == "aggressive":
        volatilityFactor = 1.5
    
    # Set conviction multipliers
    convictionMultipliers = {
        "high": 1.2,
        "medium": 1.0,
        "low": 0.8
    }
    
    stopLossTakeProfit = []
    
    for position in positionSizes:
        name = position["name"]
        conviction = position["conviction"]
        
        # Get conviction multiplier (default to 1.0 if not found)
        convictionMultiplier = convictionMultipliers.get(conviction, 1.0)
        
        # Calculate stop-loss percentage
        stopLoss = baseRiskFactor * volatilityFactor * convictionMultiplier
        
        # Cap stop-loss at 50%
        stopLoss = min(stopLoss, 0.5)
        
        # Calculate take-profit as a function of stop-loss and volatility
        takeProfit = stopLoss * (2 + volatilityFactor)
        
        # Cap take-profit at 100%
        takeProfit = min(takeProfit, 1.0)
        
        stopLossTakeProfit.append({
            "name": name,
            "stopLoss": round(stopLoss, 2),
            "takeProfit": round(takeProfit, 2)
        })
    
    return stopLossTakeProfit

def performRiskCheck(positionSizes: List[Dict[str, Any]], stopLossTakeProfit: List[Dict[str, Any]], 
                    maxLoss: float) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Perform risk check and adjust position sizes if necessary.
    
    Args:
        positionSizes: List of dictionaries with token name and position size
        stopLossTakeProfit: List of dictionaries with token name, stop-loss, and take-profit levels
        maxLoss: Maximum acceptable loss in USD
        
    Returns:
        Tuple of adjusted position sizes and boolean indicating if adjustment was needed
    """
    # Create a dictionary for quick lookup of stop-loss values
    stopLossDict = {item["name"]: item["stopLoss"] for item in stopLossTakeProfit}
    
    # Calculate total potential loss
    totalPotentialLoss = sum(position["positionSize"] * stopLossDict.get(position["name"], 0) 
                           for position in positionSizes)
    
    # Check if total potential loss exceeds maximum acceptable loss
    if totalPotentialLoss > maxLoss:
        # Calculate scaling factor
        scalingFactor = maxLoss / totalPotentialLoss
        
        # Adjust position sizes
        adjustedPositions = []
        for position in positionSizes:
            adjustedPosition = position.copy()
            adjustedPosition["positionSize"] = position["positionSize"] * scalingFactor
            adjustedPositions.append(adjustedPosition)
        
        return adjustedPositions, True
    
    return positionSizes, False

def generateSummary(positionSizes: List[Dict[str, Any]], 
                   stopLossTakeProfit: List[Dict[str, Any]]) -> str:
    """
    Generate a summary of the portfolio allocation.
    
    Args:
        positionSizes: List of dictionaries with token name and position size
        stopLossTakeProfit: List of dictionaries with token name, stop-loss, and take-profit levels
        
    Returns:
        Summary string
    """
    summaryLines = []
    
    # Create a dictionary for quick lookup of stop-loss and take-profit values
    riskDict = {item["name"]: (item["stopLoss"], item["takeProfit"]) for item in stopLossTakeProfit}
    
    for position in positionSizes:
        name = position["name"]
        positionSize = position["positionSize"]
        
        if positionSize > 0:
            stopLoss, takeProfit = riskDict.get(name, (0, 0))
            
            # Format as percentages
            stopLossPercent = int(stopLoss * 100)
            takeProfitPercent = int(takeProfit * 100)
            
            summaryLines.append(
                f"Invest ${positionSize:.2f} in {name} with {stopLossPercent}% stop-loss and "
                f"{takeProfitPercent}% take-profit"
            )
    
    return "\n".join(summaryLines)

def portfolioAllocation(data):
    """
    Calculate portfolio allocation suggestions based on input data
    
    Args:
        data (dict): Input data containing portfolio parameters
        
    Returns:
        dict: Portfolio allocation suggestions
    """
    # Extract input parameters
    current_portfolio = float(data['currentPortfolio'])
    target_portfolio = float(data['targetPortfolio'])
    time_horizon = float(data['timeHorizon'])
    max_loss = float(data['maxLoss'])
    tokens = data['tokens']
    stage = int(data.get('stage', 1))
    
    # Log input parameters
    logger.info(f"Portfolio allocation calculation with: current={current_portfolio}, target={target_portfolio}, time={time_horizon}")
    
    # Validate portfolio values
    if current_portfolio <= 0 or target_portfolio <= 0 or max_loss <= 0:
        raise ValueError("Portfolio values must be positive")
    
    # Validate time horizon - allow small positive values (0.001 and above)
    if time_horizon < 0.001:
        raise ValueError("Time horizon must be at least 0.001 years")
    
    # Calculate required CAGR
    required_cagr = (target_portfolio / current_portfolio) ** (1 / time_horizon) - 1
    
    # Determine strategy based on CAGR
    if required_cagr < 0.2:  # Less than 20% annual return
        strategy = "conservative"
    elif required_cagr < 0.5:  # Between 20% and 50% annual return
        strategy = "moderate"
    else:  # Greater than 50% annual return
        strategy = "aggressive"
    
    # Count tokens by conviction
    conviction_counts = {'high': 0, 'medium': 0, 'low': 0}
    for token in tokens:
        conviction = token.get('conviction', 'medium')
        if conviction in conviction_counts:
            conviction_counts[conviction] += 1
    
    # Calculate allocations based on conviction levels
    total_tokens = sum(conviction_counts.values())
    if total_tokens == 0:
        raise ValueError("At least one token must be specified")
    
    allocations = {}
    
    # Allocation percentages by strategy and conviction
    if strategy == "conservative":
        # Conservative allocates more to high conviction, less to low
        allocations['high'] = 60 if conviction_counts['high'] > 0 else 0
        allocations['medium'] = 30 if conviction_counts['medium'] > 0 else 0
        allocations['low'] = 10 if conviction_counts['low'] > 0 else 0
        allocations['stablecoins'] = 0  # No stablecoins in conservative strategy
    elif strategy == "moderate":
        # Moderate has a balanced approach
        allocations['high'] = 50 if conviction_counts['high'] > 0 else 0
        allocations['medium'] = 30 if conviction_counts['medium'] > 0 else 0
        allocations['low'] = 10 if conviction_counts['low'] > 0 else 0
        allocations['stablecoins'] = 10  # Some stablecoins in moderate strategy
    else:  # aggressive
        # Aggressive allocates more broadly
        allocations['high'] = 40 if conviction_counts['high'] > 0 else 0
        allocations['medium'] = 30 if conviction_counts['medium'] > 0 else 0
        allocations['low'] = 20 if conviction_counts['low'] > 0 else 0
        allocations['stablecoins'] = 10  # Some stablecoins in aggressive strategy
    
    # Normalize allocations if some conviction levels have no tokens
    total_allocation = sum(allocations.values())
    if total_allocation == 0:
        raise ValueError("No valid conviction levels selected")
    
    if total_allocation < 100:
        # Redistribute missing allocation to high, then medium, then low
        missing = 100 - total_allocation
        if conviction_counts['high'] > 0:
            allocations['high'] += missing
        elif conviction_counts['medium'] > 0:
            allocations['medium'] += missing
        elif conviction_counts['low'] > 0:
            allocations['low'] += missing
        else:
            allocations['stablecoins'] += missing
    
    # Calculate position sizes for each token
    position_sizes = []
    for token in tokens:
        conviction = token.get('conviction', 'medium')
        if conviction not in allocations or allocations[conviction] == 0:
            continue
        
        # Calculate allocation for this token
        token_allocation = allocations[conviction] / conviction_counts[conviction]
        position_size = current_portfolio * (token_allocation / 100)
        
        position_sizes.append({
            'name': token['name'],
            'positionSize': position_size,
            'allocation': token_allocation
        })
    
    # Set stop-loss and take-profit levels based on conviction
    stop_loss_take_profit = []
    for token in tokens:
        conviction = token.get('conviction', 'medium')
        
        # Higher conviction = higher take profit, lower stop loss
        if conviction == 'high':
            stop_loss = 0.2  # 20% stop loss
            take_profit = 0.5  # 50% take profit
        elif conviction == 'medium':
            stop_loss = 0.15  # 15% stop loss
            take_profit = 0.3  # 30% take profit
        else:  # low
            stop_loss = 0.1  # 10% stop loss
            take_profit = 0.2  # 20% take profit
        
        stop_loss_take_profit.append({
            'name': token['name'],
            'stopLoss': stop_loss,
            'takeProfit': take_profit
        })
    
    # Add summary text
    summary = f"Based on your target to grow your portfolio from ${current_portfolio:.2f} to ${target_portfolio:.2f} over {time_horizon:.2f} years with a maximum loss of ${max_loss:.2f}, a {strategy} strategy is recommended with a required CAGR of {required_cagr:.2%}."
    
    return {
        'requiredCagr': required_cagr,
        'recommendedStrategy': strategy,
        'allocations': allocations,
        'positionSizes': position_sizes,
        'stopLossTakeProfit': stop_loss_take_profit,
        'summary': summary
    } 