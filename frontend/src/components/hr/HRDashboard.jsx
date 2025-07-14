import React, { useState, useEffect } from 'react';
import { libraryAPI } from '../../lib/api';

const HRDashboard = () => {
  const [hrData, setHrData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [modalContent, setModalContent] = useState(null);
  const [modalTitle, setModalTitle] = useState('');
  
  const fetchHRData = async () => {
    try {
      setLoading(true);
      
      // Fetch all HR data in parallel
      const [statusData, alertsData, agentsData] = await Promise.all([
        libraryAPI.getHRStatus(),
        libraryAPI.getHRAlerts(),
        libraryAPI.getHRAgents()
      ]);
      
      setHrData(statusData);
      setAlerts(alertsData.alerts || []);
      setAgents(agentsData.agents || []);
    } catch (error) {
      console.error('HR API error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHRData();
  }, []);

  const handleRefreshData = async () => {
    console.log('Refreshing HR data...');
    await fetchHRData();
    alert('✅ HR data refreshed successfully!\n\nUpdated information from Linda\'s system.');
  };

  const handleShowReports = async () => {
    try {
      setModalTitle('📊 HR Performance Reports');
      const data = await libraryAPI.getQAReports();
      setModalContent(data);
      setShowModal(true);
    } catch (error) {
      alert('Error loading reports: ' + error.message);
    }
  };

  const handleShowTraining = async () => {
    try {
      setModalTitle('🔄 Cross-Training System');
      const data = await libraryAPI.getQATraining();
      setModalContent(data);
      setShowModal(true);
    } catch (error) {
      alert('Error loading training data: ' + error.message);
    }
  };

  const handleShowMentorship = async () => {
    try {
      setModalTitle('👥 Mentorship Program');
      const data = await libraryAPI.getQAMentorship();
      setModalContent(data);
      setShowModal(true);
    } catch (error) {
      alert('Error loading mentorship data: ' + error.message);
    }
  };
  
  if (loading) {
    return (
      <div className="hr-dashboard">
        <h2>👔 Linda's HR Management</h2>
        <p>Loading HR data...</p>
      </div>
    );
  }

  return (
    <div className="hr-dashboard">
      <h2>👔 Linda's HR Management</h2>
      
      {hrData && (
        <div className="hr-status">
          <h3>System Status</h3>
          <p>Manager: {hrData.manager}</p>
          <p>Status: <span className={`status ${hrData.status}`}>{hrData.status}</span></p>
          <p>Last Update: {new Date(hrData.timestamp).toLocaleString()}</p>
          <p>Active Systems: {hrData.systems?.join(', ')}</p>
        </div>
      )}

      {agents.length > 0 && (
        <div className="hr-agents">
          <h3>👥 Agent Performance</h3>
          <div className="agents-grid">
            {agents.map(agent => (
              <div key={agent.agent_id} className="agent-card">
                <h4>{agent.agent_name}</h4>
                <p>Success Rate: <strong>{agent.success_rate}%</strong></p>
                <p>Tasks Completed: {agent.tasks_completed}</p>
                <p>Status: <span className={`status ${agent.status}`}>{agent.status}</span></p>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {alerts.length > 0 && (
        <div className="hr-alerts">
          <h3>🚨 Active Alerts</h3>
          {alerts.map(alert => (
            <div key={alert.alert_id} className="alert-item">
              <span className="alert-type">{alert.alert_type}</span>
              <span className="alert-agent">Agent: {alert.agent_id}</span>
              <span className="alert-date">{new Date(alert.created_at).toLocaleString()}</span>
            </div>
          ))}
        </div>
      )}
      
      <div className="hr-actions">
        <button onClick={handleShowReports}>
          📊 View Reports
        </button>
        <button onClick={handleShowTraining}>
          🔄 Cross-Training
        </button>
        <button onClick={handleShowMentorship}>
          👥 Mentorship
        </button>
        <button onClick={handleRefreshData} 
                style={{backgroundColor: '#10b981'}}
                disabled={loading}>
          {loading ? '🔄 Loading...' : '🔄 Refresh Data'}
        </button>
      </div>

      {/* Modal for displaying detailed data */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{modalTitle}</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <pre>{JSON.stringify(modalContent, null, 2)}</pre>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .hr-dashboard {
          padding: 20px;
          max-width: 1200px;
          margin: 0 auto;
        }
        
        .hr-status, .hr-agents, .hr-alerts {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 16px;
          margin: 16px 0;
        }
        
        .agents-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 16px;
          margin-top: 12px;
        }
        
        .agent-card {
          background: white;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          padding: 12px;
        }
        
        .agent-card h4 {
          margin: 0 0 8px 0;
          color: #1f2937;
        }
        
        .alert-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px;
          background: white;
          border-left: 4px solid #f59e0b;
          margin: 8px 0;
          border-radius: 4px;
        }
        
        .status {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 0.875rem;
          font-weight: 500;
        }
        
        .status.operational, .status.active {
          background: #dcfce7;
          color: #166534;
        }
        
        .hr-actions {
          display: flex;
          gap: 12px;
          margin-top: 20px;
        }
        
        .hr-actions button {
          padding: 10px 16px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 14px;
        }
        
        .hr-actions button:hover:not(:disabled) {
          background: #2563eb;
          transform: translateY(-1px);
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .hr-actions button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .hr-actions button:active:not(:disabled) {
          transform: translateY(0);
        }
        
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }
        
        .modal-content {
          background: white;
          border-radius: 8px;
          width: 90%;
          max-width: 800px;
          max-height: 80vh;
          overflow: hidden;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        
        .modal-header {
          background: #f8fafc;
          padding: 16px 20px;
          border-bottom: 1px solid #e2e8f0;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .modal-header h3 {
          margin: 0;
          color: #1f2937;
        }
        
        .modal-close {
          background: none;
          border: none;
          font-size: 24px;
          cursor: pointer;
          color: #6b7280;
          padding: 0;
          width: 30px;
          height: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .modal-close:hover {
          color: #374151;
        }
        
        .modal-body {
          padding: 20px;
          overflow-y: auto;
          max-height: calc(80vh - 80px);
        }
        
        .modal-body pre {
          background: #f8fafc;
          padding: 16px;
          border-radius: 6px;
          overflow: auto;
          font-size: 12px;
          line-height: 1.4;
          color: #374151;
        }
      `}</style>
    </div>
  );
};

export default HRDashboard;
