import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function AdminLogin() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Hardcoded credentials for testing (Change these later!)
    if (username === 'tesla' && password === 'admin123') {
      sessionStorage.setItem('isAdmin', 'true'); // Create the secure session
      navigate('/admin'); // Redirect to the dashboard
    } else {
      setError('Invalid username or password.');
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>System Access</h2>
        <p style={styles.subtitle}>Enter your credentials to manage the network.</p>
        
        <form onSubmit={handleLogin} style={styles.form}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Username</label>
            <input 
              type="text" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={styles.input}
              required
              autoComplete="off"
            />
          </div>
          
          <div style={styles.inputGroup}>
            <label style={styles.label}>Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
              required
            />
          </div>

          {error && <div style={styles.error}>{error}</div>}

          <button type="submit" style={styles.button}>Secure Login</button>
        </form>
      </div>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  container: { display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', backgroundColor: '#111827', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
  card: { backgroundColor: '#1f2937', padding: '40px', borderRadius: '12px', width: '100%', maxWidth: '380px', boxShadow: '0 10px 25px rgba(0,0,0,0.5)' },
  title: { color: '#fff', fontSize: '24px', margin: '0 0 8px 0', textAlign: 'center' },
  subtitle: { color: '#9ca3af', fontSize: '14px', margin: '0 0 24px 0', textAlign: 'center' },
  form: { display: 'flex', flexDirection: 'column', gap: '20px' },
  inputGroup: { display: 'flex', flexDirection: 'column', gap: '6px' },
  label: { color: '#e5e7eb', fontSize: '13px', fontWeight: '600' },
  input: { padding: '12px', borderRadius: '6px', border: '1px solid #374151', backgroundColor: '#374151', color: '#fff', fontSize: '15px', outline: 'none' },
  button: { padding: '12px', borderRadius: '6px', border: 'none', backgroundColor: '#3b82f6', color: '#fff', fontSize: '15px', fontWeight: 'bold', cursor: 'pointer', marginTop: '10px' },
  error: { color: '#fca5a5', fontSize: '13px', textAlign: 'center', backgroundColor: '#7f1d1d', padding: '8px', borderRadius: '6px' }
};