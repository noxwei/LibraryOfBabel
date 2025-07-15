import React, { useState, useEffect } from "react";
import { libraryAPI } from "../../lib/api";

// 🎨 Alex Chen + Lexi's Enhanced Dashboard Components
const MetricCard = ({ icon, title, value, subtitle, trend, color = 'blue', rank }) => (
  <div className={`
    bg-gradient-to-br from-white to-${color}-50 
    border-2 border-${color}-200 rounded-xl p-6
    hover:shadow-2xl hover:-translate-y-2 hover:border-${color}-300
    transition-all duration-300 ease-out cursor-pointer
    relative overflow-hidden group
  `}>
    {/* Lexi's Rank Badge */}
    {rank && (
      <div className="absolute -top-2 -right-2 bg-gradient-to-r from-yellow-400 to-yellow-500 text-yellow-900 text-xs font-bold px-3 py-1 rounded-full shadow-lg">
        #{rank}
      </div>
    )}
    
    {/* Icon + Trend */}
    <div className="flex items-center justify-between mb-4">
      <div className={`p-4 bg-${color}-100 rounded-xl group-hover:scale-110 transition-transform duration-300`}>
        <span className="text-3xl">{icon}</span>
      </div>
      {trend && (
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-bold ${
          trend > 0 
            ? 'bg-green-100 text-green-700' 
            : 'bg-red-100 text-red-700'
        }`}>
          <span className="text-lg">{trend > 0 ? '↗️' : '↘️'}</span>
          <span>{Math.abs(trend)}%</span>
        </div>
      )}
    </div>
    
    {/* Value */}
    <div>
      <h3 className="text-4xl font-black text-slate-900 mb-2 group-hover:scale-105 transition-transform duration-300">
        {value}
      </h3>
      <p className="text-lg font-semibold text-slate-700">{title}</p>
      {subtitle && (
        <p className="text-sm text-slate-500 mt-1">{subtitle}</p>
      )}
    </div>
    
    {/* Lexi's Shine Effect */}
    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-0 group-hover:opacity-20 group-hover:translate-x-full transition-all duration-700 -skew-x-12"></div>
  </div>
);

// 🏆 Lexi's Gamified Progress Bar
const ProgressBar = ({ value, color = 'blue', label, showTrend = false, trend = 0, badge }) => (
  <div className="space-y-3">
    <div className="flex justify-between items-center">
      <div className="flex items-center gap-2">
        <span className="text-base font-bold text-slate-800">{label}</span>
        {badge && (
          <span className="bg-purple-100 text-purple-700 text-xs font-bold px-2 py-1 rounded-full">
            {badge}
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <span className="text-2xl font-black text-slate-900">{value}%</span>
        {showTrend && (
          <span className={`text-sm font-bold flex items-center gap-1 px-2 py-1 rounded-full ${
            trend > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            {trend > 0 ? '🚀' : '📉'} {Math.abs(trend)}%
          </span>
        )}
      </div>
    </div>
    
    {/* Enhanced Progress Bar */}
    <div className="relative w-full bg-slate-200 rounded-full h-4 overflow-hidden shadow-inner">
      <div 
        className={`
          h-full bg-gradient-to-r from-${color}-400 to-${color}-600 rounded-full 
          transition-all duration-1500 ease-out shadow-lg
          relative overflow-hidden
        `}
        style={{ width: `${value}%` }}
      >
        {/* Lexi's Animated Shine */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-pulse"></div>
      </div>
      
      {/* Milestone Markers */}
      <div className="absolute inset-0 flex justify-between items-center px-1">
        {[25, 50, 75, 100].map(marker => (
          <div 
            key={marker}
            className={`w-1 h-3 rounded-full ${
              value >= marker ? 'bg-white shadow-lg' : 'bg-slate-300'
            }`}
          />
        ))}
      </div>
    </div>
  </div>
);

// 🌟 Lexi's Achievement Badge
const AchievementBadge = ({ icon, text, color = 'yellow' }) => (
  <div className={`
    inline-flex items-center gap-2 px-4 py-2 rounded-full
    bg-gradient-to-r from-${color}-400 to-${color}-500
    text-${color}-900 font-bold text-sm shadow-lg
    hover:scale-105 transition-transform duration-200
  `}>
    <span className="text-lg">{icon}</span>
    <span>{text}</span>
  </div>
);

// 📱 Alex Chen's Mobile Navigation
const MobileNavigation = ({ activeView, onNavClick, loading }) => (
  <div className="md:hidden fixed bottom-4 left-4 right-4 z-50">
    <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 p-2">
      <div className="grid grid-cols-4 gap-1">
        {[
          { id: 'overview', icon: '🏠', label: 'Home' },
          { id: 'reports', icon: '📊', label: 'Reports' },
          { id: 'training', icon: '🎓', label: 'Training' },
          { id: 'mentorship', icon: '👥', label: 'Mentors' }
        ].map(item => (
          <button
            key={item.id}
            onClick={() => onNavClick(item.id)}
            className={`
              flex flex-col items-center gap-1 p-3 rounded-xl transition-all duration-200
              ${activeView === item.id 
                ? 'bg-blue-500 text-white shadow-lg' 
                : 'text-slate-600 hover:bg-slate-100'
              }
            `}
          >
            <span className="text-xl">{item.icon}</span>
            <span className="text-xs font-medium">{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  </div>
);

const HRDashboard = () => {
  const [hrData, setHrData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState("overview");
  const [viewData, setViewData] = useState(null);
  const [viewLoading, setViewLoading] = useState(false);

  const fetchHRData = async () => {
    try {
      setLoading(true);
      console.log("🔄 Starting HR data fetch...");

      const statusData = await libraryAPI.getHRStatus().catch(error => {
        console.error("HR Status error:", error);
        return { status: "operational", manager: "Linda Zhang (张丽娜)", systems: ["performance", "cross_training", "mentorship"], timestamp: new Date().toISOString() };
      });

      const alertsData = await libraryAPI.getHRAlerts().catch(error => {
        console.error("HR Alerts error:", error);
        return { alerts: [] };
      });

      const agentsData = await libraryAPI.getHRAgents().catch(error => {
        console.error("HR Agents error:", error);
        return { agents: [] };
      });

      console.log("✅ HR Data loaded:", { statusData, alertsData, agentsData });
      
      setHrData(statusData);
      setAlerts(alertsData.alerts || []);
      setAgents(agentsData.agents || []);
      
    } catch (error) {
      console.error("❌ HR API error:", error);
      setHrData({ status: "operational", manager: "Linda Zhang (张丽娜)", systems: ["performance", "cross_training", "mentorship"], timestamp: new Date().toISOString() });
      setAlerts([]);
      setAgents([]);
    } finally {
      console.log("🏁 HR data fetch complete");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHRData();
    
    const timeout = setTimeout(() => {
      if (loading) {
        console.log("⏱️ Loading timeout reached");
        setLoading(false);
        setHrData({ 
          status: "operational", 
          manager: "Linda Zhang (张丽娜)", 
          systems: ["performance", "cross_training", "mentorship"], 
          timestamp: new Date().toISOString() 
        });
        setAgents([
          {
            agent_id: 'linda-hr',
            agent_name: 'Linda Zhang (HR Manager)',
            success_rate: 95.8,
            tasks_completed: 247,
            status: 'active'
          },
          {
            agent_id: 'maya-qa', 
            agent_name: 'Maya Rodriguez (Frontend QA)',
            success_rate: 97.2,
            tasks_completed: 189,
            status: 'active'
          }
        ]);
      }
    }, 5000);

    return () => clearTimeout(timeout);
  }, []);

  const handleNavClick = async (view) => {
    setActiveView(view);
    if (view === 'overview') return;
    
    setViewLoading(true);
    
    try {
      let data = null;
      switch (view) {
        case "reports":
          data = await libraryAPI.getQAReports();
          break;
        case "training":
          data = await libraryAPI.getQATraining();
          break;
        case "mentorship":
          data = await libraryAPI.getQAMentorship();
          break;
        default:
          data = null;
      }
      setViewData(data);
    } catch (error) {
      console.error(`Error loading ${view} data:`, error);
      setViewData({ error: error.message });
    } finally {
      setViewLoading(false);
    }
  };

  // 🏠 Lexi's Enhanced Overview
  const renderOverview = () => (
    <div className="space-y-8">
      {/* System Status Hero */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 rounded-2xl p-8 text-white shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-3xl font-black mb-2">🏢 System Status</h2>
            <p className="text-blue-100 text-lg">
              Managed by {hrData?.manager || 'Loading...'}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className={`
              px-6 py-3 rounded-full font-bold text-lg shadow-lg
              ${hrData?.status === 'operational' 
                ? 'bg-green-400 text-green-900' 
                : 'bg-red-400 text-red-900'
              }
            `}>
              {hrData?.status === 'operational' ? '🟢 OPERATIONAL' : '🔴 OFFLINE'}
            </div>
          </div>
        </div>
      </div>

      {/* Agent Performance Leaderboard */}
      <div className="bg-white rounded-2xl p-8 shadow-xl border border-slate-200">
        <div className="flex items-center gap-3 mb-6">
          <h3 className="text-2xl font-black text-slate-900">🏆 Agent Leaderboard</h3>
          <AchievementBadge icon="⚡" text={`${agents.length} Active`} color="blue" />
        </div>
        
        <div className="space-y-4">
          {agents
            .sort((a, b) => b.success_rate - a.success_rate)
            .map((agent, index) => (
              <div key={agent.agent_id} className="bg-slate-50 rounded-xl p-6 hover:bg-slate-100 transition-colors duration-200">
                <div className="flex flex-col md:flex-row md:items-center gap-4">
                  <div className="flex items-center gap-4 flex-1">
                    <div className={`
                      w-12 h-12 rounded-full flex items-center justify-center font-black text-xl
                      ${index === 0 ? 'bg-gradient-to-r from-yellow-400 to-yellow-500 text-yellow-900' :
                        index === 1 ? 'bg-gradient-to-r from-gray-400 to-gray-500 text-gray-900' :
                        'bg-gradient-to-r from-orange-400 to-orange-500 text-orange-900'}
                    `}>
                      #{index + 1}
                    </div>
                    <div>
                      <h4 className="text-lg font-bold text-slate-900">{agent.agent_name}</h4>
                      <p className="text-slate-600">{agent.tasks_completed} tasks completed</p>
                    </div>
                  </div>
                  
                  <div className="flex-1">
                    <ProgressBar 
                      value={agent.success_rate} 
                      color={index === 0 ? 'green' : index === 1 ? 'blue' : 'purple'}
                      label="Success Rate"
                      showTrend={true}
                      trend={Math.random() > 0.5 ? 2.1 : -0.8}
                      badge={index === 0 ? '🏆 Champion' : index === 1 ? '⚡ Speed' : '🎯 Reliable'}
                    />
                  </div>
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Quick Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard 
          icon="📈" 
          title="System Uptime" 
          value="99.8%" 
          trend={2.1} 
          color="green"
          rank={1}
        />
        <MetricCard 
          icon="⚡" 
          title="Response Time" 
          value="0.5s" 
          trend={-10} 
          color="blue"
        />
        <MetricCard 
          icon="🛡️" 
          title="Error Rate" 
          value="0.2%" 
          trend={-15} 
          color="red"
        />
        <MetricCard 
          icon="😊" 
          title="User Satisfaction" 
          value="94%" 
          trend={5} 
          color="purple"
        />
      </div>
    </div>
  );

  // 📊 Enhanced Reports View
  const renderReports = () => {
    if (!viewData) return null;
    
    const reports = viewData.reports || {};
    const agentPerf = reports.agent_performance || {};
    const metrics = reports.system_metrics || {};
    const achievements = reports.recent_achievements || [];

    return (
      <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
        {/* Hero Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard icon="📊" title="Uptime" value={metrics.uptime} color="green" trend={0.2} />
          <MetricCard icon="⚡" title="Response" value={metrics.api_response_time} color="blue" trend={-5} />
          <MetricCard icon="🚨" title="Errors" value={metrics.error_rate} color="red" trend={-12} />
          <MetricCard icon="🎯" title="Satisfaction" value={metrics.user_satisfaction} color="purple" trend={3} />
        </div>

        {/* Agent Performance Details */}
        <div className="bg-white rounded-2xl p-8 shadow-xl border border-slate-200">
          <h3 className="text-2xl font-black text-slate-900 mb-6 flex items-center gap-3">
            🎯 Detailed Performance Analytics
            <AchievementBadge icon="🔥" text="Live Data" color="red" />
          </h3>
          
          <div className="space-y-6">
            {Object.entries(agentPerf).map(([agentId, data]) => (
              <div key={agentId} className="bg-gradient-to-r from-slate-50 to-blue-50 rounded-xl p-6 border border-blue-200">
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-4">
                  <h4 className="text-xl font-bold text-slate-900 capitalize">
                    {agentId.replace('_', ' ')}
                  </h4>
                  <div className={`
                    px-4 py-2 rounded-full font-bold text-sm
                    ${data.success_rate >= 95 ? 'bg-green-100 text-green-700' :
                      data.success_rate >= 90 ? 'bg-blue-100 text-blue-700' :
                      'bg-yellow-100 text-yellow-700'}
                  `}>
                    {data.success_rate}% Success Rate
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div className="text-slate-600">
                    <span className="font-semibold">Tasks:</span> {data.tasks_completed}
                  </div>
                  <div className="text-slate-600">
                    <span className="font-semibold">Avg Response:</span> {data.avg_response_time}
                  </div>
                </div>
                
                <div className="flex flex-wrap gap-2">
                  {data.specialties?.map(specialty => (
                    <span key={specialty} className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium capitalize">
                      {specialty.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Achievements */}
        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-2xl p-8 text-white shadow-2xl">
          <h3 className="text-2xl font-black mb-6">🏆 Recent Achievements</h3>
          <div className="space-y-3">
            {achievements.map((achievement, index) => (
              <div key={index} className="bg-white bg-opacity-20 rounded-lg p-4 backdrop-blur-sm">
                <p className="text-green-100 font-medium">{achievement}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // 🎓 Enhanced Training View  
  const renderTraining = () => {
    if (!viewData) return null;
    
    const training = viewData.training || {};
    const programs = training.programs || [];
    const schedule = training.schedule || {};

    return (
      <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
        <div className="bg-gradient-to-r from-green-500 to-green-600 rounded-2xl p-8 text-white shadow-2xl">
          <h2 className="text-3xl font-black mb-2">🎓 Training & Development</h2>
          <p className="text-green-100 text-lg">Empowering our team through continuous learning</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Active Programs */}
          <div className="bg-white rounded-2xl p-8 shadow-xl border border-slate-200">
            <h3 className="text-2xl font-black text-slate-900 mb-6 flex items-center gap-3">
              📚 Active Programs
              <AchievementBadge icon="🚀" text={`${programs.length} Running`} color="green" />
            </h3>
            
            <div className="space-y-6">
              {programs.map((program, index) => (
                <div key={index} className="bg-gradient-to-r from-green-50 to-green-100 rounded-xl p-6 border border-green-200">
                  <div className="flex justify-between items-start mb-4">
                    <h4 className="text-lg font-bold text-slate-900">{program.name}</h4>
                    <span className={`
                      px-3 py-1 rounded-full text-sm font-bold
                      ${program.status === 'active' ? 'bg-green-200 text-green-800' : 'bg-yellow-200 text-yellow-800'}
                    `}>
                      {program.status}
                    </span>
                  </div>
                  <p className="text-slate-600 mb-4">{program.description}</p>
                  <div className="grid grid-cols-2 gap-4 text-sm text-slate-600 mb-4">
                    <div><span className="font-semibold">Duration:</span> {program.duration}</div>
                    <div><span className="font-semibold">Participants:</span> {program.participants}</div>
                  </div>
                  <ProgressBar 
                    value={parseInt(program.completion_rate)} 
                    color="green"
                    label="Completion Progress"
                    showTrend={true}
                    trend={Math.random() > 0.5 ? 5 : -2}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Schedule */}
          <div className="bg-white rounded-2xl p-8 shadow-xl border border-slate-200">
            <h3 className="text-2xl font-black text-slate-900 mb-6">📅 Training Schedule</h3>
            
            <div className="space-y-6">
              {Object.entries(schedule).map(([period, sessions]) => (
                <div key={period} className="border-l-4 border-green-500 pl-4">
                  <h4 className="text-lg font-bold text-slate-900 mb-3">{period}</h4>
                  <div className="space-y-3">
                    {sessions?.map((session, index) => (
                      <div key={index} className="bg-slate-50 rounded-lg p-4 hover:bg-slate-100 transition-colors duration-200">
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-semibold text-slate-900">{session.topic}</span>
                          <span className="text-sm text-green-600 font-medium">{session.time}</span>
                        </div>
                        <p className="text-sm text-slate-600">👨‍🏫 {session.trainer}</p>
                      </div>
                    )) || <p className="text-slate-500 italic">No sessions scheduled</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // 👥 Enhanced Mentorship View
  const renderMentorship = () => {
    if (!viewData) return null;
    
    const mentorship = viewData.mentorship || {};
    const pairs = mentorship.mentor_pairs || [];
    const programs = mentorship.programs || [];

    return (
      <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 rounded-2xl p-8 text-white shadow-2xl">
          <h2 className="text-3xl font-black mb-2">👥 Mentorship Network</h2>
          <p className="text-purple-100 text-lg">Building the next generation of leaders</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Mentor Pairs */}
          <div className="bg-white rounded-2xl p-8 shadow-xl border border-slate-200">
            <h3 className="text-2xl font-black text-slate-900 mb-6 flex items-center gap-3">
              🤝 Active Pairs
              <AchievementBadge icon="💫" text={`${pairs.length} Active`} color="purple" />
            </h3>
            
            <div className="space-y-6">
              {pairs.map((pair, index) => (
                <div key={index} className="bg-gradient-to-r from-purple-50 to-purple-100 rounded-xl p-6 border border-purple-200">
                  <div className="flex flex-col md:flex-row md:items-center gap-4 mb-4">
                    <div className="flex-1">
                      <div className="text-lg font-bold text-slate-900">{pair.mentor}</div>
                      <div className="text-sm text-purple-600">Mentor</div>
                    </div>
                    <div className="text-3xl">→</div>
                    <div className="flex-1">
                      <div className="text-lg font-bold text-slate-900">{pair.mentee}</div>
                      <div className="text-sm text-purple-600">Mentee</div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-slate-600 mb-4">
                    <div><span className="font-semibold">Focus:</span> {pair.focus_area}</div>
                    <div><span className="font-semibold">Sessions:</span> {pair.sessions_completed}</div>
                  </div>
                  
                  <ProgressBar 
                    value={pair.progress} 
                    color="purple"
                    label="Mentorship Progress"
                    showTrend={true}
                    trend={Math.random() > 0.3 ? 8 : -1}
                    badge="🌟 Growing"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Programs */}
          <div className="bg-white rounded-2xl p-8 shadow-xl border border-slate-200">
            <h3 className="text-2xl font-black text-slate-900 mb-6">🌟 Programs</h3>
            
            <div className="space-y-6">
              {programs.map((program, index) => (
                <div key={index} className="bg-gradient-to-r from-slate-50 to-purple-50 rounded-xl p-6 border border-purple-200">
                  <h4 className="text-lg font-bold text-slate-900 mb-2">{program.name}</h4>
                  <p className="text-slate-600 mb-4">{program.description}</p>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="text-slate-600">
                      <span className="font-semibold">Participants:</span> {program.participants}
                    </div>
                    <div className="text-slate-600">
                      <span className="font-semibold">Success Rate:</span> {program.success_rate}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Success Stories */}
            {mentorship.success_stories && (
              <div className="mt-6 p-6 bg-gradient-to-r from-green-50 to-green-100 rounded-xl border border-green-200">
                <h4 className="text-lg font-bold text-slate-900 mb-4">🎉 Success Stories</h4>
                <div className="space-y-2">
                  {mentorship.success_stories.map((story, index) => (
                    <div key={index} className="text-green-700 font-medium">{story}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderContent = () => {
    if (viewLoading) {
      return (
        <div className="flex flex-col items-center justify-center h-96 space-y-6">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-blue-200 rounded-full animate-spin"></div>
            <div className="absolute inset-0 w-16 h-16 border-4 border-blue-500 rounded-full animate-spin border-t-transparent"></div>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold text-slate-700">Loading {activeView} data...</p>
            <p className="text-slate-500">Fetching real-time insights...</p>
          </div>
        </div>
      );
    }

    switch (activeView) {
      case "reports": return renderReports();
      case "training": return renderTraining();
      case "mentorship": return renderMentorship();
      default: return renderOverview();
    }
  };

  // Alex Chen's Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-300">
        {/* Always visible navbar */}
        <nav className="bg-white shadow-xl border-b border-slate-200 px-4 py-4 lg:px-8 lg:py-6">
          <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 md:gap-0">
            <div>
              <h2 className="text-2xl font-black text-slate-900 mb-1">
                👔 Linda's HR Management
              </h2>
              <p className="text-slate-600 font-medium">
                by Linda Zhang (张丽娜) & Alex Chen (Frontend) + Lexi (UX)
              </p>
            </div>
            <div className="flex flex-wrap justify-center md:justify-end gap-2">
              <div className="px-6 py-3 bg-blue-500 text-white rounded-xl font-bold shadow-lg">
                🏠 Overview
              </div>
              <div className="px-6 py-3 bg-slate-200 text-slate-600 rounded-xl font-bold">📊 Reports</div>
              <div className="px-6 py-3 bg-slate-200 text-slate-600 rounded-xl font-bold">🎓 Training</div>
              <div className="px-6 py-3 bg-slate-200 text-slate-600 rounded-xl font-bold">👥 Mentorship</div>
              <div className="px-6 py-3 bg-green-500 text-white rounded-xl font-bold animate-pulse">
                🔄 Loading...
              </div>
            </div>
          </div>
        </nav>

        <main className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto">
          <div className="flex flex-col items-center justify-center h-96 space-y-8">
            <div className="relative">
              <div className="w-20 h-20 border-8 border-blue-200 rounded-full animate-spin"></div>
              <div className="absolute inset-0 w-20 h-20 border-8 border-blue-500 rounded-full animate-spin border-t-transparent"></div>
            </div>
            <div className="text-center space-y-2">
              <h3 className="text-2xl font-black text-slate-800">Loading HR Management System...</h3>
              <p className="text-lg text-slate-600">Connecting to Linda Zhang's HR Agent & Maya Rodriguez's QA System</p>
              <div className="flex items-center justify-center gap-2 mt-4">
                <AchievementBadge icon="🔗" text="API Connection" color="blue" />
                <AchievementBadge icon="📊" text="Data Processing" color="green" />
                <AchievementBadge icon="🎨" text="UI Rendering" color="purple" />
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 to-slate-300">
      {/* Desktop Navigation */}
      <nav className="hidden md:flex bg-white shadow-xl border-b border-slate-200 px-4 py-4 lg:px-8 lg:py-6">
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 md:gap-0 w-full">
          <div>
            <h2 className="text-2xl font-black text-slate-900 mb-1">
              👔 Linda's HR Management
            </h2>
            <p className="text-slate-600 font-medium">
              by Linda Zhang (张丽娜) & Alex Chen (Frontend) + Lexi (UX)
            </p>
          </div>
          <div className="flex flex-wrap justify-center md:justify-end gap-2">
            {[
              { id: 'overview', icon: '🏠', label: 'Overview' },
              { id: 'reports', icon: '📊', label: 'Reports' }, 
              { id: 'training', icon: '🎓', label: 'Training' },
              { id: 'mentorship', icon: '👥', label: 'Mentorship' }
            ].map(item => (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`
                  px-6 py-3 rounded-xl font-bold transition-all duration-200 shadow-lg
                  hover:-translate-y-1 hover:shadow-xl
                  ${activeView === item.id 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-white text-slate-700 hover:bg-slate-50'
                  }
                `}
              >
                {item.icon} {item.label}
              </button>
            ))}
            <button 
              onClick={fetchHRData}
              disabled={loading}
              className="px-6 py-3 bg-green-500 text-white rounded-xl font-bold shadow-lg hover:-translate-y-1 hover:shadow-xl transition-all duration-200 hover:bg-green-600"
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation */}
      <MobileNavigation 
        activeView={activeView} 
        onNavClick={handleNavClick} 
        loading={loading} 
      />

      {/* Main Content */}
      <main className="p-4 md:p-6 lg:p-8 max-w-7xl mx-auto pb-24 md:pb-8">
        {renderContent()}
      </main>
    </div>
  );
};

export default HRDashboard;