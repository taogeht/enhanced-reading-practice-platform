// Student dashboard component showing assignments and story library

import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { StudentAssignment, StoryListItem } from '../types';
import { assignmentsAPI, storiesAPI } from '../services/api';
import { StoryCard } from './StoryCard';
import { AssignmentCard } from './AssignmentCard';

export const StudentDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [assignments, setAssignments] = useState<StudentAssignment[]>([]);
  const [stories, setStories] = useState<StoryListItem[]>([]);
  const [activeTab, setActiveTab] = useState<'assignments' | 'library'>('assignments');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Load assignments and stories in parallel
        const [assignmentsResponse, storiesResponse] = await Promise.all([
          assignmentsAPI.getStudentAssignments(),
          storiesAPI.getStories(user?.grade_level)
        ]);
        
        setAssignments(assignmentsResponse.results);
        setStories(storiesResponse.results);
      } catch (err: any) {
        setError('Failed to load dashboard data. Please try again.');
        console.error('Dashboard load error:', err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [user?.grade_level]);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <h2>Loading your assignments...</h2>
      </div>
    );
  }

  return (
    <div className="student-dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>Welcome back, {user?.first_name}!</h1>
          <div className="user-info">
            <span>Grade {user?.grade_level} • {user?.school}</span>
            <button onClick={logout} className="logout-button">
              Log Out
            </button>
          </div>
        </div>
      </header>

      <nav className="dashboard-nav">
        <button
          className={`nav-button ${activeTab === 'assignments' ? 'active' : ''}`}
          onClick={() => setActiveTab('assignments')}
        >
          My Assignments ({assignments.length})
        </button>
        <button
          className={`nav-button ${activeTab === 'library' ? 'active' : ''}`}
          onClick={() => setActiveTab('library')}
        >
          Story Library ({stories.length})
        </button>
      </nav>

      <main className="dashboard-content">
        {error && <div className="error-message">{error}</div>}

        {activeTab === 'assignments' && (
          <div className="assignments-section">
            <h2>Your Reading Assignments</h2>
            {assignments.length === 0 ? (
              <div className="empty-state">
                <p>No assignments yet. Check back later!</p>
              </div>
            ) : (
              <div className="assignments-grid">
                {assignments.map((assignment) => (
                  <AssignmentCard key={assignment.id} assignment={assignment} />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'library' && (
          <div className="library-section">
            <h2>Story Library</h2>
            <p className="library-description">
              Practice reading with stories at your grade level
            </p>
            {stories.length === 0 ? (
              <div className="empty-state">
                <p>No stories available for your grade level.</p>
              </div>
            ) : (
              <div className="stories-grid">
                {stories.map((story) => (
                  <StoryCard key={story.id} story={story} />
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
};