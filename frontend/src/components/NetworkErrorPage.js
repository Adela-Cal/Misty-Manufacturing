import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const NetworkErrorPage = ({ onRetry }) => {
  const navigate = useNavigate();
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      // Auto-retry when connection is restored
      if (onRetry) {
        setTimeout(() => {
          onRetry();
        }, 1000);
      }
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [onRetry]);

  const handleRetry = async () => {
    setRetrying(true);
    
    // Check if online
    if (!navigator.onLine) {
      setRetrying(false);
      return;
    }

    // Try to fetch something to verify connection
    try {
      const response = await fetch('/manifest.json', { cache: 'no-store' });
      if (response.ok) {
        if (onRetry) {
          onRetry();
        } else {
          window.location.reload();
        }
      }
    } catch (error) {
      console.error('Still offline:', error);
    } finally {
      setRetrying(false);
    }
  };

  const handleGoHome = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <img 
            src="/logo192.png" 
            alt="Misty Manufacturing" 
            className="h-24 w-24 mx-auto mb-6"
          />
          <h1 className="text-4xl font-bold text-yellow-400 mb-2">
            {isOnline ? 'Connection Lost' : 'You\'re Offline'}
          </h1>
          <p className="text-xl text-gray-300">
            {isOnline 
              ? 'Unable to reach the server' 
              : 'Please check your internet connection'}
          </p>
        </div>

        {/* Network Status Card */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6 shadow-xl">
          <div className="flex items-start mb-4">
            <div className="flex-shrink-0">
              {isOnline ? (
                <svg className="h-12 w-12 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
                </svg>
              ) : (
                <svg className="h-12 w-12 text-red-400 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
                </svg>
              )}
            </div>
            <div className="ml-4 flex-1">
              <h3 className="text-lg font-semibold text-white mb-2">
                {isOnline ? 'Server Connection Issue' : 'No Internet Connection'}
              </h3>
              <p className="text-gray-300 text-sm mb-3">
                {isOnline 
                  ? 'The application cannot reach the server. This might be temporary.'
                  : 'Your device is not connected to the internet. Please check your connection and try again.'}
              </p>
              
              <div className="text-sm text-gray-400 space-y-1">
                <p>• Check your network connection</p>
                {isOnline && <p>• Verify the server is running</p>}
                {isOnline && <p>• Check NAS is powered on and accessible</p>}
                <p>• Your work is saved locally (where possible)</p>
              </div>

              {isOnline && (
                <div className="mt-4 bg-gray-900 rounded p-3">
                  <p className="text-xs text-yellow-400">
                    💡 <span className="font-semibold">Tip:</span> If you're using NAS, ensure it's on the same network
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Connection Status Indicator */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <span className="text-gray-300 font-medium">Connection Status:</span>
            <div className="flex items-center">
              <div className={`h-3 w-3 rounded-full mr-2 ${isOnline ? 'bg-orange-400' : 'bg-red-500 animate-pulse'}`}></div>
              <span className={`font-semibold ${isOnline ? 'text-orange-400' : 'text-red-400'}`}>
                {isOnline ? 'Server Unreachable' : 'Offline'}
              </span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={handleRetry}
            disabled={retrying}
            className="flex items-center justify-center bg-yellow-500 hover:bg-yellow-600 disabled:bg-yellow-700 disabled:cursor-not-allowed text-gray-900 font-semibold px-6 py-3 rounded-lg transition-colors duration-200 shadow-lg"
          >
            {retrying ? (
              <>
                <svg className="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Retrying...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Try Again
              </>
            )}
          </button>
          
          <button
            onClick={handleGoHome}
            className="flex items-center justify-center bg-gray-700 hover:bg-gray-600 text-white font-semibold px-6 py-3 rounded-lg transition-colors duration-200 shadow-lg"
          >
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Go to Dashboard
          </button>
        </div>

        {/* Help Text */}
        <div className="text-center mt-8">
          <p className="text-gray-400 text-sm">
            Connection issues persist? Contact your system administrator
          </p>
        </div>
      </div>
    </div>
  );
};

export default NetworkErrorPage;
