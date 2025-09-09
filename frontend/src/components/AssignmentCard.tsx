// Assignment card component for displaying assignment information

import React, { useState } from 'react';
import { StudentAssignment, Story } from '../types';
import { storiesAPI } from '../services/api';
import { StoryReader } from './StoryReader';

interface AssignmentCardProps {
  assignment: StudentAssignment;
}

export const AssignmentCard: React.FC<AssignmentCardProps> = ({ assignment }) => {
  const [showReader, setShowReader] = useState(false);
  const [fullStory, setFullStory] = useState<Story | null>(null);
  const [loading, setLoading] = useState(false);

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'No due date';
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusColor = () => {
    if (assignment.is_completed) return '#4CAF50';
    if (!assignment.can_attempt) return '#F44336';
    return '#2196F3';
  };

  const getStatusText = () => {
    if (assignment.is_completed) return 'Completed';
    if (!assignment.can_attempt) return 'Max attempts reached';
    return `${assignment.attempts_used} / ${3} attempts used`;
  };

  const handleStartAssignment = async () => {
    try {
      setLoading(true);
      const storyData = await storiesAPI.getStory(assignment.story_id);
      setFullStory(storyData);
      setShowReader(true);
    } catch (error) {
      console.error('Failed to load assignment story:', error);
    } finally {
      setLoading(false);
    }
  };

  if (showReader && fullStory) {
    return (
      <StoryReader 
        story={fullStory} 
        assignment={assignment}
        onClose={() => {
          setShowReader(false);
          setFullStory(null);
        }} 
      />
    );
  }

  return (
    <div className="assignment-card">
      <div className="assignment-header">
        <h3 className="assignment-title">{assignment.assignment_title}</h3>
        <div 
          className="status-badge"
          style={{ backgroundColor: getStatusColor() }}
        >
          {getStatusText()}
        </div>
      </div>
      
      <div className="assignment-details">
        <div className="detail-item">
          <span className="label">Story:</span>
          <span className="value">{assignment.story_title}</span>
        </div>
        <div className="detail-item">
          <span className="label">Due Date:</span>
          <span className="value">{formatDate(assignment.due_date)}</span>
        </div>
        <div className="detail-item">
          <span className="label">Assigned:</span>
          <span className="value">{new Date(assignment.created_at).toLocaleDateString()}</span>
        </div>
      </div>

      <div className="assignment-actions">
        <button 
          className="start-button"
          onClick={handleStartAssignment}
          disabled={loading || (!assignment.can_attempt && !assignment.is_completed)}
        >
          {loading ? 'Loading...' : assignment.is_completed ? 'Review' : 'Start Assignment'}
        </button>
      </div>
    </div>
  );
};