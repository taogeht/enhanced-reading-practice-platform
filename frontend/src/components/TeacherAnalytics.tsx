// Teacher Analytics component for Phase 2

import React, { useState, useEffect } from 'react';
import { ClassListItem, Recording, Assignment } from '../types';
import { recordingsAPI, assignmentsAPI } from '../services/api';

interface TeacherAnalyticsProps {
  classes: ClassListItem[];
}

interface AnalyticsData {
  totalAssignments: number;
  totalRecordings: number;
  pendingReviews: number;
  completedReviews: number;
  avgFluencyScore: number;
  avgAccuracyScore: number;
  recentActivity: Recording[];
}

export const TeacherAnalytics: React.FC<TeacherAnalyticsProps> = ({ classes }) => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData>({
    totalAssignments: 0,
    totalRecordings: 0,
    pendingReviews: 0,
    completedReviews: 0,
    avgFluencyScore: 0,
    avgAccuracyScore: 0,
    recentActivity: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const totalStudents = classes.reduce((sum, cls) => sum + cls.student_count, 0);

  useEffect(() => {
    loadAnalyticsData();
  }, []);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      
      const [recordingsResponse, assignmentsResponse] = await Promise.all([
        recordingsAPI.getTeacherRecordings?.() || Promise.resolve({ results: [] }),
        assignmentsAPI.getAssignments?.() || Promise.resolve({ results: [] })
      ]);

      const recordings = (recordingsResponse as any).results || [];
      const assignments = (assignmentsResponse as any).results || [];
      
      const pendingRecordings = recordings.filter((r: Recording) => r.status === 'pending');
      const reviewedRecordings = recordings.filter((r: Recording) => r.status === 'reviewed');
      
      // Calculate average scores
      const recordingsWithScores = recordings.filter((r: Recording) => 
        r.status === 'reviewed' && r.fluency_score && r.accuracy_score
      );
      
      const avgFluency = recordingsWithScores.length > 0 
        ? recordingsWithScores.reduce((sum: number, r: any) => sum + (r.fluency_score || 0), 0) / recordingsWithScores.length
        : 0;
      
      const avgAccuracy = recordingsWithScores.length > 0 
        ? recordingsWithScores.reduce((sum: number, r: any) => sum + (r.accuracy_score || 0), 0) / recordingsWithScores.length
        : 0;

      setAnalyticsData({
        totalAssignments: assignments.length,
        totalRecordings: recordings.length,
        pendingReviews: pendingRecordings.length,
        completedReviews: reviewedRecordings.length,
        avgFluencyScore: Math.round(avgFluency * 10) / 10,
        avgAccuracyScore: Math.round(avgAccuracy * 10) / 10,
        recentActivity: recordings.slice(0, 5)
      });
      
    } catch (err: any) {
      setError('Failed to load analytics data.');
      console.error('Analytics load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getCompletionRate = () => {
    if (analyticsData.totalRecordings === 0) return 0;
    return Math.round((analyticsData.completedReviews / analyticsData.totalRecordings) * 100);
  };

  const getGradeDistribution = () => {
    const reviewedRecordings = analyticsData.recentActivity.filter(r => r.status === 'reviewed');
    const distribution = { excellent: 0, good: 0, needs_practice: 0 };
    
    reviewedRecordings.forEach(recording => {
      if (recording.grade === 'excellent') distribution.excellent++;
      else if (recording.grade === 'good') distribution.good++;
      else if (recording.grade === 'needs_practice') distribution.needs_practice++;
    });
    
    return distribution;
  };

  if (loading) {
    return <div className="loading">Loading analytics...</div>;
  }

  const gradeDistribution = getGradeDistribution();

  return (
    <div className="teacher-analytics">
      <h2>Class Analytics & Progress</h2>
      <p>Track student progress and class performance across all your classes.</p>

      {error && <div className="error-message">{error}</div>}

      {/* Current Data Overview */}
      <div className="current-stats">
        <h3>Teaching Overview</h3>
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📚</div>
            <div className="stat-content">
              <h4>{classes.length}</h4>
              <p>Active Classes</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">👥</div>
            <div className="stat-content">
              <h4>{totalStudents}</h4>
              <p>Total Students</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📝</div>
            <div className="stat-content">
              <h4>{analyticsData.totalAssignments}</h4>
              <p>Assignments Created</p>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🎤</div>
            <div className="stat-content">
              <h4>{analyticsData.totalRecordings}</h4>
              <p>Total Recordings</p>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="performance-metrics">
        <h3>Performance Metrics</h3>
        <div className="metrics-grid">
          <div className="metric-card">
            <h4>Review Status</h4>
            <div className="metric-content">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{width: `${getCompletionRate()}%`}}
                ></div>
              </div>
              <div className="metric-stats">
                <span>{analyticsData.completedReviews} reviewed</span>
                <span>{analyticsData.pendingReviews} pending</span>
                <span>{getCompletionRate()}% complete</span>
              </div>
            </div>
          </div>

          {analyticsData.avgFluencyScore > 0 && (
            <div className="metric-card">
              <h4>Average Scores</h4>
              <div className="score-metrics">
                <div className="score-item">
                  <span className="score-label">Fluency:</span>
                  <span className="score-value">{analyticsData.avgFluencyScore}/5</span>
                </div>
                <div className="score-item">
                  <span className="score-label">Accuracy:</span>
                  <span className="score-value">{analyticsData.avgAccuracyScore}/5</span>
                </div>
              </div>
            </div>
          )}

          {Object.values(gradeDistribution).some(v => v > 0) && (
            <div className="metric-card">
              <h4>Grade Distribution</h4>
              <div className="grade-distribution">
                <div className="grade-item">
                  <span className="grade-label">🌟 Excellent:</span>
                  <span className="grade-count">{gradeDistribution.excellent}</span>
                </div>
                <div className="grade-item">
                  <span className="grade-label">👍 Good:</span>
                  <span className="grade-count">{gradeDistribution.good}</span>
                </div>
                <div className="grade-item">
                  <span className="grade-label">📚 Needs Practice:</span>
                  <span className="grade-count">{gradeDistribution.needs_practice}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recent Activity */}
      {analyticsData.recentActivity.length > 0 && (
        <div className="recent-activity">
          <h3>Recent Student Activity</h3>
          <div className="activity-list">
            {analyticsData.recentActivity.map((recording) => (
              <div key={recording.id} className="activity-item">
                <div className="activity-info">
                  <div className="activity-header">
                    <strong>{recording.student_name}</strong>
                    <span className={`status-badge ${recording.status}`}>
                      {recording.status}
                    </span>
                  </div>
                  <div className="activity-details">
                    <span>📖 {recording.story_title}</span>
                    <span>📅 {new Date(recording.created_at).toLocaleDateString()}</span>
                    {recording.grade && (
                      <span className={`grade-indicator grade-${recording.grade}`}>
                        {recording.grade === 'excellent' ? '🌟' : 
                         recording.grade === 'good' ? '👍' : '📚'}
                        {recording.grade}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Class Breakdown */}
      <div className="class-breakdown">
        <h3>Class Overview</h3>
        {classes.length === 0 ? (
          <div className="empty-state">
            <p>No classes created yet. Create your first class to start tracking progress!</p>
          </div>
        ) : (
          <div className="class-analytics-grid">
            {classes.map((classItem) => (
              <div key={classItem.id} className="class-analytics-card">
                <div className="class-header">
                  <h4>{classItem.name}</h4>
                  <span className="grade-badge">Grade {classItem.grade_level}</span>
                </div>
                <div className="class-stats">
                  <div className="stat-item">
                    <span className="stat-label">Students:</span>
                    <span className="stat-value">{classItem.student_count}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Created:</span>
                    <span className="stat-value">
                      {new Date(classItem.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">School Year:</span>
                    <span className="stat-value">{classItem.school_year}</span>
                  </div>
                </div>
                <div className="class-progress">
                  <div className="progress-placeholder">
                    <div className="chart-placeholder">
                      📊 Class Progress<br/>
                      <small>Detailed analytics coming in Phase 3</small>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="coming-soon-notice">
        <h3>🚀 Phase 3 Features</h3>
        <p>Advanced analytics features planned for the next release:</p>
        <ul>
          <li>Interactive progress charts and graphs</li>
          <li>Individual student performance tracking</li>
          <li>Reading fluency trend analysis over time</li>
          <li>Detailed assignment completion reports</li>
          <li>Automated insights and recommendations</li>
          <li>Export capabilities for reports</li>
        </ul>
      </div>
    </div>
  );
};