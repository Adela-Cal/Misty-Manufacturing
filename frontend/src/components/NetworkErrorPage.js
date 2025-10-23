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
    <div className="min-h-screen w-full relative flex items-center justify-center overflow-hidden bg-gray-900">
      {/* Background Image with 30% opacity */}
      <div 
        className="absolute inset-0 bg-center bg-no-repeat"
        style={{
          backgroundImage: 'url(/Error-Screen-Background.png)',
          backgroundSize: 'contain',
          opacity: 0.3
        }}
      />
      
      {/* Content */}
      <div className="relative z-10 text-center px-4 max-w-2xl">
        {/* Network Status Icon */}
        <div className="mb-6">
          {isOnline ? (
            <svg 
              className="w-24 h-24 mx-auto text-yellow-400" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" 
              />
            </svg>
          ) : (
            <svg 
              className="w-24 h-24 mx-auto text-yellow-400 animate-pulse" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" 
              />
            </svg>
          )}
        </div>

        {/* Main Error Message */}
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-yellow-400 mb-4 leading-tight">
          {isOnline ? 'Connection Lost' : 'You\'re Offline'}
        </h1>
        
        <p className="text-2xl md:text-3xl text-yellow-400 mb-8">
          {isOnline 
            ? 'Can\'t reach the server, Big Boy!'
            : 'No internet connection, Big Boy!'}
        </p>
        
        {/* Connection Status */}
        <div className="bg-gray-800/80 backdrop-blur-sm rounded-lg p-6 mb-8 border border-yellow-400/30">
          <div className="flex items-center justify-center mb-4">
            <div className={`w-3 h-3 rounded-full mr-3 ${isOnline ? 'bg-orange-400' : 'bg-red-400'} animate-pulse`}></div>
            <p className="text-yellow-400 font-semibold">
              Status: {isOnline ? 'Server Unreachable' : 'Offline'}
            </p>
          </div>
          <p className="text-gray-300 text-sm mb-4">
            {isOnline 
              ? 'The application cannot reach the server. This might be temporary.'
              : 'Your device is not connected to the internet. Please check your connection and try again.'}
          </p>
          
          <div className="text-sm text-gray-400 space-y-1 text-left max-w-md mx-auto">
            <p>• Check your network connection</p>
            {isOnline && <p>• Verify the server is running</p>}
            {isOnline && <p>• Check NAS is powered on and accessible</p>}
            <p>• Your work is saved locally (where possible)</p>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <button
            onClick={handleRetry}
            disabled={retrying}
            className="px-8 py-3 bg-yellow-400 hover:bg-yellow-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-gray-900 font-bold rounded-lg transition-colors duration-200 min-w-[200px] flex items-center justify-center"
          >
            {retrying ? (
              <>
                <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Retrying...
              </>
            ) : (
              'Retry Connection'
            )}
          </button>
          <button
            onClick={handleGoHome}
            className="px-8 py-3 bg-transparent border-2 border-yellow-400 hover:bg-yellow-400/10 text-yellow-400 font-bold rounded-lg transition-colors duration-200 min-w-[200px]"
          >
            Go to Home
          </button>
        </div>
        
        {/* Additional Help Text */}
        <p className="text-gray-400 text-sm mt-8">
          Connection issues persist? Contact your system administrator
        </p>
      </div>
    </div>
  );
};

export default NetworkErrorPage;
