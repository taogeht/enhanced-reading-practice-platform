// Login form component

import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

export const LoginForm: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login({ username, password });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fillDemoAccount = (type: 'student' | 'teacher') => {
    if (type === 'student') {
      setUsername('student1');
      setPassword('password123');
    } else {
      setUsername('teacher1');
      setPassword('password123');
    }
  };

  return (
    <div className="login-container">
      <div className="login-form">
        <h1>Reading Practice Platform</h1>
        <p>Log in to access your reading assignments</p>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username:</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password:</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading} className="login-button">
            {loading ? 'Logging in...' : 'Log In'}
          </button>
        </form>

        <div className="demo-accounts">
          <h3>Demo Accounts</h3>
          <div className="demo-buttons">
            <button
              type="button"
              onClick={() => fillDemoAccount('student')}
              className="demo-button student"
            >
              Use Student Demo
            </button>
            <button
              type="button"
              onClick={() => fillDemoAccount('teacher')}
              className="demo-button teacher"
            >
              Use Teacher Demo
            </button>
          </div>
          <p className="demo-note">
            Click a demo button to auto-fill login credentials
          </p>
        </div>
      </div>
    </div>
  );
};