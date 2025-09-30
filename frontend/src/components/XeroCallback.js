import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';

const XeroCallback = () => {
  const [status, setStatus] = useState('processing');
  const location = useLocation();

  useEffect(() => {
    handleXeroCallback();
  }, [location]);

  const handleXeroCallback = async () => {
    try {
      const urlParams = new URLSearchParams(location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const error = urlParams.get('error');

      if (error) {
        setStatus('error');
        toast.error(`Xero authorization failed: ${error}`);
        
        // If we're in a popup, notify the opener and close
        if (window.opener) {
          window.opener.postMessage({ type: 'xero-auth-error', error }, '*');
          setTimeout(() => window.close(), 3000);
        }
        return;
      }

      if (!code) {
        setStatus('error');
        toast.error('No authorization code received from Xero');
        
        // If we're in a popup, notify the opener and close
        if (window.opener) {
          window.opener.postMessage({ type: 'xero-auth-error', error: 'No code' }, '*');
          setTimeout(() => window.close(), 3000);
        }
        return;
      }

      // If we're in a popup window, pass the data to the parent and close
      if (window.opener) {
        window.opener.postMessage({ 
          type: 'xero-auth-success', 
          code, 
          state 
        }, '*');
        
        setStatus('success');
        setTimeout(() => {
          window.close();
        }, 1000);
        return;
      }

      // If not in popup, handle directly (fallback)
      const response = await apiHelpers.handleXeroCallback({ code, state });
      
      setStatus('success');
      toast.success('Successfully connected to Xero!');
      
      // Close the popup window after a short delay
      setTimeout(() => {
        window.close();
      }, 2000);

    } catch (error) {
      console.error('Xero callback error:', error);
      setStatus('error');
      toast.error('Failed to complete Xero connection');
      
      // If we're in a popup, notify the opener
      if (window.opener) {
        window.opener.postMessage({ type: 'xero-auth-error', error: error.message }, '*');
      }
      
      setTimeout(() => window.close(), 3000);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="bg-gray-800 rounded-lg p-8 border border-gray-700">
          {status === 'processing' && (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400 mx-auto mb-4"></div>
              <h2 className="text-xl font-bold text-white mb-2">Connecting to Xero</h2>
              <p className="text-gray-400">Please wait while we complete the connection...</p>
            </>
          )}
          
          {status === 'success' && (
            <>
              <div className="h-12 w-12 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-green-400 mb-2">Connection Successful!</h2>
              <p className="text-gray-400">Xero has been connected to your Misty account.</p>
              <p className="text-sm text-gray-500 mt-2">This window will close automatically...</p>
            </>
          )}
          
          {status === 'error' && (
            <>
              <div className="h-12 w-12 bg-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-red-400 mb-2">Connection Failed</h2>
              <p className="text-gray-400">There was an error connecting to Xero.</p>
              <p className="text-sm text-gray-500 mt-2">This window will close automatically...</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default XeroCallback;