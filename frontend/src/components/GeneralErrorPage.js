import React from 'react';
import { useNavigate } from 'react-router-dom';

function GeneralErrorPage({ error, resetError }) {
  const navigate = useNavigate();

  const handleTryAgain = () => {
    if (resetError) {
      resetError();
    }
    navigate('/dashboard');
  };

  const handleGoHome = () => {
    if (resetError) {
      resetError();
    }
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
        {/* Main Error Message */}
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-yellow-400 mb-6 leading-tight text-center">
          OHHHH, FUG MY TIGHT LITTLE P.....rogram has an error!<br />
          Try again, hung boy.
        </h1>
        
        {/* Error Details */}
        {error && (
          <div className="bg-gray-800/80 backdrop-blur-sm rounded-lg p-6 mb-8 border border-yellow-400/30">
            <p className="text-yellow-400 font-semibold mb-2">Error Details:</p>
            <p className="text-gray-300 text-sm font-mono break-words">
              {error.toString()}
            </p>
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <button
            onClick={handleTryAgain}
            className="px-8 py-3 bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-bold rounded-lg transition-colors duration-200 min-w-[200px]"
          >
            Try Again
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
          If this problem persists, please contact your system administrator or try refreshing the page.
        </p>
      </div>
    </div>
  );
}

export default GeneralErrorPage;
