// Enhanced Teacher dashboard component for Phase 2

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ClassListItem, StoryListItem, Recording } from '../types';
import { classAPI, storiesAPI, recordingsAPI } from '../services/api';
import { ClassManagement } from './ClassManagement';
import { AssignmentCreation } from './AssignmentCreation';
import { RecordingReview } from './RecordingReview';
import { TeacherAnalytics } from './TeacherAnalytics';
import { BulkAudioGeneration } from './BulkAudioGeneration';
import { AdvancedAnalytics } from './AdvancedAnalytics';
import { BulkReports } from './BulkReports';

export const TeacherDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'overview' | 'classes' | 'assignments' | 'recordings' | 'analytics' | 'advanced' | 'reports' | 'audio'>('overview');
  const [classes, setClasses] = useState<ClassListItem[]>([]);
  const [stories, setStories] = useState<StoryListItem[]>([]);
  const [pendingRecordings, setPendingRecordings] = useState<Recording[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        
        // Load all data in parallel
        const [classesResponse, storiesResponse, recordingsResponse] = await Promise.all([
          classAPI.getClasses(),
          storiesAPI.getStories(),
          recordingsAPI.getTeacherRecordings?.() || Promise.resolve({ results: [] })
        ]);
        
        setClasses(classesResponse.results);
        setStories(storiesResponse.results);
        
        // Only get pending recordings for the overview
        const pending = (recordingsResponse as any).results?.filter((r: Recording) => r.status === 'pending') || [];
        setPendingRecordings(pending.slice(0, 5)); // Show only first 5 for overview
        
      } catch (err: any) {
        setError('Failed to load dashboard data. Please try again.');
        console.error('Dashboard load error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <h2>Loading your teaching dashboard...</h2>
      </div>
    );
  }

  return (
    <div className="teacher-dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Welcome, {user?.first_name} {user?.last_name}!</h1>
          <div className="user-info">
            <span>Teacher • {user?.school}</span>
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
          Overview
        </button>
        <button
          className={`nav-button ${activeTab === 'classes' ? 'active' : ''}`}
          onClick={() => setActiveTab('classes')}
        >
          My Classes ({classes.length})
        </button>
        <button
          className={`nav-button ${activeTab === 'assignments' ? 'active' : ''}`}
          onClick={() => setActiveTab('assignments')}
        >
          Create Assignment
        </button>
        <button
          className={`nav-button ${activeTab === 'recordings' ? 'active' : ''}`}
          onClick={() => setActiveTab('recordings')}
        >
          Review Recordings ({pendingRecordings.length})
        </button>
        <button
          className={`nav-button ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          Analytics
        </button>
        <button
          className={`nav-button ${activeTab === 'advanced' ? 'active' : ''}`}
          onClick={() => setActiveTab('advanced')}
        >
          🚀 Advanced
        </button>
        <button
          className={`nav-button ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          📊 Reports
        </button>
        <button
          className={`nav-button ${activeTab === 'audio' ? 'active' : ''}`}
          onClick={() => setActiveTab('audio')}
        >
          Audio Generation
        </button>
      </nav>

      <main className="dashboard-content">
        {error && <div className="error-message">{error}</div>}

        {activeTab === 'overview' && (
          <div className="overview-section">
            <h2>Teaching Overview</h2>
            
            <div className="overview-cards">
              <div className="overview-card">
                <div className="card-icon">📚</div>
                <div className="card-content">
                  <h3>{classes.length}</h3>
                  <p>Active Classes</p>
                </div>
              </div>
              
              <div className="overview-card">
                <div className="card-icon">👥</div>
                <div className="card-content">
                  <h3>{classes.reduce((total, cls) => total + cls.student_count, 0)}</h3>
                  <p>Total Students</p>
                </div>
              </div>
              
              <div className="overview-card">
                <div className="card-icon">🎤</div>
                <div className="card-content">
                  <h3>{pendingRecordings.length}</h3>
                  <p>Pending Reviews</p>
                </div>
              </div>
              
              <div className="overview-card">
                <div className="card-icon">📖</div>
                <div className="card-content">
                  <h3>{stories.length}</h3>
                  <p>Available Stories</p>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="quick-actions">
              <h3>Quick Actions</h3>
              <div className="action-buttons">
                <button 
                  className="action-button primary"
                  onClick={() => setActiveTab('assignments')}
                >
                  📝 Create New Assignment
                </button>
                <button 
                  className="action-button"
                  onClick={() => setActiveTab('classes')}
                >
                  👥 Manage Classes
                </button>
                <button 
                  className="action-button"
                  onClick={() => setActiveTab('recordings')}
                >
                  🎤 Review Recordings
                </button>
              </div>
            </div>

            {/* Recent Activity */}
            {pendingRecordings.length > 0 && (
              <div className="recent-activity">
                <h3>Recent Submissions Waiting for Review</h3>
                <div className="activity-list">
                  {pendingRecordings.map((recording) => (
                    <div key={recording.id} className="activity-item">
                      <div className="activity-info">
                        <strong>{recording.student_name}</strong> submitted "{recording.story_title}"
                        <span className="activity-time">
                          {new Date(recording.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <button 
                        className="review-button"
                        onClick={() => setActiveTab('recordings')}
                      >
                        Review
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'classes' && (
          <ClassManagement 
            classes={classes} 
            onClassesChange={setClasses}
          />
        )}

        {activeTab === 'assignments' && (
          <AssignmentCreation 
            classes={classes}
            stories={stories}
          />
        )}

        {activeTab === 'recordings' && (
          <RecordingReview />
        )}

        {activeTab === 'analytics' && (
          <TeacherAnalytics classes={classes} />
        )}

        {activeTab === 'advanced' && (
          <AdvancedAnalytics classes={classes} />
        )}

        {activeTab === 'reports' && (
          <BulkReports classes={classes} />
        )}

        {activeTab === 'audio' && (
          <BulkAudioGeneration />
        )}
      </main>
    </div>
  );
};