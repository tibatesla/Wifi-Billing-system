import React, { useEffect, useState } from 'react';

interface Transaction {
  id: string;
  phone_number: string;
  amount: number;
  status: string;
  created_at: string;
}

export default function Admin() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // In production, this endpoint would require JWT authentication
    const fetchTransactions = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/transactions/');
        if (response.ok) {
          const data = await response.json();
          setTransactions(data);
        }
      } catch (error) {
        console.error("Failed to fetch transactions:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, []);

  return (
    <div style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
        <h1 style={{ margin: 0, color: '#111' }}>Dashboard Overview</h1>
        <div style={{ backgroundColor: '#e1effe', color: '#1e429f', padding: '8px 16px', borderRadius: '20px', fontWeight: 'bold' }}>
          System Status: ONLINE
        </div>
      </div>

      <div style={{ backgroundColor: '#fff', padding: '24px', borderRadius: '12px', boxShadow: '0 2px 10px rgba(0,0,0,0.05)' }}>
        <h2 style={{ fontSize: '18px', marginTop: 0, marginBottom: '20px', color: '#333' }}>Recent M-Pesa Transactions</h2>
        
        {loading ? (
          <p>Loading data...</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #eee', color: '#666' }}>
                <th style={{ padding: '12px 8px' }}>Date</th>
                <th style={{ padding: '12px 8px' }}>Phone Number</th>
                <th style={{ padding: '12px 8px' }}>Amount (KES)</th>
                <th style={{ padding: '12px 8px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {transactions.length === 0 ? (
                <tr>
                  <td colSpan={4} style={{ padding: '20px', textAlign: 'center', color: '#999' }}>No transactions found.</td>
                </tr>
              ) : (
                transactions.map((tx) => (
                  <tr key={tx.id} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '12px 8px' }}>{new Date(tx.created_at).toLocaleString()}</td>
                    <td style={{ padding: '12px 8px' }}>{tx.phone_number}</td>
                    <td style={{ padding: '12px 8px', fontWeight: 'bold' }}>{tx.amount}</td>
                    <td style={{ padding: '12px 8px' }}>
                      <span style={{ 
                        backgroundColor: tx.status === 'COMPLETED' ? '#def7ec' : '#fde8e8',
                        color: tx.status === 'COMPLETED' ? '#03543f' : '#9b1c1c',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 'bold'
                      }}>
                        {tx.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}