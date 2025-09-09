// Administrative Dashboard - Phase 3

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { analyticsAPI, authAPI } from '../services/api';

interface SystemAnalytics {
  id: number;
  date: string;
  total_students: number;
  active_students: number;
  total_teachers: number;
  active_teachers: number;
  total_assignments_created: number;
  total_recordings_submitted: number;
  total_recordings_reviewed: number;
  avg_response_time: number;
  storage_used_gb: number;
  system_uptime_percentage: number;
}

interface SchoolMetrics {
  total_users: number;
  total_classes: number;
  total_assignments: number;
  total_recordings: number;
  platform_adoption_rate: number;
  avg_engagement_score: number;
}

export const AdminDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'analytics' | 'users' | 'system' | 'reports'>('overview');
  const [systemAnalytics, setSystemAnalytics] = useState<SystemAnalytics[]>([]);
  const [dashboardSummary, setDashboardSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [systemResponse, summaryResponse] = await Promise.all([
        analyticsAPI.getSystemAnalytics(),
        analyticsAPI.getDashboardSummary()
      ]);

      setSystemAnalytics(systemResponse.results || []);
      setDashboardSummary(summaryResponse);
    } catch (err: any) {
      setError('Failed to load dashboard data.');
      console.error('Admin dashboard load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderOverview = () => {
    const latestMetrics = systemAnalytics[0];
    
    return (
      <div className="admin-overview">
        <h3>Platform Overview</h3>
        
        {latestMetrics && (
          <div className="metrics-grid">
            <div className="metric-card users">
              <div className="metric-icon">👥</div>
              <div className="metric-content">
                <h4>{latestMetrics.total_students + latestMetrics.total_teachers}</h4>
                <p>Total Users</p>
                <span className="metric-detail">
                  {latestMetrics.total_students} students, {latestMetrics.total_teachers} teachers
                </span>
              </div>
            </div>

            <div className="metric-card activity">
              <div className="metric-icon">📈</div>
              <div className="metric-content">
                <h4>{latestMetrics.active_students}</h4>
                <p>Active Students</p>
                <span className="metric-detail">
                  {Math.round((latestMetrics.active_students / latestMetrics.total_students) * 100)}% engagement rate
                </span>
              </div>
            </div>

            <div className="metric-card content">
              <div className="metric-icon">📝</div>
              <div className="metric-content">
                <h4>{latestMetrics.total_assignments_created}</h4>
                <p>Total Assignments</p>
                <span className="metric-detail">
                  {latestMetrics.total_recordings_submitted} recordings submitted
                </span>
              </div>
            </div>

            <div className="metric-card performance">
              <div className="metric-icon">⚡</div>
              <div className="metric-content">
                <h4>{Math.round(latestMetrics.avg_response_time)}ms</h4>
                <p>Avg Response Time</p>
                <span className="metric-detail">
                  {latestMetrics.system_uptime_percentage.toFixed(1)}% uptime
                </span>
              </div>
            </div>

            <div className="metric-card storage">
              <div className="metric-icon">💾</div>
              <div className="metric-content">
                <h4>{latestMetrics.storage_used_gb.toFixed(2)} GB</h4>
                <p>Storage Used</p>
                <span className="metric-detail">
                  Audio files and recordings
                </span>
              </div>
            </div>

            <div className="metric-card reviews">
              <div className="metric-icon">✅</div>
              <div className="metric-content">
                <h4>{Math.round((latestMetrics.total_recordings_reviewed / latestMetrics.total_recordings_submitted) * 100)}%</h4>
                <p>Review Rate</p>
                <span className="metric-detail">
                  {latestMetrics.total_recordings_reviewed} of {latestMetrics.total_recordings_submitted} reviewed
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="quick-actions">
          <h4>Quick Actions</h4>
          <div className="action-buttons">
            <button 
              className="action-button"
              onClick={() => analyticsAPI.triggerAnalysis?.()}
            >
              🔄 Run System Analysis
            </button>
            <button 
              className="action-button"
              onClick={() => setActiveTab('reports')}
            >
              📊 Generate Reports
            </button>
            <button 
              className="action-button"
              onClick={() => setActiveTab('users')}
            >
              👥 Manage Users
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderAnalytics = () => (
    <div className="admin-analytics">
      <h3>System Analytics</h3>
      
      {dashboardSummary && (
        <div className="analytics-summary">
          <div className="summary-cards">
            <div className="summary-card flags">
              <h4>Student Flags</h4>
              <div className="summary-content">
                <div className="summary-stat">
                  <span className="stat-number urgent">{dashboardSummary.urgent_flags}</span>
                  <span className="stat-label">Urgent</span>
                </div>
                <div className="summary-stat">
                  <span className="stat-number high">{dashboardSummary.high_priority_flags}</span>
                  <span className="stat-label">High Priority</span>
                </div>
                <div className="summary-stat">
                  <span className="stat-number total">{dashboardSummary.total_flags}</span>
                  <span className="stat-label">Total Active</span>
                </div>
              </div>
            </div>

            <div className="summary-card attention">
              <h4>Students Needing Attention</h4>
              <div className="summary-content">
                <div className="summary-stat">
                  <span className="stat-number attention">{dashboardSummary.students_needing_attention}</span>
                  <span className="stat-label">Require Support</span>
                </div>
              </div>
            </div>
          </div>

          <div className="trend-analysis">
            <h4>Performance Trends</h4>
            {dashboardSummary.students_by_trend && (
              <div className="trend-grid">
                {Object.entries(dashboardSummary.students_by_trend).map(([trend, count]: [string, any]) => (
                  <div key={trend} className="trend-item">
                    <span className={`trend-indicator ${trend}`}>
                      {trend === 'improving' ? '📈' : 
                       trend === 'stable' ? '📊' : 
                       trend === 'declining' ? '📉' : '❓'}
                    </span>
                    <div className="trend-info">
                      <span className="trend-count">{count}</span>
                      <span className="trend-label">{trend.replace('_', ' ')}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="historical-data">
        <h4>Historical Metrics</h4>
        {systemAnalytics.length > 0 && (
          <div className="metrics-table">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Students</th>
                  <th>Active</th>
                  <th>Assignments</th>
                  <th>Recordings</th>
                  <th>Storage (GB)</th>
                  <th>Uptime</th>
                </tr>
              </thead>
              <tbody>
                {systemAnalytics.slice(0, 10).map((metric) => (
                  <tr key={metric.id}>
                    <td>{new Date(metric.date).toLocaleDateString()}</td>
                    <td>{metric.total_students}</td>
                    <td>{metric.active_students}</td>
                    <td>{metric.total_assignments_created}</td>
                    <td>{metric.total_recordings_submitted}</td>
                    <td>{metric.storage_used_gb.toFixed(2)}</td>
                    <td>{metric.system_uptime_percentage.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );

  const renderUsers = () => (
    <div className="admin-users">
      <h3>User Management</h3>
      
      <div className="user-actions">
        <div className="action-section">
          <h4>Teacher Management</h4>
          <p>Manage teacher accounts, assign classes, and monitor activity.</p>
          <button className="management-button">
            👨‍🏫 Manage Teachers
          </button>
        </div>

        <div className="action-section">
          <h4>Student Management</h4>
          <p>View student profiles, track progress, and manage enrollments.</p>
          <button className="management-button">
            👨‍🎓 Manage Students
          </button>
        </div>

        <div className="action-section">
          <h4>Class Administration</h4>
          <p>Oversee class creation, student assignments, and teacher permissions.</p>
          <button className="management-button">
            📚 Manage Classes
          </button>
        </div>

        <div className="action-section">
          <h4>Bulk Operations</h4>
          <p>Import users, export data, and perform batch updates.</p>
          <button className="management-button">
            📦 Bulk Operations
          </button>
        </div>
      </div>

      <div className="coming-soon">
        <h4>🚧 Coming Soon</h4>
        <p>Advanced user management features are being developed:</p>
        <ul>
          <li>User creation and editing interface</li>
          <li>Role-based permission management</li>
          <li>Bulk user import/export</li>
          <li>Activity monitoring and reporting</li>
        </ul>
      </div>
    </div>
  );

  const renderSystem = () => (
    <div className="admin-system">
      <h3>System Administration</h3>
      
      <div className="system-sections">
        <div className="system-section">
          <h4>⚙️ Configuration</h4>
          <div className="config-options">
            <div className="config-item">
              <span>Platform Settings</span>
              <button>Configure</button>
            </div>
            <div className="config-item">
              <span>Email Notifications</span>
              <button>Configure</button>
            </div>
            <div className="config-item">
              <span>Storage Management</span>
              <button>Configure</button>
            </div>
          </div>
        </div>

        <div className="system-section">
          <h4>🔧 Maintenance</h4>
          <div className="maintenance-options">
            <div className="maintenance-item">
              <span>Database Optimization</span>
              <button>Run</button>
            </div>
            <div className="maintenance-item">
              <span>Cache Management</span>
              <button>Clear</button>
            </div>
            <div className="maintenance-item">
              <span>Log Cleanup</span>
              <button>Clean</button>
            </div>
          </div>
        </div>

        <div className="system-section">
          <h4>📊 Monitoring</h4>
          <div className="monitoring-info">
            <p>System health and performance monitoring</p>
            <div className="monitoring-stats">
              <div className="stat">
                <span className="stat-label">API Response Time:</span>
                <span className="stat-value good">Fast</span>
              </div>
              <div className="stat">
                <span className="stat-label">Database Performance:</span>
                <span className="stat-value good">Optimal</span>
              </div>
              <div className="stat">
                <span className="stat-label">Storage Status:</span>
                <span className="stat-value good">Available</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderReports = () => (
    <div className="admin-reports">
      <h3>Administrative Reports</h3>
      
      <div className="report-categories">
        <div className="report-category">
          <h4>📈 Usage Reports</h4>
          <div className="report-list">
            <div className="report-item">
              <span>Platform Usage Summary</span>
              <button>Generate</button>
            </div>
            <div className="report-item">
              <span>Teacher Activity Report</span>
              <button>Generate</button>
            </div>
            <div className="report-item">
              <span>Student Engagement Analysis</span>
              <button>Generate</button>
            </div>
          </div>
        </div>

        <div className="report-category">
          <h4>⚡ Performance Reports</h4>
          <div className="report-list">
            <div className="report-item">
              <span>System Performance Metrics</span>
              <button>Generate</button>
            </div>
            <div className="report-item">
              <span>Storage Usage Analysis</span>
              <button>Generate</button>
            </div>
            <div className="report-item">
              <span>Response Time Trends</span>
              <button>Generate</button>
            </div>
          </div>
        </div>

        <div className="report-category">
          <h4>🎓 Educational Reports</h4>
          <div className="report-list">
            <div className="report-item">
              <span>School-Wide Performance</span>
              <button>Generate</button>
            </div>
            <div className="report-item">
              <span>Learning Outcomes Analysis</span>
              <button>Generate</button>
            </div>
            <div className="report-item">
              <span>Intervention Effectiveness</span>
              <button>Generate</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="admin-loading">
        <h2>Loading administrative dashboard...</h2>
      </div>
    );
  }

  if (!user?.is_admin) {
    return (
      <div className="access-denied">
        <h2>Access Denied</h2>
        <p>Administrative privileges required to access this dashboard.</p>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Administrative Dashboard</h1>
          <div className="admin-info">
            <span>Administrator • {user.first_name} {user.last_name}</span>
            <button onClick={logout} className="logout-button">
              Log Out
            </button>
          </div>
        </div>
      </header>

      <nav className="dashboard-nav">
        <button
          className={`nav-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          🏠 Overview
        </button>
        <button
          className={`nav-button ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          📊 Analytics
        </button>
        <button
          className={`nav-button ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          👥 Users
        </button>
        <button
          className={`nav-button ${activeTab === 'system' ? 'active' : ''}`}
          onClick={() => setActiveTab('system')}
        >
          ⚙️ System
        </button>
        <button
          className={`nav-button ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          📋 Reports
        </button>
      </nav>

      <main className="dashboard-content">
        {error && <div className="error-message">{error}</div>}

        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'analytics' && renderAnalytics()}
        {activeTab === 'users' && renderUsers()}
        {activeTab === 'system' && renderSystem()}
        {activeTab === 'reports' && renderReports()}
      </main>
    </div>
  );
};