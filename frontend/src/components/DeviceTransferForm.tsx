import React, { useState, useEffect } from 'react';


// Replace with your actual backend URL or use an environment variable
const API_BASE_URL = 'http://localhost:8000/api/v1';

export default function DeviceTransferForm() {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [transferPin, setTransferPin] = useState('');
  const [macAddress, setMacAddress] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<{ newPin: string } | null>(null);

  // 1. Extract the MAC address from the MikroTik URL parameters
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const mac = params.get('mac'); // MikroTik usually passes ?mac=XX:XX:XX:XX:XX:XX
    if (mac) setMacAddress(mac);
  }, []);

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (!macAddress) {
      setError("Cannot detect your device MAC address. Please reconnect to the Wi-Fi.");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/auth/transfer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          transfer_pin: transferPin,
          new_mac_address: macAddress,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Transfer failed. Please check your PIN.');
      }

      // Success! Store the new PIN to show the user
      setSuccessData({ newPin: data.new_transfer_pin });

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 2. Success Ui
  if (successData) {
    return (
      <div className="p-6 bg-green-50 rounded-lg border border-green-200 text-center">
        <h3 className="text-xl font-bold text-green-700 mb-2">Transfer Successful!</h3>
        <p className="text-gray-700 mb-4">
          Your old device has been disconnected. You can now log in on this device.
        </p>
        <div className="bg-white p-4 rounded shadow-sm inline-block mb-4">
          <p className="text-sm text-gray-500 uppercase tracking-wide">Your New Transfer PIN</p>
          <p className="text-2xl font-mono font-bold tracking-widest text-blue-600">
            {successData.newPin}
          </p>
        </div>
        <p className="text-sm text-gray-600">
          Save this new PIN in case you need to switch devices again.
        </p>
        
        {/* MikroTik hidden login form to auto-authenticate the new device */}
        <form action="$(link-login-only)" method="post" className="mt-4">
          <input type="hidden" name="username" value={phoneNumber} />
          <input type="hidden" name="password" value={phoneNumber} />
          <button 
            type="submit" 
            className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded hover:bg-blue-700"
          >
            Connect to Internet Now
          </button>
        </form>
      </div>
    );
  }

  // 3. Main Form UI
  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Transfer Wi-Fi Session</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleTransfer}>
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2">
            Phone Number
          </label>
          <input
            type="tel"
            required
            placeholder="07XX XXX XXX"
            className="w-full p-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
          />
        </div>

        <div className="mb-6">
          <label className="block text-gray-700 text-sm font-bold mb-2">
            6-Digit Transfer PIN
          </label>
          <input
            type="text"
            required
            maxLength={6}
            placeholder="e.g. A1B2C3"
            className="w-full p-3 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 uppercase font-mono tracking-widest"
            value={transferPin}
            onChange={(e) => setTransferPin(e.target.value.toUpperCase())}
          />
        </div>

        <button
          type="submit"
          disabled={loading || !macAddress}
          className={`w-full text-white font-bold py-3 px-4 rounded transition-colors ${
            loading || !macAddress ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {loading ? 'Verifying PIN...' : 'Transfer to this Device'}
        </button>
      </form>
    </div>
  );
}