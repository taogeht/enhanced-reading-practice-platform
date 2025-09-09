// Story reader component with audio playback and recording functionality

import React, { useState, useRef, useEffect } from 'react';
import { Story, StudentAssignment } from '../types';
import { storiesAPI, recordingsAPI } from '../services/api';
import { AudioRecorder } from './AudioRecorder';

interface StoryReaderProps {
  story: Story;
  assignment?: StudentAssignment;
  onClose: () => void;
}

export const StoryReader: React.FC<StoryReaderProps> = ({ story, assignment, onClose }) => {
  const [selectedVoice, setSelectedVoice] = useState<string>(story.audio_files[0]?.voice_type || 'female_1');
  const [isPlaying, setIsPlaying] = useState(false);
  const [showRecording, setShowRecording] = useState(false);
  const [audioError, setAudioError] = useState('');
  const audioRef = useRef<HTMLAudioElement>(null);

  const voiceOptions = [
    { value: 'female_1', label: 'Female Voice 1' },
    { value: 'female_2', label: 'Female Voice 2' },
    { value: 'male_1', label: 'Male Voice 1' },
    { value: 'male_2', label: 'Male Voice 2' },
  ];

  const availableVoices = voiceOptions.filter(voice => 
    story.audio_files.some(audio => audio.voice_type === voice.value)
  );

  const currentAudioFile = story.audio_files.find(audio => audio.voice_type === selectedVoice);
  const audioUrl = currentAudioFile ? storiesAPI.getAudioUrl(story.id, selectedVoice) : '';

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.load();
    }
  }, [selectedVoice]);

  const handlePlay = () => {
    if (audioRef.current) {
      setAudioError('');
      audioRef.current.play()
        .then(() => setIsPlaying(true))
        .catch((error) => {
          console.error('Audio play error:', error);
          setAudioError('Unable to play audio. The audio file may not be available.');
        });
    }
  };

  const handlePause = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
    }
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
  };

  const handleAudioError = () => {
    setAudioError('Audio file could not be loaded. This may be because the audio files have not been generated yet.');
    setIsPlaying(false);
  };

  const handleStartRecording = () => {
    setShowRecording(true);
  };

  const handleRecordingComplete = async (audioBlob: Blob) => {
    if (assignment) {
      try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.wav');
        formData.append('story', story.id.toString());
        formData.append('assignment', assignment.id.toString());
        formData.append('duration', '60'); // Placeholder duration
        formData.append('file_size', audioBlob.size.toString());

        await recordingsAPI.uploadRecording(formData);
        alert('Recording uploaded successfully!');
      } catch (error) {
        console.error('Failed to upload recording:', error);
        alert('Failed to upload recording. Please try again.');
      }
    }
    setShowRecording(false);
  };

  if (showRecording) {
    return (
      <AudioRecorder
        story={story}
        onComplete={handleRecordingComplete}
        onCancel={() => setShowRecording(false)}
      />
    );
  }

  return (
    <div className="story-reader">
      <div className="reader-header">
        <button className="close-button" onClick={onClose}>
          ← Back
        </button>
        <h1 className="story-title">{story.title}</h1>
        {assignment && (
          <div className="assignment-info">
            Assignment: {assignment.assignment_title}
          </div>
        )}
      </div>

      <div className="reader-content">
        <div className="audio-controls">
          <div className="voice-selector">
            <label htmlFor="voice-select">Choose voice:</label>
            <select 
              id="voice-select"
              value={selectedVoice} 
              onChange={(e) => setSelectedVoice(e.target.value)}
            >
              {availableVoices.map((voice) => (
                <option key={voice.value} value={voice.value}>
                  {voice.label}
                </option>
              ))}
            </select>
          </div>

          <div className="playback-controls">
            {!isPlaying ? (
              <button className="play-button" onClick={handlePlay}>
                ▶ Listen to Story
              </button>
            ) : (
              <button className="pause-button" onClick={handlePause}>
                ⏸ Pause
              </button>
            )}
          </div>

          {audioError && (
            <div className="audio-error">
              {audioError}
            </div>
          )}

          <audio
            ref={audioRef}
            onEnded={handleAudioEnded}
            onError={handleAudioError}
            style={{ display: 'none' }}
          >
            <source src={audioUrl} type="audio/mpeg" />
            Your browser does not support the audio element.
          </audio>
        </div>

        <div className="story-text">
          <p>{story.content}</p>
        </div>

        <div className="recording-section">
          <h3>Now it's your turn!</h3>
          <p>Practice reading the story aloud. Click the button below to start recording:</p>
          
          <button 
            className="record-button"
            onClick={handleStartRecording}
            disabled={assignment && !assignment.can_attempt}
          >
            🎤 Start Recording
          </button>
          
          {assignment && !assignment.can_attempt && (
            <p className="attempts-warning">
              You have used all your attempts for this assignment.
            </p>
          )}
        </div>

        <div className="story-info">
          <div className="info-grid">
            <div className="info-item">
              <strong>Grade Level:</strong> {story.grade_level}
            </div>
            <div className="info-item">
              <strong>Difficulty:</strong> {story.difficulty}
            </div>
            <div className="info-item">
              <strong>Word Count:</strong> {story.word_count}
            </div>
            <div className="info-item">
              <strong>Estimated Time:</strong> {story.estimated_reading_time} seconds
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};