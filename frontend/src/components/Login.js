import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';

const Login = () => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!credentials.username || !credentials.password) {
      toast.error('Please enter both username and password');
      return;
    }

    setLoading(true);
    const result = await login(credentials);
    
    if (!result.success) {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          {/* Adela Merchants Logo */}
          <div className="mx-auto mb-4">
            <img 
              src="/adela-logo.jpg" 
              alt="Adela Merchants Logo" 
              className="h-24 w-24 mx-auto rounded-xl object-cover"
            />
          </div>
          <h1 className="text-3xl font-bold text-yellow-400 mb-2">Adela Merchants</h1>
          <h2 className="text-xl text-gray-300 mb-2">Manufacturing Management</h2>
          <p className="text-sm text-gray-400">Adela Merchants</p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-1">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                className="misty-input w-full"
                placeholder="Enter your username"
                value={credentials.username}
                onChange={handleChange}
                disabled={loading}
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="misty-input w-full"
                placeholder="Enter your password"
                value={credentials.password}
                onChange={handleChange}
                disabled={loading}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full misty-button misty-button-primary py-3 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="login-submit-button"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-900 mr-2"></div>
                  Signing in...
                </div>
              ) : (
                'Sign in'
              )}
            </button>
          </div>

          <div className="text-center">
            <div className="text-sm text-gray-400 bg-gray-800 border border-gray-700 rounded-lg p-4">
              <p className="font-medium mb-2">Demo Credentials:</p>
              <p><strong>Username:</strong> Callum</p>
              <p><strong>Password:</strong> Peach7510</p>
            </div>
          </div>
        </form>

        <div className="text-center">
          <p className="text-xs text-gray-500">
            © 2024 Adela Merchants. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;