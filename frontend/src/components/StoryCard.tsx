// Story card component for displaying story information

import React, { useState } from 'react';
import { StoryListItem, Story } from '../types';
import { storiesAPI } from '../services/api';
import { StoryReader } from './StoryReader';

interface StoryCardProps {
  story: StoryListItem;
}

export const StoryCard: React.FC<StoryCardProps> = ({ story }) => {
  const [showReader, setShowReader] = useState(false);
  const [fullStory, setFullStory] = useState<Story | null>(null);
  const [loading, setLoading] = useState(false);

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return '#4CAF50';
      case 'medium': return '#FF9800';
      case 'hard': return '#F44336';
      default: return '#2196F3';
    }
  };

  const handleReadStory = async () => {
    try {
      setLoading(true);
      const storyData = await storiesAPI.getStory(story.id);
      setFullStory(storyData);
      setShowReader(true);
    } catch (error) {
      console.error('Failed to load story:', error);
    } finally {
      setLoading(false);
    }
  };

  if (showReader && fullStory) {
    return (
      <StoryReader 
        story={fullStory} 
        onClose={() => {
          setShowReader(false);
          setFullStory(null);
        }} 
      />
    );
  }

  return (
    <div className="story-card">
      <div className="story-header">
        <h3 className="story-title">{story.title}</h3>
        <div 
          className="difficulty-badge"
          style={{ backgroundColor: getDifficultyColor(story.difficulty) }}
        >
          {story.difficulty}
        </div>
      </div>
      
      <div className="story-details">
        <div className="detail-item">
          <span className="label">Grade Level:</span>
          <span className="value">{story.grade_level}</span>
        </div>
        <div className="detail-item">
          <span className="label">Words:</span>
          <span className="value">{story.word_count}</span>
        </div>
        <div className="detail-item">
          <span className="label">Reading Time:</span>
          <span className="value">{story.estimated_reading_time}s</span>
        </div>
        <div className="detail-item">
          <span className="label">Audio Options:</span>
          <span className="value">{story.audio_count} voices</span>
        </div>
      </div>

      <div className="story-actions">
        <button 
          className="read-button"
          onClick={handleReadStory}
          disabled={loading}
        >
          {loading ? 'Loading...' : 'Read Story'}
        </button>
      </div>
    </div>
  );
};