import React, { useContext } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Import the Context Provider
import { AuthContext, AuthProvider } from './context/AuthContext';

// Import your Views
import CaptivePortal from './CaptivePortal';
import AdminDashboard from './AdminDashboard';
import AdminLogin from './AdminLogin'; 

// Upgraded ProtectedRoute: Checks the JWT Context instead of local sessionStorage
const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const auth = useContext(AuthContext);
  
  if (!auth?.isAuthenticated) {
    // If they don't have a valid JWT token, kick them back to the login page
    return <Navigate to="/admin/login" replace />;
  }
  
  return children;
};

export default function App() {
  return (
    /* The AuthProvider MUST wrap everything so the token survives page changes */
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* PUBLIC ROUTE: The Captive Portal for customers */}
          <Route path="/" element={<CaptivePortal />} />

          {/* PUBLIC ROUTE: The Admin Login Screen */}
          <Route path="/admin/login" element={<AdminLogin />} />

          {/* SECURE ROUTE: The actual dashboard, wrapped in our JWT protection */}
          {/* Notice the path is now /admin/dashboard to match our login redirect */}
          <Route 
            path="/admin/dashboard" 
            element={
              <ProtectedRoute>
                <AdminDashboard />
              </ProtectedRoute>
            } 
          />
          
          {/* Fallback route: Prevents 404 errors by redirecting unknown URLs to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}