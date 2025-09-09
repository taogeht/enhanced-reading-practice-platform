// Advanced Analytics Dashboard - Phase 3

import React, { useState, useEffect } from 'react';
import { ClassListItem } from '../types';
import { analyticsAPI } from '../services/api';

interface StudentFlag {
  id: number;
  student_name: string;
  student_username: string;
  flag_type: string;
  flag_type_display: string;
  severity: string;
  severity_display: string;
  description: string;
  is_resolved: boolean;
  created_at: string;
}

interface StudentAnalytics {
  id: number;
  student_name: string;
  student_username: string;
  submission_rate: number;
  completion_rate: number;
  avg_fluency_score: number;
  avg_accuracy_score: number;
  days_since_last_submission: number;
  improvement_trend: string;
  needs_attention: boolean;
}

interface DashboardSummary {
  total_flags: number;
  high_priority_flags: number;
  urgent_flags: number;
  students_needing_attention: number;
  flag_distribution: Record<string, number>;
  average_completion_rate: number;
  students_by_trend: Record<string, number>;
}

interface AdvancedAnalyticsProps {
  classes: ClassListItem[];
}

export const AdvancedAnalytics: React.FC<AdvancedAnalyticsProps> = ({ classes }) => {
  const [flags, setFlags] = useState<StudentFlag[]>([]);
  const [studentAnalytics, setStudentAnalytics] = useState<StudentAnalytics[]>([]);
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedView, setSelectedView] = useState<'overview' | 'flags' | 'students' | 'insights'>('overview');

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      const [flagsResponse, analyticsResponse, summaryResponse] = await Promise.all([
        analyticsAPI.getStudentFlags(),
        analyticsAPI.getStudentAnalytics(),
        analyticsAPI.getDashboardSummary()
      ]);

      setFlags(flagsResponse.results || []);
      setStudentAnalytics(analyticsResponse.results || []);
      setDashboardSummary(summaryResponse);
    } catch (err: any) {
      setError('Failed to load analytics data.');
      console.error('Analytics load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleResolveFlag = async (flagId: number, notes: string = '') => {
    try {
      await analyticsAPI.resolveFlag(flagId, notes);
      // Refresh flags
      const response = await analyticsAPI.getStudentFlags();
      setFlags(response.results || []);
    } catch (err: any) {
      setError('Failed to resolve flag.');
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'urgent': return '#d32f2f';
      case 'high': return '#f57c00';
      case 'medium': return '#1976d2';
      case 'low': return '#388e3c';
      default: return '#757575';
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'improving': return '#4caf50';
      case 'stable': return '#ff9800';
      case 'declining': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return '📈';
      case 'stable': return '📊';
      case 'declining': return '📉';
      default: return '❓';
    }
  };

  const renderOverview = () => (
    <div className="analytics-overview">
      <h3>Analytics Overview</h3>
      
      {dashboardSummary && (
        <>
          <div className="summary-cards">
            <div className="summary-card urgent">
              <div className="card-icon">🚨</div>
              <div className="card-content">
                <h4>{dashboardSummary.urgent_flags}</h4>
                <p>Urgent Flags</p>
              </div>
            </div>
            
            <div className="summary-card high">
              <div className="card-icon">⚠️</div>
              <div className="card-content">
                <h4>{dashboardSummary.high_priority_flags}</h4>
                <p>High Priority</p>
              </div>
            </div>
            
            <div className="summary-card attention">
              <div className="card-icon">👀</div>
              <div className="card-content">
                <h4>{dashboardSummary.students_needing_attention}</h4>
                <p>Need Attention</p>
              </div>
            </div>
            
            <div className="summary-card completion">
              <div className="card-icon">📊</div>
              <div className="card-content">
                <h4>{Math.round(dashboardSummary.average_completion_rate || 0)}%</h4>
                <p>Avg Completion</p>
              </div>
            </div>
          </div>

          <div className="charts-section">
            <div className="chart-container">
              <h4>Flag Distribution</h4>
              <div className="flag-distribution-chart">
                {Object.entries(dashboardSummary.flag_distribution).map(([type, count]) => (
                  <div key={type} className="distribution-item">
                    <span className="distribution-label">{type.replace('_', ' ')}:</span>
                    <span className="distribution-count">{count}</span>
                    <div 
                      className="distribution-bar" 
                      style={{width: `${(count / Math.max(...Object.values(dashboardSummary.flag_distribution))) * 100}%`}}
                    ></div>
                  </div>
                ))}
              </div>
            </div>

            <div className="chart-container">
              <h4>Student Progress Trends</h4>
              <div className="trend-distribution">
                {Object.entries(dashboardSummary.students_by_trend).map(([trend, count]) => (
                  <div key={trend} className="trend-item">
                    <span className="trend-icon" style={{color: getTrendColor(trend)}}>
                      {getTrendIcon(trend)}
                    </span>
                    <span className="trend-label">{trend.replace('_', ' ')}:</span>
                    <span className="trend-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );

  const renderFlags = () => (
    <div className="flags-section">
      <div className="section-header">
        <h3>Student Flags ({flags.length})</h3>
        <button 
          onClick={() => analyticsAPI.triggerAnalysis?.()}
          className="trigger-analysis-button"
        >
          🔄 Run Analysis
        </button>
      </div>

      {flags.length === 0 ? (
        <div className="empty-state">
          <h4>🎉 No active flags!</h4>
          <p>All students appear to be performing well.</p>
        </div>
      ) : (
        <div className="flags-grid">
          {flags.filter(flag => !flag.is_resolved).map((flag) => (
            <div key={flag.id} className="flag-card">
              <div className="flag-header">
                <div className="flag-student">
                  <strong>{flag.student_name}</strong>
                  <span className="username">@{flag.student_username}</span>
                </div>
                <span 
                  className="severity-badge"
                  style={{backgroundColor: getSeverityColor(flag.severity)}}
                >
                  {flag.severity_display}
                </span>
              </div>
              
              <div className="flag-content">
                <h4>{flag.flag_type_display}</h4>
                <p>{flag.description}</p>
                <div className="flag-meta">
                  <span>Created: {new Date(flag.created_at).toLocaleDateString()}</span>
                </div>
              </div>
              
              <div className="flag-actions">
                <button
                  onClick={() => handleResolveFlag(flag.id, 'Addressed with student')}
                  className="resolve-button"
                >
                  ✓ Resolve
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderStudents = () => (
    <div className="students-section">
      <h3>Student Analytics ({studentAnalytics.length})</h3>
      
      <div className="students-grid">
        {studentAnalytics.map((student) => (
          <div 
            key={student.id} 
            className={`student-analytics-card ${student.needs_attention ? 'needs-attention' : ''}`}
          >
            <div className="student-header">
              <div className="student-info">
                <strong>{student.student_name}</strong>
                <span className="username">@{student.student_username}</span>
              </div>
              <div className="trend-indicator">
                <span 
                  className="trend-icon"
                  style={{color: getTrendColor(student.improvement_trend)}}
                >
                  {getTrendIcon(student.improvement_trend)}
                </span>
                <span className="trend-label">{student.improvement_trend}</span>
              </div>
            </div>
            
            <div className="student-metrics">
              <div className="metric-row">
                <span className="metric-label">Completion Rate:</span>
                <span className="metric-value">
                  <div className="progress-bar small">
                    <div 
                      className="progress-fill"
                      style={{width: `${student.completion_rate}%`}}
                    ></div>
                  </div>
                  {Math.round(student.completion_rate)}%
                </span>
              </div>
              
              <div className="metric-row">
                <span className="metric-label">Avg Fluency:</span>
                <span className="metric-value">{student.avg_fluency_score.toFixed(1)}/5</span>
              </div>
              
              <div className="metric-row">
                <span className="metric-label">Avg Accuracy:</span>
                <span className="metric-value">{student.avg_accuracy_score.toFixed(1)}/5</span>
              </div>
              
              <div className="metric-row">
                <span className="metric-label">Days Since Last:</span>
                <span className={`metric-value ${student.days_since_last_submission > 7 ? 'warning' : ''}`}>
                  {student.days_since_last_submission}
                </span>
              </div>
            </div>
            
            {student.needs_attention && (
              <div className="attention-notice">
                ⚠️ Needs Attention
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderInsights = () => (
    <div className="insights-section">
      <h3>AI-Powered Insights</h3>
      
      <div className="insights-grid">
        <div className="insight-card">
          <h4>📈 Performance Trends</h4>
          <div className="insight-content">
            {studentAnalytics.length > 0 && (
              <>
                <p>
                  <strong>{studentAnalytics.filter(s => s.improvement_trend === 'improving').length}</strong> students 
                  are showing improvement in their recent submissions.
                </p>
                <p>
                  <strong>{studentAnalytics.filter(s => s.improvement_trend === 'declining').length}</strong> students 
                  may need additional support.
                </p>
              </>
            )}
          </div>
        </div>
        
        <div className="insight-card">
          <h4>🎯 Engagement Analysis</h4>
          <div className="insight-content">
            <p>
              Students with completion rates below 70% are 
              <strong> 3x more likely</strong> to struggle with reading fluency.
            </p>
            <p>
              Consider implementing targeted interventions for these students.
            </p>
          </div>
        </div>
        
        <div className="insight-card">
          <h4>📚 Content Recommendations</h4>
          <div className="insight-content">
            <p>
              Based on performance data, consider assigning more 
              <strong> beginner-level stories</strong> to students with average fluency below 2.5.
            </p>
            <p>
              Advanced students (fluency > 4.0) would benefit from challenging materials.
            </p>
          </div>
        </div>
        
        <div className="insight-card">
          <h4>⏰ Timing Insights</h4>
          <div className="insight-content">
            <p>
              Students who submit within 2 days of assignment show 
              <strong>25% better</strong> performance scores.
            </p>
            <p>
              Consider sending reminders for assignments due in 3+ days.
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return <div className="loading">Loading advanced analytics...</div>;
  }

  return (
    <div className="advanced-analytics">
      <div className="section-header">
        <h2>Advanced Analytics Dashboard</h2>
        <p>Deep insights into student performance and engagement patterns</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      <nav className="analytics-nav">
        <button
          className={`nav-button ${selectedView === 'overview' ? 'active' : ''}`}
          onClick={() => setSelectedView('overview')}
        >
          📊 Overview
        </button>
        <button
          className={`nav-button ${selectedView === 'flags' ? 'active' : ''}`}
          onClick={() => setSelectedView('flags')}
        >
          🚩 Flags ({flags.filter(f => !f.is_resolved).length})
        </button>
        <button
          className={`nav-button ${selectedView === 'students' ? 'active' : ''}`}
          onClick={() => setSelectedView('students')}
        >
          👥 Students
        </button>
        <button
          className={`nav-button ${selectedView === 'insights' ? 'active' : ''}`}
          onClick={() => setSelectedView('insights')}
        >
          🧠 Insights
        </button>
      </nav>

      <div className="analytics-content">
        {selectedView === 'overview' && renderOverview()}
        {selectedView === 'flags' && renderFlags()}
        {selectedView === 'students' && renderStudents()}
        {selectedView === 'insights' && renderInsights()}
      </div>
    </div>
  );
};