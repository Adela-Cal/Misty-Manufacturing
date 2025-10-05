import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';

const JobCardSimple = ({ jobId, stage, orderId, onClose }) => {
  console.log('JobCardSimple props:', { jobId, stage, orderId });

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] overflow-y-auto w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Job Card - Test</h2>
          <button
            onClick={onClose}
            className="flex items-center px-3 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
          >
            <XMarkIcon className="h-4 w-4 mr-2" />
            Close
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="bg-blue-50 p-4 rounded-lg mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Order Information</h3>
            <div className="space-y-2 text-sm">
              <div><strong>Job ID:</strong> {jobId || 'N/A'}</div>
              <div><strong>Stage:</strong> {stage || 'N/A'}</div>
              <div><strong>Order ID:</strong> {orderId || 'N/A'}</div>
              <div><strong>Customer:</strong> Sample Client Co.</div>
              <div><strong>Quantity:</strong> 1,000 units</div>
              <div><strong>Due Date:</strong> {new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toLocaleDateString()}</div>
            </div>
          </div>

          <div className="bg-purple-50 p-4 rounded-lg mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Machine Line</h3>
            <div className="space-y-2 text-sm">
              <div><strong>Machine:</strong> Test Machine 1</div>
              <div><strong>Setup Time:</strong> 30 minutes</div>
              <div><strong>Run Time:</strong> 120 minutes</div>
            </div>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Product Specifications</h3>
            <div className="space-y-2 text-sm">
              <div><strong>Product Code:</strong> PC-100-50</div>
              <div><strong>Description:</strong> Paper Core 100mm ID, 50mm length</div>
              <div><strong>Wall Thickness:</strong> 3.0mm</div>
            </div>
          </div>

          <div className="bg-green-50 p-4 rounded-lg mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Production Calculations</h3>
            <div className="space-y-2 text-sm">
              <div><strong>Material Length:</strong> 1,000 meters</div>
              <div><strong>Setup Time:</strong> 30 minutes</div>
              <div><strong>Total Time:</strong> 150 minutes</div>
            </div>
          </div>

          <div className="bg-yellow-50 p-4 rounded-lg mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Quality Control</h3>
            <div className="space-y-2 text-sm">
              <div><strong>ID Tolerance:</strong> ±0.5 mm</div>
              <div><strong>Wall Tolerance:</strong> ±0.1 mm</div>
              <div><strong>Check Interval:</strong> Every 60 minutes</div>
            </div>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Packing & Delivery</h3>
            <div className="space-y-2 text-sm">
              <div><strong>Tubes per Carton:</strong> 50</div>
              <div><strong>Cartons Required:</strong> 20</div>
              <div><strong>Pallets Required:</strong> 1</div>
            </div>
          </div>

          <div className="border-t-2 border-gray-800 pt-4 mt-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Operator Sign-off</h3>
            <div className="grid grid-cols-3 gap-6">
              <div className="text-center">
                <div className="border-b-2 border-gray-400 mb-2 h-8"></div>
                <div className="text-sm text-gray-600">Setup By / Date</div>
              </div>
              <div className="text-center">
                <div className="border-b-2 border-gray-400 mb-2 h-8"></div>
                <div className="text-sm text-gray-600">Production By / Date</div>
              </div>
              <div className="text-center">
                <div className="border-b-2 border-gray-400 mb-2 h-8"></div>
                <div className="text-sm text-gray-600">QC Check By / Date</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default JobCardSimple;