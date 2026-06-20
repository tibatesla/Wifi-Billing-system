import React, { useState, useEffect } from 'react';

interface InternetPlan {
  id: string;
  name: string;
  price: number;
  duration: string;
}

export default function App() {
  // Navigation State now includes 'success'
  const [view, setView] = useState<'plans' | 'payment' | 'success'>('plans');
  
  // Data State
  const [selectedPlan, setSelectedPlan] = useState<InternetPlan | null>(null);
  const [phoneNumber, setPhoneNumber] = useState<string>('');
  const [checkoutId, setCheckoutId] = useState<string | null>(null); // Tracks the active M-Pesa request
  
  // UI State
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  // Exact UUIDs matching your PostgreSQL database
  const plans: InternetPlan[] = [
    { id: 'a1111111-1111-1111-1111-111111111111', name: '1 Hour Quick', price: 10, duration: '1 Hour' },
    { id: 'a2222222-2222-2222-2222-222222222222', name: '4 Hours Pass', price: 20, duration: '4 Hours' },
    { id: 'a3333333-3333-3333-3333-333333333333', name: '24 Hours Daily', price: 40, duration: '24 Hours' },
    { id: 'a4444444-4444-4444-4444-444444444444', name: 'Weekly Pass', price: 200, duration: '7 Days' },
    { id: 'a5555555-5555-5555-5555-555555555555', name: 'Bi-Weekly', price: 300, duration: '14 Days' },
    { id: 'a6666666-6666-6666-6666-666666666666', name: 'Monthly Max', price: 650, duration: '30 Days' },
  ];

  // --- THE POLLING ENGINE ---
  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    // Only run the poll if we have a checkoutId and are actively on the payment screen
    if (checkoutId && view === 'payment') {
      intervalId = setInterval(async () => {
        try {
          // Ask FastAPI for the exact status of this specific transaction
          const res = await fetch(`http://localhost:8000/api/v1/mpesa/status/${checkoutId}`);
          
          if (res.ok) {
            const data = await res.json();
            
            if (data.status === 'COMPLETED') {
              setCheckoutId(null); // Stop polling
              setLoading(false);
              setView('success');  // Transition to the connected screen
            } else if (data.status === 'FAILED' || data.status === 'CANCELLED') {
              setCheckoutId(null); // Stop polling
              setLoading(false);
              setStatusMessage({ type: 'error', text: 'Payment failed or was cancelled. Please try again.' });
            }
            // If status is 'PENDING', the loop just quietly continues on the next tick
          }
        } catch (error) {
          console.error("Polling error: Lost connection to backend.", error);
        }
      }, 3000); // Ping the backend every 3 seconds
    }

    // Cleanup function: If the component unmounts or state changes, kill the timer immediately to prevent memory leaks.
    return () => clearInterval(intervalId);
  }, [checkoutId, view]);

  const handlePlanClick = (plan: InternetPlan) => {
    setSelectedPlan(plan);
    setStatusMessage(null);
    setView('payment');
  };

  const handleBackToPlans = () => {
    setView('plans');
    setStatusMessage(null);
    setCheckoutId(null); // Abort polling if they back out
  };

  const handlePayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPlan) return;

    let formattedPhone = phoneNumber.replace('+', '').trim();
    if (formattedPhone.startsWith('0')) {
      formattedPhone = '254' + formattedPhone.slice(1);
    }

    if (!formattedPhone.match(/^254(7|1)\d{8}$/)) {
      setStatusMessage({ type: 'error', text: 'Enter a valid Safaricom number starting with 07 or 01.' });
      return;
    }

    setLoading(true);
    setStatusMessage({ type: 'info', text: 'Sending M-Pesa STK Push... Check your phone.' });

    try {
      const response = await fetch('http://localhost:8000/api/v1/mpesa/stk-push', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone_number: formattedPhone,
          plan_id: selectedPlan.id,
          tenant_id: '11111111-1111-1111-1111-111111111111' 
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatusMessage({ type: 'success', text: 'STK Push sent! Please enter your M-Pesa PIN on your phone.' });
        // Start the polling engine by setting the ID returned from Safaricom
        setCheckoutId(data.checkout_id); 
      } else {
        let errorMessage = 'Failed to initiate payment. Please try again.';
        if (data.detail) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail)) {
            errorMessage = `Validation Error: ${data.detail[0].loc.join(' -> ')} - ${data.detail[0].msg}`;
          }
        }
        setStatusMessage({ type: 'error', text: errorMessage });
        setLoading(false);
      }
    } catch (error) {
      setStatusMessage({ type: 'error', text: 'Cannot connect to backend server. Ensure the backend is running.' });
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        
        {/* VIEW 1: PLANS */}
        {view === 'plans' && (
          <div>
            <div style={styles.header}>
              <h1 style={styles.title}>HIGH-SPEED WI-FI</h1>
              <p style={styles.subtitle}>Select a plan to get instant internet access.</p>
            </div>
            <div style={styles.planGrid}>
              {plans.map((plan) => (
                <div 
                  key={plan.id} 
                  onClick={() => handlePlanClick(plan)}
                  style={styles.planCard}
                >
                  <div style={styles.planName}>{plan.name}</div>
                  <div style={styles.planDuration}>{plan.duration}</div>
                  <div style={styles.planPrice}>KES {plan.price}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* VIEW 2: PAYMENT */}
        {view === 'payment' && selectedPlan && (
          <div>
            <button onClick={handleBackToPlans} style={styles.backButton} disabled={loading}>
              ← Back to Packages
            </button>
            
            <div style={styles.header}>
              <h1 style={styles.title}>Payment Checkout</h1>
            </div>

            <div style={styles.summaryCard}>
              <span style={styles.summaryTitle}>{selectedPlan.name}</span>
              <span style={styles.summaryPrice}>KES {selectedPlan.price}</span>
            </div>

            <form onSubmit={handlePayment} style={styles.form}>
              <div style={styles.inputGroup}>
                <label style={styles.label}>M-Pesa Phone Number</label>
                <input 
                  type="tel" 
                  placeholder="e.g., 0712345678 or 0112345678" 
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  disabled={loading}
                  style={styles.input}
                  required
                />
              </div>

              {statusMessage && (
                <div style={{
                  ...styles.alert,
                  backgroundColor: statusMessage.type === 'error' ? '#fde8e8' : statusMessage.type === 'success' ? '#def7ec' : '#e1effe',
                  color: statusMessage.type === 'error' ? '#9b1c1c' : statusMessage.type === 'success' ? '#03543f' : '#1e429f'
                }}>
                  {statusMessage.text}
                </div>
              )}

              <button 
                type="submit" 
                disabled={loading}
                style={{
                  ...styles.button,
                  backgroundColor: loading ? '#a0a0a0' : '#000',
                  cursor: loading ? 'not-allowed' : 'pointer'
                }}
              >
                {loading ? 'Waiting for Payment...' : 'Pay & Connect Now'}
              </button>
            </form>
          </div>
        )}

        {/* VIEW 3: SUCCESS (Auto-Connection) */}
        {view === 'success' && (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
            <h1 style={{ color: '#03543f', margin: '0 0 12px 0', fontSize: '24px', fontWeight: '800' }}>Payment Received!</h1>
            <p style={{ color: '#333', fontSize: '15px', lineHeight: '1.5', margin: '0 0 24px 0' }}>
              Your device has been authorized on the network. You are now securely connected to the internet.
            </p>
            <button 
              onClick={() => {
                setView('plans');
                setPhoneNumber('');
              }} 
              style={{...styles.button, width: '100%'}}
            >
              Return Home
            </button>
          </div>
        )}

        <div style={styles.footer}>
          Powered by Standalone Billing Engine
        </div>
      </div>
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  container: { display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', backgroundColor: '#f5f5f7', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', padding: '20px' },
  card: { backgroundColor: '#fff', borderRadius: '16px', boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)', width: '100%', maxWidth: '440px', padding: '32px 24px', boxSizing: 'border-box' },
  header: { textAlign: 'center', marginBottom: '28px' },
  title: { fontSize: '24px', fontWeight: '800', letterSpacing: '1px', margin: '0 0 8px 0', color: '#000' },
  subtitle: { fontSize: '14px', color: '#666', margin: 0, lineHeight: '1.4' },
  planGrid: { display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' },
  planCard: { border: '2px solid #e0e0e0', borderRadius: '12px', padding: '16px 8px', textAlign: 'center', cursor: 'pointer', transition: 'all 0.2s ease', backgroundColor: '#fff' },
  planName: { fontSize: '13px', fontWeight: '600', color: '#333', marginBottom: '4px' },
  planDuration: { fontSize: '11px', color: '#888', marginBottom: '8px' },
  planPrice: { fontSize: '15px', fontWeight: '800', color: '#000' },
  backButton: { background: 'none', border: 'none', color: '#1e429f', fontSize: '14px', fontWeight: '600', cursor: 'pointer', padding: 0, marginBottom: '20px' },
  summaryCard: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', backgroundColor: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb', marginBottom: '24px' },
  summaryTitle: { fontSize: '15px', fontWeight: '600', color: '#111' },
  summaryPrice: { fontSize: '16px', fontWeight: '800', color: '#1e429f' },
  form: { display: 'flex', flexDirection: 'column', gap: '20px' },
  inputGroup: { display: 'flex', flexDirection: 'column', gap: '6px' },
  label: { fontSize: '13px', fontWeight: '600', color: '#333' },
  input: { padding: '12px 16px', borderRadius: '8px', border: '1px solid #ccc', fontSize: '16px', outline: 'none', boxSizing: 'border-box', width: '100%' },
  button: { color: '#fff', border: 'none', borderRadius: '8px', padding: '14px', fontSize: '16px', fontWeight: '600', transition: 'background-color 0.2s ease', marginTop: '8px', width: '100%' },
  alert: { padding: '12px', borderRadius: '8px', fontSize: '13px', lineHeight: '1.4', textAlign: 'center' },
  footer: { textAlign: 'center', fontSize: '11px', color: '#aaa', marginTop: '32px' }
};