import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from "./context/AuthContext";

export default function AdminLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const auth = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await auth?.login(email, password);
      // Redirect to the dashboard upon successful token generation
      navigate('/admin/dashboard'); 
    } catch (err: any) {
      setError(err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>System Access</h2>
        <p style={styles.subtitle}>Enter your credentials to manage the network.</p>
        
        <form onSubmit={handleLogin} style={styles.form}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Email Address</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
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

          <button 
            type="submit" 
            disabled={loading}
            style={{
              ...styles.button,
              backgroundColor: loading ? '#6b7280' : '#3b82f6',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Authenticating...' : 'Secure Login'}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  container: { 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    minHeight: '100vh', 
    backgroundColor: '#111827', 
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' 
  },
  card: { 
    backgroundColor: '#1f2937', 
    padding: '40px', 
    borderRadius: '12px', 
    width: '100%', 
    maxWidth: '380px', 
    boxShadow: '0 10px 25px rgba(0,0,0,0.5)' 
  },
  title: { 
    color: '#fff', 
    fontSize: '24px', 
    margin: '0 0 8px 0', 
    textAlign: 'center' 
  },
  subtitle: { 
    color: '#9ca3af', 
    fontSize: '14px', 
    margin: '0 0 24px 0', 
    textAlign: 'center' 
  },
  form: { 
    display: 'flex', 
    flexDirection: 'column', 
    gap: '20px' 
  },
  inputGroup: { 
    display: 'flex', 
    flexDirection: 'column', 
    gap: '6px' 
  },
  label: { 
    color: '#e5e7eb', 
    fontSize: '13px', 
    fontWeight: '600' 
  },
  input: { 
    padding: '12px', 
    borderRadius: '6px', 
    border: '1px solid #374151', 
    backgroundColor: '#374151', 
    color: '#fff', 
    fontSize: '15px', 
    outline: 'none' 
  },
  button: { 
    padding: '12px', 
    borderRadius: '6px', 
    border: 'none', 
    color: '#fff', 
    fontSize: '15px', 
    fontWeight: 'bold', 
    marginTop: '10px',
    transition: 'background-color 0.2s'
  },
  error: { 
    color: '#fca5a5', 
    fontSize: '13px', 
    textAlign: 'center', 
    backgroundColor: '#7f1d1d', 
    padding: '8px', 
    borderRadius: '6px' 
  }
};