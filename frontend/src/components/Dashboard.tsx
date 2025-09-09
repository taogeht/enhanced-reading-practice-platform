// Main dashboard component that routes between login and app content

import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { LoginForm } from './LoginForm';
import { StudentDashboard } from './StudentDashboard';
import { TeacherDashboard } from './TeacherDashboard';

export const Dashboard: React.FC = () => {
  const { user, loading, isStudent, isTeacher } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <h2>Loading...</h2>
      </div>
    );
  }

  if (!user) {
    return <LoginForm />;
  }

  if (isStudent) {
    return <StudentDashboard />;
  }

  if (isTeacher) {
    return <TeacherDashboard />;
  }

  return (
    <div className="dashboard">
      <h1>Welcome to Reading Platform</h1>
      <p>User type not recognized: {user.user_type}</p>
    </div>
  );
};