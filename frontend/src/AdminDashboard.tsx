import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from "./context/AuthContext";
import SettingsPanel from "./components/SettingsPanel";

// --- TypeScript Interfaces ---
interface DashboardStats {
  total_revenue_kes: number;
  total_sales: number;
  active_users: number;
}

interface Transaction {
  id: string;
  amount: number;
  status: 'COMPLETED' | 'PENDING' | 'FAILED';
  checkout_request_id: string;
}

export default function AdminDashboard() {
  const auth = useContext(AuthContext);
  const navigate = useNavigate();

  // --- Tab State ---
  const [activeTab, setActiveTab] = useState<'dashboard' | 'routers' | 'settings'>('dashboard');

  // --- Data State ---
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Protect the route: Kick them out if not authenticated
  useEffect(() => {
    if (!auth?.isAuthenticated) {
      navigate('/admin/login');
    }
  }, [auth?.isAuthenticated, navigate]);

// --- Data Fetching ---
  useEffect(() => {
    if (!auth?.token) return;

    const fetchAdminData = async () => {
      try {
        const fetchOptions = {
          headers: {
            'Authorization': `Bearer ${auth.token}`, 
            'Content-Type': 'application/json'
          }
        };

        // Notice the URLs no longer need the tenant ID!
        const [statsRes, txRes] = await Promise.all([
          fetch(`http://localhost:8000/api/v1/admin/dashboard/stats`, fetchOptions),
          fetch(`http://localhost:8000/api/v1/admin/transactions`, fetchOptions)
        ]);

        if (statsRes.status === 401 || txRes.status === 401) {
           auth.logout(); 
           return;
        }

        if (!statsRes.ok || !txRes.ok) throw new Error('Failed to fetch dashboard data');

        const statsData = await statsRes.json();
        const txData = await txRes.json();

        setStats(statsData);
        setTransactions(Array.isArray(txData.transactions) ? txData.transactions : []);
      } catch (err) {
        setError('Could not connect to the admin API. Ensure FastAPI is running.');
      } finally {
        setLoading(false);
      }
    };

    fetchAdminData();
    const interval = setInterval(fetchAdminData, 30000);
    return () => clearInterval(interval);
  }, [auth?.token]); // Removed auth.user dependency
  // Prevent rendering the dashboard until auth state is confirmed
  if (!auth?.isAuthenticated) return null;

  if (loading) return <div style={styles.center}>Loading Command Center...</div>;
  if (error) return <div style={{...styles.center, color: 'red'}}>{error}</div>;


  return (
    <div style={styles.container}>
      {/* --- SIDEBAR NAVIGATION --- */}
      <div style={styles.sidebar}>
        <h2 style={styles.brand}>Wi-Fi Manager</h2>
        
        {/* Added Logged in User info */}
        <div style={styles.userInfo}>
           <span style={{ fontSize: '11px', color: '#6b7280', textTransform: 'uppercase' }}>Logged in as</span>
           <br/>
           <span style={{ fontSize: '13px', color: '#e5e7eb', wordBreak: 'break-all' }}>{auth.user?.email}</span>
        </div>

        <ul style={styles.nav}>
          <li 
            style={activeTab === 'dashboard' ? styles.navItemActive : styles.navItem}
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </li>
          <li 
            style={activeTab === 'routers' ? styles.navItemActive : styles.navItem}
            onClick={() => setActiveTab('routers')}
          >
            Routers
          </li>
          <li 
            style={activeTab === 'settings' ? styles.navItemActive : styles.navItem}
            onClick={() => setActiveTab('settings')}
          >
            Settings
          </li>
        </ul>
        <div style={{ marginTop: 'auto' }}>
          <button onClick={() => auth.logout()} style={styles.logoutBtn}>Log Out</button>
        </div>
      </div>

      {/* --- MAIN CONTENT AREA --- */}
      <div style={styles.main}>
        <div style={styles.header}>
          <h1 style={styles.title}>
            {activeTab === 'dashboard' && 'Overview'}
            {activeTab === 'routers' && 'Router Management'}
            {activeTab === 'settings' && 'System Settings'}
          </h1>
          {activeTab === 'dashboard' && (
            <button style={styles.refreshBtn} onClick={() => window.location.reload()}>
              ↻ Refresh
            </button>
          )}
        </div>

        {/* --- VIEW: DASHBOARD --- */}
        {activeTab === 'dashboard' && (
          <>
            <div style={styles.statsGrid}>
              <div style={styles.card}>
                <div style={styles.cardTitle}>Total Revenue</div>
                <div style={styles.cardValue}>KES {stats?.total_revenue_kes?.toLocaleString() || 0}</div>
              </div>
              <div style={styles.card}>
                <div style={styles.cardTitle}>Successful Sales</div>
                <div style={styles.cardValue}>{stats?.total_sales || 0}</div>
              </div>
              <div style={styles.card}>
                <div style={styles.cardTitle}>Active Connections</div>
                <div style={styles.cardValue}>{stats?.active_users || 0}</div>
              </div>
            </div>

            <div style={{...styles.card, marginTop: '24px'}}>
              <h2 style={{ fontSize: '18px', margin: '0 0 16px 0' }}>Recent Transactions</h2>
              <div style={styles.tableWrapper}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Checkout ID</th>
                      <th style={styles.th}>Amount</th>
                      <th style={styles.th}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {transactions.map((tx) => (
                      <tr key={tx.id} style={styles.tr}>
                        <td style={styles.td}>
                          <span style={styles.code}>{tx.checkout_request_id.replace('ws_CO_', '...')}</span>
                        </td>
                        <td style={{...styles.td, fontWeight: '600'}}>KES {tx.amount}</td>
                        <td style={styles.td}>
                          <span style={{
                            ...styles.badge,
                            backgroundColor: tx.status === 'COMPLETED' ? '#def7ec' : tx.status === 'FAILED' ? '#fde8e8' : '#fef3c7',
                            color: tx.status === 'COMPLETED' ? '#03543f' : tx.status === 'FAILED' ? '#9b1c1c' : '#92400e'
                          }}>
                            {tx.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                    {transactions.length === 0 && (
                      <tr><td colSpan={3} style={{textAlign: 'center', padding: '20px', color: '#888'}}>No transactions yet.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* --- VIEW: ROUTERS --- */}
        {activeTab === 'routers' && (
          <div style={styles.card}>
            <h2 style={{ fontSize: '18px', margin: '0 0 16px 0' }}>MikroTik Integrations</h2>
            <p style={{ color: '#6b7280', fontSize: '14px', lineHeight: '1.5' }}>
              This panel will manage your active MikroTik routers. You will be able to see CPU usage, active Hotspot users, and manually authorize or kick MAC addresses from here.
            </p>
            <button style={{...styles.refreshBtn, marginTop: '16px', backgroundColor: '#111827', color: '#fff'}}>
              + Add New Router
            </button>
          </div>
        )}

        {/* --- VIEW: SETTINGS --- */}
        {activeTab === 'settings' && (
           <SettingsPanel />
        )}

        {/* --- VIEW: SETTINGS --- */}
        {activeTab === 'settings' && (
          <div style={styles.card}>
            <h2 style={{ fontSize: '18px', margin: '0 0 16px 0' }}>Tenant Configuration</h2>
            <p style={{ color: '#6b7280', fontSize: '14px', lineHeight: '1.5' }}>
              Configure your Daraja API keys, update internet package pricing, and manage your admin credentials here.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}


// --- Styles ---
const styles: { [key: string]: React.CSSProperties } = {
  center: { display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontFamily: 'sans-serif' },
  container: { display: 'flex', minHeight: '100vh', backgroundColor: '#f3f4f6', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
  sidebar: { width: '250px', backgroundColor: '#111827', color: '#fff', padding: '24px', display: 'flex', flexDirection: 'column' },
  brand: { fontSize: '20px', fontWeight: '800', letterSpacing: '1px', marginBottom: '24px', color: '#fff' },
  userInfo: { marginBottom: '32px', paddingBottom: '16px', borderBottom: '1px solid #374151' },
  nav: { listStyle: 'none', padding: 0, margin: 0 },
  navItem: { padding: '12px 16px', borderRadius: '8px', marginBottom: '8px', cursor: 'pointer', color: '#9ca3af', transition: 'all 0.2s' },
  navItemActive: { padding: '12px 16px', borderRadius: '8px', marginBottom: '8px', cursor: 'pointer', backgroundColor: '#1f2937', color: '#fff', fontWeight: '600' },
  logoutBtn: { width: '100%', padding: '12px', backgroundColor: '#7f1d1d', color: '#fca5a5', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' },
  main: { flex: 1, padding: '40px', overflowY: 'auto' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' },
  title: { fontSize: '28px', fontWeight: '700', color: '#111827', margin: 0 },
  refreshBtn: { padding: '8px 16px', backgroundColor: '#fff', border: '1px solid #d1d5db', borderRadius: '6px', cursor: 'pointer', fontWeight: '600', color: '#374151' },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px' },
  card: { backgroundColor: '#fff', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' },
  cardTitle: { fontSize: '14px', color: '#6b7280', fontWeight: '600', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' },
  cardValue: { fontSize: '32px', fontWeight: '800', color: '#111827' },
  tableWrapper: { overflowX: 'auto' },
  table: { width: '100%', borderCollapse: 'collapse', textAlign: 'left' },
  th: { padding: '12px 16px', borderBottom: '1px solid #e5e7eb', color: '#6b7280', fontSize: '12px', textTransform: 'uppercase', fontWeight: '600' },
  tr: { borderBottom: '1px solid #f3f4f6' },
  td: { padding: '16px', fontSize: '14px', color: '#374151', verticalAlign: 'middle' },
  code: { fontFamily: 'monospace', backgroundColor: '#f3f4f6', padding: '4px 8px', borderRadius: '4px', fontSize: '13px' },
  badge: { padding: '4px 10px', borderRadius: '9999px', fontSize: '12px', fontWeight: '700', display: 'inline-block' }
};