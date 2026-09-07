import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, ScatterChart, Scatter, ComposedChart
} from 'recharts';
import {
  AlertTriangle, TrendingUp, Zap, Eye, CheckCircle, Activity, Filter, Download,
  Clock, Users, Database, Wifi, MoreVertical, ArrowUpRight, ArrowDownRight, Lightbulb, Bookmark, ShieldAlert, Plus,
  RefreshCw, Trash2, ShieldCheck, ShieldOff, UserCheck, UserX, Star, UserPlus, X
} from 'lucide-react';
import {
  getEvents, getAnalytics, getInsights, getHighConfidenceInsights, getAnomalies, getAnomalySummary,
  acknowledgeAnomaly, runAnomalyDetection, getUsers, getAuditLogs, setUserAdmin, activateUser, deactivateUser, deleteUser, createUser,
  getSavedViews, createSavedView, deleteSavedView, deleteEvent,
} from '../utils/api';

const TYPE_COLORS = ['#3b82f6', '#06b6d4', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#ef4444', '#6366f1'];

export default function Dashboard({ activeTab, setActiveTab, user }) {
  const [events, setEvents] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [insights, setInsights] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [anomalySummary, setAnomalySummary] = useState(null);
  const [savedViews, setSavedViews] = useState([]);
  const [adminUsers, setAdminUsers] = useState(null);
  const [auditLogs, setAuditLogs] = useState(null);
  const [adminError, setAdminError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [highConfidenceOnly, setHighConfidenceOnly] = useState(false);
  const [userActionId, setUserActionId] = useState(null);
  const [analyticsSearch, setAnalyticsSearch] = useState('');
  const [analyticsSeverity, setAnalyticsSeverity] = useState('ALL');
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [createUserForm, setCreateUserForm] = useState({ username: '', email: '', password: '', is_admin: false });
  const [createUserError, setCreateUserError] = useState('');
  const [creatingUser, setCreatingUser] = useState(false);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeTab === 'saved-views') {
      getSavedViews().then(setSavedViews).catch(() => setSavedViews([]));
    }
    if (activeTab === 'admin' && user?.is_admin) {
      getUsers().then(setAdminUsers).catch(() => setAdminError(true));
      getAuditLogs(10).then(setAuditLogs).catch(() => setAuditLogs([]));
    }
  }, [activeTab, user]);

  const loadDashboardData = async () => {
    try {
      const [eventsData, analyticsData, insightsData] = await Promise.all([
        getEvents(),
        getAnalytics(),
        getInsights(),
      ]);

      setEvents(Array.isArray(eventsData) ? eventsData : []);
      setAnalytics(analyticsData);
      setInsights(Array.isArray(insightsData) ? insightsData : []);

      try {
        const [anomaliesData, summaryData] = await Promise.all([getAnomalies(), getAnomalySummary()]);
        setAnomalies(Array.isArray(anomaliesData) ? anomaliesData : []);
        setAnomalySummary(summaryData);
      } catch (e) {
        setAnomalies([]);
        setAnomalySummary(null);
      }

      setLoading(false);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setLoading(false);
    }
  };

  const handleAcknowledge = async (anomalyId) => {
    try {
      await acknowledgeAnomaly(anomalyId);
      setAnomalies((prev) => prev.filter((a) => a.id !== anomalyId));
    } catch (err) {
      console.error('Failed to acknowledge anomaly:', err);
    }
  };

  const handleSaveView = async () => {
    const name = window.prompt('Name this view:', `${activeTab} view`);
    if (!name) return;
    try {
      const view = await createSavedView({ name, description: `Snapshot of ${activeTab} tab`, filters: { tab: activeTab } });
      setSavedViews((prev) => [...prev, view]);
    } catch (err) {
      console.error('Failed to save view:', err);
    }
  };

  const handleDeleteSavedView = async (viewId) => {
    try {
      await deleteSavedView(viewId);
      setSavedViews((prev) => prev.filter((v) => v.id !== viewId));
    } catch (err) {
      console.error('Failed to delete saved view:', err);
    }
  };

  const handleRunDetection = async () => {
    setDetecting(true);
    try {
      await runAnomalyDetection();
      const [anomaliesData, summaryData] = await Promise.all([getAnomalies(), getAnomalySummary()]);
      setAnomalies(Array.isArray(anomaliesData) ? anomaliesData : []);
      setAnomalySummary(summaryData);
    } catch (err) {
      console.error('Failed to run anomaly detection:', err);
    } finally {
      setDetecting(false);
    }
  };

  const handleToggleHighConfidence = async () => {
    const next = !highConfidenceOnly;
    setHighConfidenceOnly(next);
    try {
      const insightsData = next ? await getHighConfidenceInsights() : await getInsights();
      setInsights(Array.isArray(insightsData) ? insightsData : []);
    } catch (err) {
      console.error('Failed to load insights:', err);
    }
  };

  const handleUserAction = async (userId, action) => {
    setUserActionId(userId);
    try {
      if (action === 'promote') await setUserAdmin(userId, true);
      if (action === 'demote') await setUserAdmin(userId, false);
      if (action === 'activate') await activateUser(userId);
      if (action === 'deactivate') await deactivateUser(userId);
      const updatedUsers = await getUsers();
      setAdminUsers(updatedUsers);
    } catch (err) {
      console.error('Failed to update user:', err);
    } finally {
      setUserActionId(null);
    }
  };

  const handleDeleteUser = async (userId, username) => {
    if (!window.confirm(`Permanently delete user "${username}"? This cannot be undone.`)) return;
    setUserActionId(userId);
    try {
      await deleteUser(userId);
      setAdminUsers((prev) => prev.filter((u) => u.id !== userId));
    } catch (err) {
      console.error('Failed to delete user:', err);
      window.alert(err.message || 'Failed to delete user');
    } finally {
      setUserActionId(null);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setCreateUserError('');
    setCreatingUser(true);
    try {
      const newUser = await createUser(createUserForm);
      setAdminUsers((prev) => [...(prev || []), newUser]);
      setShowCreateUser(false);
      setCreateUserForm({ username: '', email: '', password: '', is_admin: false });
    } catch (err) {
      setCreateUserError(err.message || 'Failed to create user');
    } finally {
      setCreatingUser(false);
    }
  };

  const handleDeleteEvent = async (eventId) => {
    try {
      await deleteEvent(eventId);
      setEvents((prev) => prev.filter((e) => e.id !== eventId));
    } catch (err) {
      console.error('Failed to delete event:', err);
    }
  };

  // Generate severity data from real events
  const generateSeverityData = () => {
    const severityCounts = { CRITICAL: 0, ERROR: 0, WARNING: 0, INFO: 0 };
    events.forEach(event => {
      if (severityCounts.hasOwnProperty(event.severity)) {
        severityCounts[event.severity]++;
      }
    });

    return [
      { name: 'Critical', value: severityCounts.CRITICAL, fill: '#ef4444' },
      { name: 'Error', value: severityCounts.ERROR, fill: '#f97316' },
      { name: 'Warning', value: severityCounts.WARNING, fill: '#eab308' },
      { name: 'Info', value: severityCounts.INFO, fill: '#22c55e' },
    ].filter(item => item.value > 0);
  };

  // Generate event type data with bar chart format
  const generateEventTypeData = () => {
    const typeCounts = {};
    events.forEach(event => {
      typeCounts[event.event_type] = (typeCounts[event.event_type] || 0) + 1;
    });

    return Object.entries(typeCounts).map(([type, count], idx) => ({
      name: type.replace(/_/g, ' '),
      value: count,
      fill: TYPE_COLORS[idx % TYPE_COLORS.length]
    }));
  };

  // Generate source distribution
  const generateSourceData = () => {
    const sourceCounts = {};
    events.forEach(event => {
      sourceCounts[event.source] = (sourceCounts[event.source] || 0) + 1;
    });

    return Object.entries(sourceCounts).map(([source, count]) => ({
      name: source,
      count: count
    }));
  };

  // Generate timeline data
  const generateTimelineData = () => {
    const hourCounts = {};
    events.forEach(event => {
      const hour = new Date(event.timestamp).getHours();
      const key = `${hour}:00`;
      hourCounts[key] = (hourCounts[key] || 0) + 1;
    });

    return Array.from({ length: 24 }, (_, i) => {
      const hour = i.toString().padStart(2, '0');
      return {
        time: `${hour}:00`,
        count: hourCounts[`${i}:00`] || 0
      };
    });
  };

  const totalEvents = events.length;
  const errorCount = events.filter(e => ['ERROR', 'CRITICAL'].includes(e.severity)).length;
  const systemHealth = 100 - Math.min((errorCount / Math.max(totalEvents, 1)) * 100, 100);
  const severityData = generateSeverityData();
  const eventTypeData = generateEventTypeData();
  const sourceData = generateSourceData();
  const timelineData = generateTimelineData();

  // Real average duration from event metadata, when present
  const durations = events.map(e => e.event_metadata?.duration_ms).filter(d => typeof d === 'number');
  const avgDuration = durations.length > 0
    ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length)
    : null;

  const busiestHour = timelineData.reduce(
    (max, cur) => (cur.count > max.count ? cur : max),
    { time: 'N/A', count: 0 }
  );

  const analyticsFilteredEvents = events.filter((e) => {
    const matchesSeverity = analyticsSeverity === 'ALL' || e.severity === analyticsSeverity;
    const query = analyticsSearch.trim().toLowerCase();
    const matchesSearch = !query ||
      e.message?.toLowerCase().includes(query) ||
      e.source?.toLowerCase().includes(query) ||
      e.event_type?.toLowerCase().includes(query);
    return matchesSeverity && matchesSearch;
  });

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return 'text-red-400 bg-red-900';
      case 'ERROR':
        return 'text-orange-400 bg-orange-900';
      case 'WARNING':
        return 'text-yellow-400 bg-yellow-900';
      default:
        return 'text-green-400 bg-green-900';
    }
  };

  const getSeverityBg = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-900/20 border-red-700';
      case 'ERROR':
        return 'bg-orange-900/20 border-orange-700';
      case 'WARNING':
        return 'bg-yellow-900/20 border-yellow-700';
      default:
        return 'bg-green-900/20 border-green-700';
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center h-full">
        <div className="text-center">
          <div className="inline-block animate-spin">
            <Activity className="w-8 h-8 text-blue-400" />
          </div>
          <p className="text-gray-400 mt-3">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl">
      {/* ===== OVERVIEW TAB ===== */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              icon={<Zap className="w-6 h-6 text-blue-400" />}
              title="Total Events"
              value={totalEvents.toString()}
              change={`${totalEvents} recorded`}
              changePositive={totalEvents > 0}
              trend="+24%"
            />
            <MetricCard
              icon={<AlertTriangle className="w-6 h-6 text-orange-400" />}
              title="Errors"
              value={errorCount.toString()}
              change={errorCount === 0 ? 'No errors' : `${Math.round((errorCount / totalEvents) * 100)}% of events`}
              changePositive={errorCount === 0}
              trend={errorCount > 0 ? '-12%' : '0%'}
            />
            <MetricCard
              icon={<TrendingUp className="w-6 h-6 text-cyan-400" />}
              title="Insights"
              value={insights.length.toString()}
              change="AI analyzed"
              changePositive={true}
              trend={insights.length > 0 ? '+5' : 'pending'}
            />
            <MetricCard
              icon={<Eye className="w-6 h-6 text-green-400" />}
              title="System Health"
              value={`${Math.round(systemHealth)}%`}
              change={systemHealth > 95 ? 'Excellent' : systemHealth > 80 ? 'Good' : 'Needs attention'}
              changePositive={systemHealth > 80}
              trend={systemHealth > 90 ? '↑' : systemHealth > 70 ? '→' : '↓'}
            />
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Event Timeline Chart */}
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 shadow-xl hover:shadow-2xl transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-400" />
                  Events Timeline (24h)
                </h2>
                <button className="p-2 hover:bg-gray-700 rounded-lg transition">
                  <MoreVertical className="w-4 h-4 text-gray-400" />
                </button>
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={timelineData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Area type="monotone" dataKey="count" stroke="#3b82f6" fillOpacity={1} fill="url(#colorCount)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Severity Distribution */}
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 shadow-xl hover:shadow-2xl transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  Severity Breakdown
                </h2>
              </div>
              {severityData.length > 0 ? (
                <div className="flex gap-6">
                  <div className="w-40 h-56">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={severityData}
                          cx="50%"
                          cy="50%"
                          innerRadius={40}
                          outerRadius={70}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {severityData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                          labelStyle={{ color: '#fff' }}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex-1 space-y-3">
                    {severityData.map((item) => (
                      <div key={item.name} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded" style={{ backgroundColor: item.fill }}></div>
                          <span className="text-gray-400">{item.name}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-white font-semibold">{item.value}</span>
                          <span className="text-gray-500 text-xs">
                            {Math.round((item.value / totalEvents) * 100)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center text-gray-400 py-20">No severity data</div>
              )}
            </div>
          </div>

          {/* Event Types Bar Chart */}
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 shadow-xl hover:shadow-2xl transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Database className="w-5 h-5 text-cyan-400" />
                Event Types Distribution
              </h2>
              <button className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-lg text-gray-300 text-sm">
                Export
              </button>
            </div>
            {eventTypeData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={eventTypeData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="name" stroke="#9CA3AF" angle={-45} textAnchor="end" height={100} />
                  <YAxis stroke="#9CA3AF" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Bar dataKey="value" fill="#06b6d4" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-gray-400 py-20">No event type data</div>
            )}
          </div>
        </div>
      )}

      {/* ===== ANALYTICS TAB ===== */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">Advanced Analytics</h1>
            <div className="flex gap-2">
              <button className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-gray-300 flex items-center gap-2">
                <Filter className="w-4 h-4" /> Filter
              </button>
              <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white flex items-center gap-2">
                <Download className="w-4 h-4" /> Export
              </button>
            </div>
          </div>

          {/* KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatBox
              label="Avg Event Duration"
              value={avgDuration !== null ? `${avgDuration}ms` : 'N/A'}
              subtitle={avgDuration !== null ? `Across ${durations.length} events` : 'No duration metadata'}
              icon={<Clock className="w-5 h-5 text-blue-400" />}
              trend={avgDuration !== null ? 'measured' : '—'}
              trendPositive={true}
            />
            <StatBox
              label="Error Rate"
              value={totalEvents > 0 ? `${Math.round((errorCount / totalEvents) * 100)}%` : '0%'}
              subtitle={`${errorCount} of ${totalEvents} events`}
              icon={<AlertTriangle className="w-5 h-5 text-orange-400" />}
              trend={errorCount > 5 ? 'elevated' : 'nominal'}
              trendPositive={errorCount <= 5}
            />
            <StatBox
              label="Busiest Hour"
              value={busiestHour.time}
              subtitle={`${busiestHour.count} events`}
              icon={<TrendingUp className="w-5 h-5 text-green-400" />}
              trend="peak"
              trendPositive={true}
            />
          </div>

          {/* All Events */}
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 shadow-xl">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Database className="w-5 h-5 text-cyan-400" />
                All Events ({analyticsFilteredEvents.length})
              </h2>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={analyticsSearch}
                  onChange={(e) => setAnalyticsSearch(e.target.value)}
                  placeholder="Search message, source, type..."
                  className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 text-sm focus:outline-none focus:border-blue-500 w-56"
                />
                <select
                  value={analyticsSeverity}
                  onChange={(e) => setAnalyticsSeverity(e.target.value)}
                  className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="ALL">All Severities</option>
                  <option value="CRITICAL">Critical</option>
                  <option value="ERROR">Error</option>
                  <option value="WARNING">Warning</option>
                  <option value="INFO">Info</option>
                </select>
              </div>
            </div>
            {analyticsFilteredEvents.length === 0 ? (
              <div className="text-center text-gray-400 py-8">No events match this filter</div>
            ) : (
              <div className="overflow-x-auto max-h-96 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-gray-900">
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-2 px-3 text-gray-400">Time</th>
                      <th className="text-left py-2 px-3 text-gray-400">Severity</th>
                      <th className="text-left py-2 px-3 text-gray-400">Source</th>
                      <th className="text-left py-2 px-3 text-gray-400">Type</th>
                      <th className="text-left py-2 px-3 text-gray-400">Message</th>
                      <th className="text-left py-2 px-3 text-gray-400">Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analyticsFilteredEvents.map((event) => (
                      <tr key={event.id} className="border-b border-gray-700/60 hover:bg-gray-700/30 transition">
                        <td className="py-2 px-3 text-gray-400 whitespace-nowrap">{new Date(event.timestamp).toLocaleString()}</td>
                        <td className="py-2 px-3">
                          <span className={`px-2 py-0.5 text-xs font-semibold rounded ${getSeverityColor(event.severity)}`}>
                            {event.severity}
                          </span>
                        </td>
                        <td className="py-2 px-3 text-gray-300 whitespace-nowrap">{event.source}</td>
                        <td className="py-2 px-3 text-gray-300 whitespace-nowrap capitalize">{event.event_type?.replace(/_/g, ' ')}</td>
                        <td className="py-2 px-3 text-gray-300 max-w-xs truncate" title={event.message}>{event.message}</td>
                        <td className="py-2 px-3 text-gray-400 whitespace-nowrap">
                          {typeof event.event_metadata?.duration_ms === 'number' ? `${event.event_metadata.duration_ms}ms` : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Detailed Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Source Distribution */}
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 shadow-xl">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Wifi className="w-5 h-5 text-purple-400" />
                Events by Source
              </h2>
              {sourceData.length > 0 ? (
                <div className="space-y-3">
                  {sourceData.map((item, idx) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-2 flex-1">
                        <div className="w-2 h-2 rounded-full bg-gradient-to-r from-purple-400 to-pink-400"></div>
                        <span className="text-gray-400 capitalize">{item.name}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-32 bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all"
                            style={{ width: `${(item.count / totalEvents) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-white font-semibold w-8 text-right">{item.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-gray-400 py-8">No source data</div>
              )}
            </div>

            {/* Severity Breakdown (real data) */}
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 shadow-xl">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5 text-yellow-400" />
                Severity Ratio
              </h2>
              <div className="space-y-4">
                {severityData.length > 0 ? severityData.map((item) => (
                  <PerformanceMetric
                    key={item.name}
                    label={item.name}
                    value={`${item.value} (${Math.round((item.value / totalEvents) * 100)}%)`}
                    percentage={Math.round((item.value / totalEvents) * 100)}
                    barColor={item.fill}
                  />
                )) : (
                  <div className="text-center text-gray-400 py-8">No severity data</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ===== ANOMALIES TAB ===== */}
      {activeTab === 'anomalies' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">Anomaly Detection</h1>
            <button
              onClick={handleRunDetection}
              disabled={detecting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-white flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${detecting ? 'animate-spin' : ''}`} />
              {detecting ? 'Scanning...' : 'Run Detection'}
            </button>
          </div>

          {/* Anomaly Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AnomalySummaryCard
              title="Active Anomalies"
              value={(anomalySummary?.total_anomalies ?? anomalies.length).toString()}
              subtitle="Currently tracked"
              icon={<AlertTriangle className="w-5 h-5 text-red-400" />}
              color="red"
            />
            <AnomalySummaryCard
              title="Unacknowledged"
              value={(anomalySummary?.unacknowledged ?? anomalies.length).toString()}
              subtitle="Needs review"
              icon={<Clock className="w-5 h-5 text-yellow-400" />}
              color="yellow"
            />
          </div>

          {/* Anomaly Detection Chart */}
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-white mb-4">Anomaly Trend</h2>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                  labelStyle={{ color: '#fff' }}
                />
                <Bar dataKey="count" fill="#ef4444" opacity={0.3} />
                <Line type="monotone" dataKey="count" stroke="#ef4444" strokeWidth={2} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Anomaly List */}
          {anomalies.length === 0 ? (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-12 text-center">
              <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-white mb-2">No Anomalies Detected</h3>
              <p className="text-gray-400">System is operating normally. Keep monitoring for any changes.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {anomalies.slice(0, 5).map((anomaly) => (
                <div key={anomaly.id} className="bg-red-900/20 border border-red-700 rounded-lg p-4 hover:bg-red-900/30 transition">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="px-2 py-1 bg-red-600 text-red-100 text-xs rounded font-semibold">
                          {anomaly.anomaly_type?.toUpperCase() || 'ANOMALY'}
                        </span>
                        <span className="text-gray-400">{anomaly.source} - {anomaly.event_type}</span>
                      </div>
                      <p className="text-white font-semibold">Deviation: {(anomaly.deviation_percent || 0).toFixed(1)}%</p>
                    </div>
                    <button
                      onClick={() => handleAcknowledge(anomaly.id)}
                      title="Acknowledge"
                      className="p-2 hover:bg-red-600/20 rounded transition"
                    >
                      <CheckCircle className="w-5 h-5 text-gray-400 hover:text-green-400" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ===== INSIGHTS TAB ===== */}
      {activeTab === 'insights' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">AI-Generated Insights</h1>
            <button
              onClick={handleToggleHighConfidence}
              className={`px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition ${
                highConfidenceOnly ? 'bg-yellow-600 text-white' : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
              }`}
            >
              <Star className="w-4 h-4" /> High Confidence Only
            </button>
          </div>

          {insights.length === 0 ? (
            <div className="bg-gradient-to-br from-blue-900/40 via-gray-800 to-gray-900 rounded-xl border border-blue-700/50 p-12 text-center">
              <Lightbulb className="w-12 h-12 text-blue-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-white mb-2">No Insights Yet</h3>
              <p className="text-gray-400 mb-6 max-w-md mx-auto">
                Set your OPENAI_API_KEY environment variable to enable AI-powered insights. The system will automatically analyze events and generate actionable recommendations.
              </p>
              <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 text-left text-sm text-gray-300 font-mono inline-block">
                export OPENAI_API_KEY="sk-..."
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {insights.map((insight) => (
                <div key={insight.id} className="bg-gradient-to-r from-blue-900/40 to-cyan-900/40 border border-blue-700/50 rounded-lg p-6 hover:border-blue-600 transition">
                  <div className="flex items-start justify-between mb-3">
                    <span className="px-3 py-1 bg-blue-600/50 text-blue-200 text-xs rounded-full font-semibold">
                      {insight.insight_type || 'INSIGHT'}
                    </span>
                    <span className="text-yellow-400 font-semibold text-sm">
                      {Math.round((insight.confidence_score || 0) * 100)}% confident
                    </span>
                  </div>
                  <p className="text-gray-200 mb-3">{insight.analysis}</p>
                  {insight.recommendations && insight.recommendations.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold text-gray-300 mb-2">Recommendations:</p>
                      <ul className="space-y-1">
                        {insight.recommendations.map((rec, idx) => (
                          <li key={idx} className="text-sm text-gray-300 flex items-start gap-2">
                            <span className="w-1.5 h-1.5 bg-cyan-400 rounded-full mt-1.5 flex-shrink-0"></span>
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ===== ADMIN TAB ===== */}
      {activeTab === 'admin' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">System Administration</h1>
            <span className="px-3 py-1 bg-gray-700 rounded-full text-xs text-gray-300">
              Logged in as {user?.username} ({user?.is_admin ? 'Administrator' : 'Standard User'})
            </span>
          </div>

          {/* System Stats (real, always available) */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <AdminStatCard label="Total Events" value={totalEvents} icon={<Database className="w-5 h-5 text-cyan-400" />} />
            <AdminStatCard label="Total Insights" value={insights.length} icon={<Lightbulb className="w-5 h-5 text-blue-400" />} />
            <AdminStatCard label="Active Anomalies" value={anomalySummary?.total_anomalies ?? anomalies.length} icon={<AlertTriangle className="w-5 h-5 text-red-400" />} />
            <AdminStatCard label="Unique Sources" value={sourceData.length} icon={<Wifi className="w-5 h-5 text-purple-400" />} />
          </div>

          {user?.is_admin ? (
            <>
              {/* User Management */}
              <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 shadow-xl">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                    <Users className="w-5 h-5 text-blue-400" />
                    Users
                  </h2>
                  <button
                    onClick={() => setShowCreateUser(true)}
                    className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-white text-sm flex items-center gap-2"
                  >
                    <UserPlus className="w-4 h-4" /> Create User
                  </button>
                </div>
                {adminUsers === null ? (
                  <div className="text-center text-gray-400 py-6">Loading users...</div>
                ) : adminUsers.length === 0 ? (
                  <div className="text-center text-gray-400 py-6">No users found</div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-700">
                          <th className="text-left py-2 px-4 text-gray-400">Username</th>
                          <th className="text-left py-2 px-4 text-gray-400">Email</th>
                          <th className="text-left py-2 px-4 text-gray-400">Role</th>
                          <th className="text-left py-2 px-4 text-gray-400">Status</th>
                          <th className="text-left py-2 px-4 text-gray-400">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminUsers.map((u) => (
                          <tr key={u.id} className="border-b border-gray-700 hover:bg-gray-700/50 transition">
                            <td className="py-3 px-4 text-white font-semibold">{u.username}</td>
                            <td className="py-3 px-4 text-gray-400">{u.email}</td>
                            <td className="py-3 px-4 text-gray-400">{u.is_admin ? 'Admin' : 'User'}</td>
                            <td className="py-3 px-4">
                              <span className={`px-2 py-1 rounded text-xs font-semibold ${u.is_active ? 'bg-green-900/50 text-green-400' : 'bg-gray-700 text-gray-400'}`}>
                                {u.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="py-3 px-4">
                              <div className="flex items-center gap-2">
                                <button
                                  disabled={userActionId === u.id || u.username === user?.username}
                                  onClick={() => handleUserAction(u.id, u.is_admin ? 'demote' : 'promote')}
                                  title={u.is_admin ? 'Revoke admin' : 'Make admin'}
                                  className="p-1.5 hover:bg-gray-600 rounded transition disabled:opacity-30"
                                >
                                  {u.is_admin ? <ShieldOff className="w-4 h-4 text-yellow-400" /> : <ShieldCheck className="w-4 h-4 text-gray-400" />}
                                </button>
                                <button
                                  disabled={userActionId === u.id || u.username === user?.username}
                                  onClick={() => handleUserAction(u.id, u.is_active ? 'deactivate' : 'activate')}
                                  title={u.is_active ? 'Deactivate user' : 'Activate user'}
                                  className="p-1.5 hover:bg-gray-600 rounded transition disabled:opacity-30"
                                >
                                  {u.is_active ? <UserX className="w-4 h-4 text-red-400" /> : <UserCheck className="w-4 h-4 text-green-400" />}
                                </button>
                                <button
                                  disabled={userActionId === u.id || u.username === user?.username}
                                  onClick={() => handleDeleteUser(u.id, u.username)}
                                  title="Delete user"
                                  className="p-1.5 hover:bg-red-600/20 rounded transition disabled:opacity-30"
                                >
                                  <Trash2 className="w-4 h-4 text-gray-400 hover:text-red-400" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Audit Logs */}
              <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 shadow-xl">
                <h2 className="text-lg font-semibold text-white mb-4">Recent Audit Logs</h2>
                {auditLogs === null ? (
                  <div className="text-center text-gray-400 py-6">Loading audit logs...</div>
                ) : auditLogs.length === 0 ? (
                  <div className="text-center text-gray-400 py-6">No audit log entries yet</div>
                ) : (
                  <div className="space-y-2 text-sm">
                    {auditLogs.map((log) => (
                      <div key={log.id} className="flex justify-between text-gray-400 border-b border-gray-700 pb-2">
                        <span>{log.username} &middot; {log.action}</span>
                        <span className="text-gray-500">{new Date(log.created_at).toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-12 text-center">
              <ShieldAlert className="w-12 h-12 text-yellow-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-white mb-2">Admin Access Required</h3>
              <p className="text-gray-400">User management and audit logs are only visible to administrator accounts.</p>
            </div>
          )}

          {showCreateUser && (
            <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 w-full max-w-md shadow-2xl">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-white">Create User</h3>
                  <button onClick={() => setShowCreateUser(false)} className="p-1 hover:bg-gray-700 rounded transition">
                    <X className="w-5 h-5 text-gray-400" />
                  </button>
                </div>
                <form onSubmit={handleCreateUser} className="space-y-3">
                  {createUserError && (
                    <div className="px-3 py-2 bg-red-900/40 border border-red-700 rounded-lg text-red-300 text-sm">
                      {createUserError}
                    </div>
                  )}
                  <input
                    type="text"
                    placeholder="Username"
                    required
                    minLength={3}
                    value={createUserForm.username}
                    onChange={(e) => setCreateUserForm((f) => ({ ...f, username: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 text-sm focus:outline-none focus:border-blue-500"
                  />
                  <input
                    type="email"
                    placeholder="Email"
                    required
                    value={createUserForm.email}
                    onChange={(e) => setCreateUserForm((f) => ({ ...f, email: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 text-sm focus:outline-none focus:border-blue-500"
                  />
                  <input
                    type="password"
                    placeholder="Password (min. 8 characters)"
                    required
                    minLength={8}
                    value={createUserForm.password}
                    onChange={(e) => setCreateUserForm((f) => ({ ...f, password: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 text-sm focus:outline-none focus:border-blue-500"
                  />
                  <label className="flex items-center gap-2 text-sm text-gray-300">
                    <input
                      type="checkbox"
                      checked={createUserForm.is_admin}
                      onChange={(e) => setCreateUserForm((f) => ({ ...f, is_admin: e.target.checked }))}
                      className="rounded border-gray-600"
                    />
                    Grant admin privileges
                  </label>
                  <div className="flex gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowCreateUser(false)}
                      className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-gray-300 text-sm"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={creatingUser}
                      className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg text-white text-sm"
                    >
                      {creatingUser ? 'Creating...' : 'Create User'}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===== SAVED VIEWS TAB ===== */}
      {activeTab === 'saved-views' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-white">Saved Views</h1>
            <button
              onClick={handleSaveView}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white flex items-center gap-2"
            >
              <Plus className="w-4 h-4" /> Save Current View
            </button>
          </div>

          {savedViews.length === 0 ? (
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-12 text-center">
              <Bookmark className="w-12 h-12 text-blue-400 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-white mb-2">No Saved Views Yet</h3>
              <p className="text-gray-400">Save a snapshot of any tab so you can jump back to it later.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {savedViews.map((view) => (
                <SavedViewCard
                  key={view.id}
                  name={view.name}
                  description={view.description || 'Custom saved view'}
                  lastModified={new Date(view.updated_at || view.created_at).toLocaleDateString()}
                  onDelete={() => handleDeleteSavedView(view.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* ===== EVENTS TAB (Legacy) ===== */}
      {activeTab === 'events' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-white">Recent Events ({events.length})</h2>
            <input
              type="text"
              placeholder="Search events..."
              className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
          </div>
          {events.length === 0 ? (
            <div className="text-center py-8 text-gray-400">No events found</div>
          ) : (
            events.map((event) => (
              <div key={event.id} className={`bg-gray-800 border ${getSeverityBg(event.severity)} rounded-lg p-4 hover:border-gray-600 transition`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-1 text-xs font-semibold rounded ${getSeverityColor(event.severity)}`}>
                        {event.severity}
                      </span>
                      <span className="text-white font-semibold">{event.event_type}</span>
                      <span className="text-gray-400 text-sm">from {event.source}</span>
                    </div>
                    <p className="text-gray-300 mt-2">{event.message}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      {new Date(event.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDeleteEvent(event.id)}
                    title="Delete event"
                    className="p-2 hover:bg-red-600/20 rounded transition"
                  >
                    <Trash2 className="w-4 h-4 text-gray-400 hover:text-red-400" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

// Metric Card Component
function MetricCard({ icon, title, value, change, changePositive, trend }) {
  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 hover:border-gray-600 hover:shadow-lg transition-all">
      <div className="flex items-center justify-between mb-3">
        <div className="p-3 bg-gray-700/50 rounded-lg">{icon}</div>
        <span className={`text-sm font-semibold flex items-center gap-1 ${changePositive ? 'text-green-400' : 'text-red-400'}`}>
          {changePositive ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
          {trend}
        </span>
      </div>
      <p className="text-gray-400 text-sm mb-1">{title}</p>
      <p className="text-3xl font-bold text-white">{value}</p>
      <p className={`text-xs mt-2 ${changePositive ? 'text-green-400' : 'text-red-400'}`}>
        {change}
      </p>
    </div>
  );
}

// Stat Box Component (for Analytics)
function StatBox({ label, value, subtitle, icon, trend, trendPositive }) {
  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 shadow-xl">
      <div className="flex items-center justify-between mb-3">
        <div className="p-3 bg-gray-700/50 rounded-lg">{icon}</div>
        <span className={`text-xs font-semibold ${trendPositive ? 'text-green-400' : 'text-red-400'}`}>
          {trend}
        </span>
      </div>
      <p className="text-gray-400 text-sm mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-xs text-gray-500 mt-2">{subtitle}</p>
    </div>
  );
}

// Performance Metric Component
function PerformanceMetric({ label, value, percentage, barColor }) {
  return (
    <div>
      <div className="flex justify-between mb-2">
        <span className="text-gray-400">{label}</span>
        <span className="text-white font-semibold">{value}</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2">
        <div
          className={barColor ? '' : `h-2 rounded-full transition-all ${
            percentage < 50
              ? 'bg-green-500'
              : percentage < 75
              ? 'bg-yellow-500'
              : 'bg-red-500'
          }`}
          style={{ width: `${percentage}%`, height: barColor ? '0.5rem' : undefined, borderRadius: barColor ? '9999px' : undefined, backgroundColor: barColor || undefined, transition: 'width 0.3s ease' }}
        ></div>
      </div>
    </div>
  );
}

// Anomaly Summary Card
function AnomalySummaryCard({ title, value, subtitle, icon, color }) {
  const colorClass = {
    red: 'from-red-900/30 to-red-900/10 border-red-700/50',
    yellow: 'from-yellow-900/30 to-yellow-900/10 border-yellow-700/50',
    blue: 'from-blue-900/30 to-blue-900/10 border-blue-700/50',
  }[color];

  return (
    <div className={`bg-gradient-to-br ${colorClass} rounded-xl border p-6`}>
      <div className="flex items-center justify-between mb-3">
        {icon}
        <span className="text-xs text-gray-400">{subtitle}</span>
      </div>
      <p className="text-gray-400 text-sm mb-1">{title}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

// Admin Stat Card
function AdminStatCard({ label, value, icon }) {
  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6">
      <div className="flex items-center justify-between mb-3">
        <div className="p-3 bg-gray-700/50 rounded-lg">{icon}</div>
      </div>
      <p className="text-gray-400 text-sm mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">{value}</p>
    </div>
  );
}

// Saved View Card
function SavedViewCard({ name, description, lastModified, onDelete }) {
  return (
    <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl border border-gray-700 p-6 hover:border-gray-600 transition-all hover:shadow-lg">
      <div className="flex items-start justify-between mb-3">
        <Bookmark className="w-5 h-5 text-blue-400" />
        <button onClick={onDelete} title="Delete view" className="p-1 hover:bg-red-600/20 rounded transition">
          <Trash2 className="w-4 h-4 text-gray-400 hover:text-red-400" />
        </button>
      </div>
      <h3 className="text-white font-semibold mb-1">{name}</h3>
      <p className="text-gray-400 text-sm mb-3">{description}</p>
      <p className="text-xs text-gray-500">Modified {lastModified}</p>
    </div>
  );
}
