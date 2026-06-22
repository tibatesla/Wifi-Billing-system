import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

export default function SettingsPanel() {
  const auth = useContext(AuthContext);
  const tenantId = auth?.user?.tenant_id;

  // UI State
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<{type: 'success' | 'error', msg: string} | null>(null);

  // Form States
  const [mpesa, setMpesa] = useState({ shortcode: '', consumer_key: '', consumer_secret: '' });
  const [router, setRouter] = useState({ name: 'Main HQ', ip_address: '', api_username: 'admin', api_password: '', api_port: 8728 });
  const [plan, setPlan] = useState({ name: '', price: '', speed_limit: '10M/10M', validity_hours: '1', mikrotik_profile_name: 'default' });

  const showNotification = (type: 'success' | 'error', msg: string) => {
    setNotification({ type, msg });
    setTimeout(() => setNotification(null), 5000);
  };

  const handleMpesaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/settings/tenant/${tenantId}/mpesa`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${auth?.token}` },
        body: JSON.stringify(mpesa)
      });
      if (!res.ok) throw new Error("Failed to update M-Pesa Keys");
      showNotification('success', 'M-Pesa Daraja Keys updated securely.');
      setMpesa({ shortcode: '', consumer_key: '', consumer_secret: '' }); // Clear form
    } catch (err: any) {
      showNotification('error', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRouterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/settings/router`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${auth?.token}` },
        body: JSON.stringify(router)
      });
      if (!res.ok) throw new Error("Failed to add Router");
      showNotification('success', 'MikroTik Router connected to system.');
      setRouter({ ...router, ip_address: '', api_password: '' });
    } catch (err: any) {
      showNotification('error', err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePlanSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/settings/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${auth?.token}` },
        body: JSON.stringify({
            ...plan,
            price: parseFloat(plan.price),
            validity_hours: parseInt(plan.validity_hours)
        })
      });
      if (!res.ok) throw new Error("Failed to add Plan");
      showNotification('success', 'New Internet Plan created.');
      setPlan({ name: '', price: '', speed_limit: '10M/10M', validity_hours: '1', mikrotik_profile_name: 'default' });
    } catch (err: any) {
      showNotification('error', err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {notification && (
        <div style={{...styles.alert, backgroundColor: notification.type === 'success' ? '#def7ec' : '#fde8e8', color: notification.type === 'success' ? '#03543f' : '#9b1c1c'}}>
          {notification.msg}
        </div>
      )}

      <div style={styles.grid}>
        
        {/* --- M-PESA DARAJA KEYS --- */}
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>M-Pesa Daraja Configuration</h2>
          <p style={styles.cardDesc}>Link your Safaricom Paybill or Till Number.</p>
          <form onSubmit={handleMpesaSubmit} style={styles.form}>
            <input style={styles.input} placeholder="Shortcode (e.g. 174379)" value={mpesa.shortcode} onChange={e => setMpesa({...mpesa, shortcode: e.target.value})} required />
            <input style={styles.input} placeholder="Consumer Key" value={mpesa.consumer_key} onChange={e => setMpesa({...mpesa, consumer_key: e.target.value})} required />
            <input style={styles.input} type="password" placeholder="Consumer Secret" value={mpesa.consumer_secret} onChange={e => setMpesa({...mpesa, consumer_secret: e.target.value})} required />
            <button disabled={loading} style={styles.button}>Save API Keys</button>
          </form>
        </div>

        {/* --- MIKROTIK ROUTER --- */}
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Add MikroTik Router</h2>
          <p style={styles.cardDesc}>Connect a physical router to the billing engine.</p>
          <form onSubmit={handleRouterSubmit} style={styles.form}>
            <input style={styles.input} placeholder="Router Nickname (e.g. CBD Tower 1)" value={router.name} onChange={e => setRouter({...router, name: e.target.value})} required />
            <input style={styles.input} placeholder="Public IP Address (e.g. 197.xx.xx.xx)" value={router.ip_address} onChange={e => setRouter({...router, ip_address: e.target.value})} required />
            <div style={{display: 'flex', gap: '10px'}}>
              <input style={styles.input} placeholder="API Username" value={router.api_username} onChange={e => setRouter({...router, api_username: e.target.value})} required />
              <input style={styles.input} type="password" placeholder="API Password" value={router.api_password} onChange={e => setRouter({...router, api_password: e.target.value})} required />
            </div>
            <button disabled={loading} style={styles.button}>Register Router</button>
          </form>
        </div>

        {/* --- INTERNET PLANS --- */}
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>Create Internet Plan</h2>
          <p style={styles.cardDesc}>Add a new package to the Captive Portal.</p>
          <form onSubmit={handlePlanSubmit} style={styles.form}>
            <div style={{display: 'flex', gap: '10px'}}>
              <input style={styles.input} placeholder="Plan Name (e.g. 1 Hour Quick)" value={plan.name} onChange={e => setPlan({...plan, name: e.target.value})} required />
              <input style={styles.input} type="number" placeholder="Price (KES)" value={plan.price} onChange={e => setPlan({...plan, price: e.target.value})} required />
            </div>
            <div style={{display: 'flex', gap: '10px'}}>
              <input style={styles.input} type="number" placeholder="Validity (Hours)" value={plan.validity_hours} onChange={e => setPlan({...plan, validity_hours: e.target.value})} required />
              <input style={styles.input} placeholder="Speed Limit (e.g. 5M/5M)" value={plan.speed_limit} onChange={e => setPlan({...plan, speed_limit: e.target.value})} required />
            </div>
            <input style={styles.input} placeholder="MikroTik Profile Name (Must match exactly)" value={plan.mikrotik_profile_name} onChange={e => setPlan({...plan, mikrotik_profile_name: e.target.value})} required />
            <button disabled={loading} style={styles.button}>Publish Plan</button>
          </form>
        </div>

      </div>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  container: { width: '100%', maxWidth: '1000px', margin: '0 auto' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' },
  card: { backgroundColor: '#fff', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', border: '1px solid #e5e7eb' },
  cardTitle: { fontSize: '18px', fontWeight: '700', color: '#111827', margin: '0 0 8px 0' },
  cardDesc: { fontSize: '13px', color: '#6b7280', margin: '0 0 20px 0', lineHeight: '1.4' },
  form: { display: 'flex', flexDirection: 'column', gap: '12px' },
  input: { padding: '10px 12px', borderRadius: '6px', border: '1px solid #d1d5db', fontSize: '14px', width: '100%', boxSizing: 'border-box' },
  button: { padding: '12px', backgroundColor: '#111827', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: '600', fontSize: '14px', marginTop: '8px' },
  alert: { padding: '12px', borderRadius: '8px', fontSize: '14px', fontWeight: '500', marginBottom: '24px', textAlign: 'center' }
};