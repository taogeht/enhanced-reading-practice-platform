// Audio recorder component for student recordings

import React, { useState, useRef, useEffect } from 'react';
import { Story } from '../types';

interface AudioRecorderProps {
  story: Story;
  onComplete: (audioBlob: Blob) => void;
  onCancel: () => void;
}

export const AudioRecorder: React.FC<AudioRecorderProps> = ({ story, onComplete, onCancel }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [hasRecording, setHasRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState('');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioUrlRef = useRef<string>('');
  const audioElementRef = useRef<HTMLAudioElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      setError('');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' });
        audioUrlRef.current = URL.createObjectURL(audioBlob);
        setHasRecording(true);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (err) {
      console.error('Error starting recording:', err);
      setError('Unable to access microphone. Please check your browser permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const playRecording = () => {
    if (audioElementRef.current && audioUrlRef.current) {
      audioElementRef.current.play();
      setIsPlaying(true);
    }
  };

  const pauseRecording = () => {
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      setIsPlaying(false);
    }
  };

  const handleAudioEnded = () => {
    setIsPlaying(false);
  };

  const handleSubmit = () => {
    if (audioChunksRef.current.length > 0) {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' });
      onComplete(audioBlob);
    }
  };

  const handleRetry = () => {
    setHasRecording(false);
    setRecordingTime(0);
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = '';
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="audio-recorder">
      <div className="recorder-header">
        <button className="back-button" onClick={onCancel}>
          ← Back to Story
        </button>
        <h2>Record Reading: {story.title}</h2>
      </div>

      <div className="recorder-content">
        <div className="story-preview">
          <h3>Read this story aloud:</h3>
          <div className="story-text">
            <p>{story.content}</p>
          </div>
        </div>

        <div className="recording-controls">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {!hasRecording ? (
            <div className="record-section">
              <div className="record-status">
                {isRecording ? (
                  <>
                    <div className="recording-indicator">
                      🔴 Recording...
                    </div>
                    <div className="recording-timer">
                      {formatTime(recordingTime)}
                    </div>
                  </>
                ) : (
                  <div className="ready-to-record">
                    Click the button below to start recording
                  </div>
                )}
              </div>

              <div className="record-buttons">
                {!isRecording ? (
                  <button 
                    className="start-record-button" 
                    onClick={startRecording}
                  >
                    🎤 Start Recording
                  </button>
                ) : (
                  <button 
                    className="stop-record-button" 
                    onClick={stopRecording}
                  >
                    ⏹ Stop Recording
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="review-section">
              <div className="recording-complete">
                ✅ Recording Complete! ({formatTime(recordingTime)})
              </div>

              <div className="playback-controls">
                <audio
                  ref={audioElementRef}
                  src={audioUrlRef.current}
                  onEnded={handleAudioEnded}
                  style={{ display: 'none' }}
                />

                {!isPlaying ? (
                  <button 
                    className="play-recording-button" 
                    onClick={playRecording}
                  >
                    ▶ Play Recording
                  </button>
                ) : (
                  <button 
                    className="pause-recording-button" 
                    onClick={pauseRecording}
                  >
                    ⏸ Pause
                  </button>
                )}
              </div>

              <div className="submit-controls">
                <button 
                  className="retry-button" 
                  onClick={handleRetry}
                >
                  🔄 Record Again
                </button>
                <button 
                  className="submit-button" 
                  onClick={handleSubmit}
                >
                  ✅ Submit Recording
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="recording-tips">
          <h4>Recording Tips:</h4>
          <ul>
            <li>Find a quiet place to record</li>
            <li>Speak clearly and at a comfortable pace</li>
            <li>You can record again if you're not happy with your first attempt</li>
            <li>Make sure your browser has microphone permissions</li>
          </ul>
        </div>
      </div>
    </div>
  );
};