const getStrategyPerformanceConfigs = async (params) => {
  return axios.get('http://localhost:8080/api/reports/strategy-configs', { params });
};

const getStrategyPerformanceExecutions = async (params) => {
  return axios.get('http://localhost:8080/api/reports/strategy-executions', { params });
};

const getStrategySpecificExecutions = async (strategyId, params) => {
  return axios.get(`http://localhost:8080/api/reports/strategy-config/${strategyId}/executions`, { params });
}; 