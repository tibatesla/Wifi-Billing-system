import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import CaptivePortal from './CaptivePortal';
import AdminDashboard from './AdminDashboard';
import AdminLogin from './AdminLogin'; // Import the new login screen

//component checks the session before rendering the dashboard
const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const isAuthenticated = sessionStorage.getItem('isAdmin') === 'true';
  
  if (!isAuthenticated) {
    // If they aren't logged in, kick them back to the login page
    return <Navigate to="/admin/login" replace />;
  }
  
  return children;
};

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* PUBLIC ROUTE: The Captive Portal for customers */}
        <Route path="/" element={<CaptivePortal />} />

        {/* PUBLIC ROUTE: The Admin Login Screen */}
        <Route path="/admin/login" element={<AdminLogin />} />

        {/* SECURE ROUTE: The actual dashboard, wrapped in our protection logic */}
        <Route 
          path="/admin" 
          element={
            <ProtectedRoute>
              <AdminDashboard />
            </ProtectedRoute>
          } 
        />
        
        {/* Fallback route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}