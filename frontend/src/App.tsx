import React from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { Dashboard } from './components/Dashboard';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <Dashboard />
      </div>
    </AuthProvider>
  );
}

export default App;
