import React from 'react';
import { useNavigate } from 'react-router-dom';

const GeneralErrorPage = ({ error, resetError }) => {
  const navigate = useNavigate();

  const handleGoHome = () => {
    if (resetError) resetError();
    navigate('/');
  };

  const handleRefresh = () => {
    if (resetError) resetError();
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <img 
            src="/logo192.png" 
            alt="Misty Manufacturing" 
            className="h-24 w-24 mx-auto mb-6 animate-pulse"
          />
          <h1 className="text-4xl font-bold text-yellow-400 mb-2">
            Oops! Something Went Wrong
          </h1>
          <p className="text-xl text-gray-300">
            We encountered an unexpected error
          </p>
        </div>

        {/* Error Details Card */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6 shadow-xl">
          <div className="flex items-start mb-4">
            <div className="flex-shrink-0">
              <svg className="h-12 w-12 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="ml-4 flex-1">
              <h3 className="text-lg font-semibold text-white mb-2">Error Details</h3>
              <p className="text-gray-300 text-sm mb-3">
                Don't worry! Our system is designed to recover from errors. Try one of the options below:
              </p>
              {error && (
                <div className="bg-gray-900 rounded p-3 mb-3">
                  <p className="text-xs text-gray-400 font-mono break-all">
                    {error.message || 'An unexpected error occurred'}
                  </p>
                </div>
              )}
              <div className="text-sm text-gray-400">
                <p>• Your work has been auto-saved</p>
                <p>• You can safely return to the dashboard</p>
                <p>• If this persists, contact your system administrator</p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={handleGoHome}
            className="flex items-center justify-center bg-yellow-500 hover:bg-yellow-600 text-gray-900 font-semibold px-6 py-3 rounded-lg transition-colors duration-200 shadow-lg"
          >
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Go to Dashboard
          </button>
          
          <button
            onClick={handleRefresh}
            className="flex items-center justify-center bg-gray-700 hover:bg-gray-600 text-white font-semibold px-6 py-3 rounded-lg transition-colors duration-200 shadow-lg"
          >
            <svg className="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh Page
          </button>
        </div>

        {/* Help Text */}
        <div className="text-center mt-8">
          <p className="text-gray-400 text-sm">
            Need help? Contact your system administrator
          </p>
          <p className="text-gray-500 text-xs mt-2">
            Error ID: {new Date().getTime()}
          </p>
        </div>
      </div>
    </div>
  );
};

export default GeneralErrorPage;
