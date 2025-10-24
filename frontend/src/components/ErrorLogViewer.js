import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';

const ErrorLogViewer = () => {
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, critical, error, warning

  useEffect(() => {
    loadErrorLogs();
  }, []);

  const loadErrorLogs = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/error-logs`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setErrors(data.data || []);
      } else {
        toast.error('Failed to load error logs');
      }
    } catch (error) {
      console.error('Error loading error logs:', error);
      toast.error('Failed to load error logs');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'text-red-400';
      case 'error':
        return 'text-orange-400';
      case 'warning':
        return 'text-yellow-400';
      default:
        return 'text-gray-400';
    }
  };

  const filteredErrors = filter === 'all' 
    ? errors 
    : errors.filter(err => err.severity === filter);

  return (
    <div className="min-h-screen w-full relative flex flex-col overflow-hidden bg-gray-900">
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
      <div className="relative z-10 p-8 flex-1 overflow-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold text-yellow-400 mb-4">
            Application Error Logs
          </h1>
          <p className="text-xl text-gray-300">
            Review errors and affected code
          </p>
        </div>

        {/* Filters */}
        <div className="max-w-6xl mx-auto mb-6 flex justify-center space-x-4">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'all'
                ? 'bg-yellow-400 text-gray-900'
                : 'bg-gray-800/80 text-yellow-400 hover:bg-gray-700/80'
            }`}
          >
            All ({errors.length})
          </button>
          <button
            onClick={() => setFilter('critical')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'critical'
                ? 'bg-red-400 text-gray-900'
                : 'bg-gray-800/80 text-red-400 hover:bg-gray-700/80'
            }`}
          >
            Critical ({errors.filter(e => e.severity === 'critical').length})
          </button>
          <button
            onClick={() => setFilter('error')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'error'
                ? 'bg-orange-400 text-gray-900'
                : 'bg-gray-800/80 text-orange-400 hover:bg-gray-700/80'
            }`}
          >
            Errors ({errors.filter(e => e.severity === 'error').length})
          </button>
          <button
            onClick={() => setFilter('warning')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'warning'
                ? 'bg-yellow-400 text-gray-900'
                : 'bg-gray-800/80 text-yellow-400 hover:bg-gray-700/80'
            }`}
          >
            Warnings ({errors.filter(e => e.severity === 'warning').length})
          </button>
          <button
            onClick={loadErrorLogs}
            className="px-4 py-2 rounded-lg font-medium bg-gray-800/80 text-gray-300 hover:bg-gray-700/80 transition-colors"
          >
            Refresh
          </button>
        </div>

        {/* Error List */}
        <div className="max-w-6xl mx-auto space-y-4">
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400 mx-auto"></div>
              <p className="text-gray-400 mt-4">Loading error logs...</p>
            </div>
          ) : filteredErrors.length === 0 ? (
            <div className="bg-gray-800/80 backdrop-blur-sm rounded-lg p-12 text-center border border-yellow-400/30">
              <svg className="w-16 h-16 text-green-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-2xl font-bold text-yellow-400 mb-2">No Errors Found</h3>
              <p className="text-gray-400">The application is running smoothly!</p>
            </div>
          ) : (
            filteredErrors.map((error, index) => (
              <div 
                key={index}
                className="bg-gray-800/80 backdrop-blur-sm rounded-lg p-6 border border-yellow-400/30 hover:border-yellow-400/50 transition-all"
              >
                {/* Error Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className={`px-3 py-1 rounded text-sm font-bold ${getSeverityColor(error.severity)}`}>
                        {error.severity?.toUpperCase() || 'ERROR'}
                      </span>
                      <span className="text-gray-400 text-sm">
                        {new Date(error.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <h3 className="text-xl font-semibold text-yellow-400 mb-2">
                      {error.message || 'Unknown Error'}
                    </h3>
                  </div>
                </div>

                {/* Error Details */}
                {error.details && (
                  <div className="mb-4">
                    <p className="text-gray-300 text-sm">{error.details}</p>
                  </div>
                )}

                {/* Affected Files/Code */}
                {error.affected_files && error.affected_files.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-yellow-400 mb-2">Affected Files:</h4>
                    <div className="space-y-1">
                      {error.affected_files.map((file, idx) => (
                        <div key={idx} className="bg-gray-900/50 rounded px-3 py-2">
                          <code className="text-sm text-gray-300">{file}</code>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Stack Trace */}
                {error.stack_trace && (
                  <div>
                    <h4 className="text-sm font-semibold text-yellow-400 mb-2">Stack Trace:</h4>
                    <div className="bg-gray-900/50 rounded p-3 overflow-x-auto">
                      <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap">
                        {error.stack_trace}
                      </pre>
                    </div>
                  </div>
                )}

                {/* Error Context */}
                {error.context && (
                  <div className="mt-4">
                    <h4 className="text-sm font-semibold text-yellow-400 mb-2">Context:</h4>
                    <div className="bg-gray-900/50 rounded p-3">
                      <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap">
                        {JSON.stringify(error.context, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Back Button */}
        <div className="text-center mt-8">
          <button
            onClick={() => window.close()}
            className="px-8 py-3 bg-yellow-400 hover:bg-yellow-500 text-gray-900 font-bold rounded-lg transition-colors duration-200"
          >
            Close Window
          </button>
        </div>
      </div>
    </div>
  );
};

export default ErrorLogViewer;
