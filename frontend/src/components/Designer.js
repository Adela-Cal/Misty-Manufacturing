import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from './Layout';
import LabelDesigner from './LabelDesigner';
import PageDesigner from './PageDesigner';
import { HomeIcon } from '@heroicons/react/24/outline';

const Designer = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('labels');

  return (
    <Layout>
      <div className="min-h-screen bg-gray-900">
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-yellow-400">Designer</h1>
            <button
              onClick={() => navigate('/')}
              className="misty-button misty-button-secondary flex items-center"
            >
              <HomeIcon className="h-5 w-5 mr-2" />
              Back to Dashboard
            </button>
          </div>
          
          {/* Tabs */}
          <div className="flex space-x-1 mt-4">
            <button
              onClick={() => setActiveTab('labels')}
              className={`px-6 py-3 rounded-t-lg font-medium transition-colors ${
                activeTab === 'labels'
                  ? 'bg-gray-900 text-yellow-400 border-t-2 border-yellow-400'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Label Designs
            </button>
            <button
              onClick={() => setActiveTab('pages')}
              className={`px-6 py-3 rounded-t-lg font-medium transition-colors ${
                activeTab === 'pages'
                  ? 'bg-gray-900 text-yellow-400 border-t-2 border-yellow-400'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Page Designs
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === 'labels' ? (
            <LabelDesigner embedded={true} />
          ) : (
            <PageDesigner />
          )}
        </div>
      </div>
    </Layout>
  );
};

export default Designer;
