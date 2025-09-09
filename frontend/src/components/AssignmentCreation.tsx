// Assignment Creation component for teachers

import React, { useState } from 'react';
import { ClassListItem, StoryListItem, CreateClassAssignmentRequest } from '../types';
import { teacherAssignmentAPI } from '../services/api';

interface AssignmentCreationProps {
  classes: ClassListItem[];
  stories: StoryListItem[];
}

export const AssignmentCreation: React.FC<AssignmentCreationProps> = ({ classes, stories }) => {
  const [assignment, setAssignment] = useState<CreateClassAssignmentRequest>({
    class_id: 0,
    story_id: 0,
    title: '',
    description: '',
    due_date: '',
    max_attempts: 3
  });
  
  const [selectedStory, setSelectedStory] = useState<StoryListItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleStorySelect = (story: StoryListItem) => {
    setSelectedStory(story);
    setAssignment({
      ...assignment,
      story_id: story.id,
      title: `Reading Practice: ${story.title}`
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!assignment.class_id || !assignment.story_id || !assignment.title) {
      setError('Please fill in all required fields.');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setSuccess('');
      
      const response = await teacherAssignmentAPI.createClassAssignment(assignment);
      setSuccess(response.message);
      
      // Reset form
      setAssignment({
        class_id: 0,
        story_id: 0,
        title: '',
        description: '',
        due_date: '',
        max_attempts: 3
      });
      setSelectedStory(null);
      
    } catch (err: any) {
      setError('Failed to create assignment. Please try again.');
      console.error('Assignment creation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  const getSelectedClass = () => {
    return classes.find(c => c.id === assignment.class_id);
  };

  return (
    <div className="assignment-creation">
      <h2>Create Class Assignment</h2>
      <p>Assign a story to an entire class for reading practice and assessment.</p>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <form onSubmit={handleSubmit} className="assignment-form">
        {/* Class Selection */}
        <div className="form-section">
          <h3>1. Select Class</h3>
          <div className="class-selection">
            {classes.length === 0 ? (
              <p>No classes available. Create a class first to assign stories.</p>
            ) : (
              <div className="class-grid">
                {classes.map((classItem) => (
                  <div
                    key={classItem.id}
                    className={`class-option ${assignment.class_id === classItem.id ? 'selected' : ''}`}
                    onClick={() => setAssignment({ ...assignment, class_id: classItem.id })}
                  >
                    <h4>{classItem.name}</h4>
                    <div className="class-info">
                      <span>Grade {classItem.grade_level}</span>
                      <span>• {classItem.student_count} students</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Story Selection */}
        <div className="form-section">
          <h3>2. Select Story</h3>
          <div className="story-selection">
            {stories.length === 0 ? (
              <p>No stories available.</p>
            ) : (
              <div className="story-grid">
                {stories.map((story) => (
                  <div
                    key={story.id}
                    className={`story-option ${assignment.story_id === story.id ? 'selected' : ''}`}
                    onClick={() => handleStorySelect(story)}
                  >
                    <div className="story-header">
                      <h4>{story.title}</h4>
                      <div className="difficulty-badge" style={{
                        backgroundColor: story.difficulty === 'easy' ? '#4CAF50' :
                                       story.difficulty === 'medium' ? '#FF9800' : '#F44336'
                      }}>
                        {story.difficulty}
                      </div>
                    </div>
                    <div className="story-details">
                      <span>Grade {story.grade_level}</span>
                      <span>• {story.word_count} words</span>
                      <span>• {story.estimated_reading_time}s</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Assignment Details */}
        <div className="form-section">
          <h3>3. Assignment Details</h3>
          
          <div className="form-group">
            <label htmlFor="title">Assignment Title:</label>
            <input
              id="title"
              type="text"
              value={assignment.title}
              onChange={(e) => setAssignment({ ...assignment, title: e.target.value })}
              placeholder="Enter assignment title"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description (Optional):</label>
            <textarea
              id="description"
              value={assignment.description}
              onChange={(e) => setAssignment({ ...assignment, description: e.target.value })}
              placeholder="Instructions for students..."
              rows={3}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="due-date">Due Date (Optional):</label>
              <input
                id="due-date"
                type="datetime-local"
                value={assignment.due_date}
                onChange={(e) => setAssignment({ ...assignment, due_date: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label htmlFor="max-attempts">Max Attempts:</label>
              <select
                id="max-attempts"
                value={assignment.max_attempts}
                onChange={(e) => setAssignment({ ...assignment, max_attempts: Number(e.target.value) })}
              >
                <option value={1}>1 attempt</option>
                <option value={2}>2 attempts</option>
                <option value={3}>3 attempts</option>
                <option value={5}>5 attempts</option>
                <option value={-1}>Unlimited</option>
              </select>
            </div>
          </div>
        </div>

        {/* Preview */}
        {assignment.class_id > 0 && selectedStory && (
          <div className="assignment-preview">
            <h3>4. Assignment Preview</h3>
            <div className="preview-content">
              <div className="preview-item">
                <strong>Class:</strong> {getSelectedClass()?.name} 
                ({getSelectedClass()?.student_count} students will receive this assignment)
              </div>
              <div className="preview-item">
                <strong>Story:</strong> {selectedStory.title}
              </div>
              <div className="preview-item">
                <strong>Title:</strong> {assignment.title}
              </div>
              {assignment.description && (
                <div className="preview-item">
                  <strong>Description:</strong> {assignment.description}
                </div>
              )}
              {assignment.due_date && (
                <div className="preview-item">
                  <strong>Due Date:</strong> {formatDate(assignment.due_date)}
                </div>
              )}
              <div className="preview-item">
                <strong>Max Attempts:</strong> {assignment.max_attempts === -1 ? 'Unlimited' : assignment.max_attempts}
              </div>
            </div>
          </div>
        )}

        {/* Submit */}
        <div className="form-actions">
          <button
            type="submit"
            disabled={loading || !assignment.class_id || !assignment.story_id || !assignment.title}
            className="create-assignment-button"
          >
            {loading ? 'Creating Assignment...' : 'Create Assignment'}
          </button>
        </div>
      </form>
    </div>
  );
};