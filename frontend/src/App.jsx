import React, { useState, useEffect } from 'react';
import { BarChart3, LogOut, Menu, X, Activity, TrendingUp, AlertCircle, Lightbulb, Settings, Bookmark } from 'lucide-react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');
    if (token && userData) {
      setIsAuthenticated(true);
      setUser(JSON.parse(userData));
    }
  }, []);

  const handleLogin = (userData, token) => {
    setUser(userData);
    setIsAuthenticated(true);
    localStorage.setItem('access_token', token);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUser(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      {/* Sidebar */}
      <div
        className={`${
          sidebarOpen ? 'w-64' : 'w-0'
        } relative transition-all duration-300 bg-gray-800 border-r border-gray-700 overflow-hidden flex-shrink-0`}
      >
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg">
              <BarChart3 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">LogPulse</h1>
              <p className="text-xs text-gray-400">Real-time Analytics</p>
            </div>
          </div>
        </div>

        <nav className="p-4 space-y-2">
          <NavItem 
            icon={<Activity className="w-5 h-5" />} 
            label="Dashboard" 
            id="overview" 
            active={activeTab === 'overview'}
            onClick={() => setActiveTab('overview')}
          />
          <NavItem 
            icon={<TrendingUp className="w-5 h-5" />} 
            label="Analytics" 
            id="analytics" 
            active={activeTab === 'analytics'}
            onClick={() => setActiveTab('analytics')}
          />
          <NavItem 
            icon={<AlertCircle className="w-5 h-5" />} 
            label="Anomalies" 
            id="anomalies" 
            active={activeTab === 'anomalies'}
            onClick={() => setActiveTab('anomalies')}
          />
          <NavItem 
            icon={<Lightbulb className="w-5 h-5" />} 
            label="Insights" 
            id="insights" 
            active={activeTab === 'insights'}
            onClick={() => setActiveTab('insights')}
          />
          <NavItem 
            icon={<Settings className="w-5 h-5" />} 
            label="Admin" 
            id="admin" 
            active={activeTab === 'admin'}
            onClick={() => setActiveTab('admin')}
          />
          <NavItem 
            icon={<Bookmark className="w-5 h-5" />} 
            label="Saved Views" 
            id="saved-views" 
            active={activeTab === 'saved-views'}
            onClick={() => setActiveTab('saved-views')}
          />
        </nav>

        <div className="absolute bottom-0 w-64 p-4 text-center border-t border-gray-700">
          <p className="text-xs text-gray-500">LogPulse v1.0 &middot; {new Date().getFullYear()}</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-gray-700 rounded-lg transition"
          >
            {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-300">Live</span>
            </div>
            <div className="flex items-center gap-3 pl-3 border-l border-gray-700">
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white text-sm font-semibold">
                {user?.username?.[0]?.toUpperCase() || '?'}
              </div>
              <div className="text-right">
                <p className="text-sm font-medium text-white">{user?.username}</p>
                <p className="text-xs text-gray-400">
                  {user?.is_admin ? 'Administrator' : 'User'}
                </p>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 hover:bg-gray-700 rounded-lg transition text-red-400 hover:text-red-300"
                title="Log out"
              >
                <LogOut size={20} />
              </button>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="flex-1 overflow-auto">
          <div key={activeTab} className="animate-fade-in">
            <Dashboard activeTab={activeTab} setActiveTab={setActiveTab} user={user} />
          </div>
        </div>
      </div>
    </div>
  );
}

function NavItem({ icon, label, id, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`relative w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
        active
          ? 'bg-gradient-to-r from-blue-600/90 to-cyan-600/90 text-white shadow-lg shadow-blue-900/30'
          : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/60'
      }`}
    >
      {active && <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 bg-white/80 rounded-r"></span>}
      {icon}
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
}
