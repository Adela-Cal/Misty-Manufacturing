import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  ClipboardDocumentListIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  CalendarIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  BellIcon,
  BellSlashIcon,
  ArrowUpIcon,
  ArrowDownIcon
} from '@heroicons/react/24/outline';

const Stocktake = () => {
  // Monthly Stocktake states
  const [currentStocktake, setCurrentStocktake] = useState(null);
  const [stocktakeRequired, setStocktakeRequired] = useState(false);
  const [materials, setMaterials] = useState([]);
  const [entries, setEntries] = useState({});
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);

  // Stock Management System states
  const [activeTab, setActiveTab] = useState('monthly'); // monthly, raw_substrates, raw_materials
  const [rawSubstrates, setRawSubstrates] = useState([]);
  const [rawMaterialsStock, setRawMaterialsStock] = useState([]);
  const [selectedClient, setSelectedClient] = useState('all'); // for filtering substrates
  const [clients, setClients] = useState([]);
  const [stockAlerts, setStockAlerts] = useState([]);
  const [showStockAlert, setShowStockAlert] = useState(false);

  // Modal states
  const [showSubstrateModal, setShowSubstrateModal] = useState(false);
  const [showMaterialModal, setShowMaterialModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [editingField, setEditingField] = useState(null);

  // Form states for new entries
  const [substrateForm, setSubstrateForm] = useState({
    client_id: '',
    client_name: '',
    product_id: '',
    product_code: '',
    product_description: '',
    quantity_on_hand: 0,
    unit_of_measure: 'units',
    source_order_id: '',
    is_shared_product: false,
    shared_with_clients: [],
    minimum_stock_level: 0
  });

  const [materialForm, setMaterialForm] = useState({
    material_id: '',
    material_name: '',
    quantity_on_hand: 0,
    unit_of_measure: 'kg',
    minimum_stock_level: 0,
    alert_threshold_days: 7,
    supplier_id: '',
    usage_rate_per_month: 0
  });

  useEffect(() => {
    loadStocktakeStatus();
  }, []);

  const loadStocktakeStatus = async () => {
    try {
      setLoading(true);
      const response = await apiHelpers.getCurrentStocktake();
      const data = response.data;
      
      setCurrentStocktake(data.stocktake);
      setStocktakeRequired(data.stocktake_required);
      
      // If stocktake exists but not completed, load entries
      if (data.stocktake && data.stocktake.status === 'in_progress') {
        // Load materials for this stocktake (you may need to add this endpoint)
        const materialsRes = await apiHelpers.getMaterials();
        setMaterials(materialsRes.data);
      }
    } catch (error) {
      console.error('Failed to load stocktake status:', error);
      toast.error('Failed to load stocktake status');
    } finally {
      setLoading(false);
    }
  };

  const startStocktake = async () => {
    try {
      const today = new Date();
      const response = await apiHelpers.createStocktake({
        stocktake_date: today.toISOString().split('T')[0]
      });
      
      setMaterials(response.data.materials);
      setCurrentStocktake({
        id: response.data.stocktake_id,
        status: 'in_progress',
        stocktake_date: today.toISOString().split('T')[0],
        month: today.toISOString().substring(0, 7)
      });
      setStocktakeRequired(false);
      
      toast.success('Stocktake started successfully');
    } catch (error) {
      console.error('Failed to start stocktake:', error);
      toast.error('Failed to start stocktake');
    }
  };

  const updateEntry = async (materialId, quantity) => {
    if (!currentStocktake) return;
    
    try {
      await apiHelpers.updateStocktakeEntry(currentStocktake.id, {
        material_id: materialId,
        current_quantity: parseFloat(quantity)
      });
      
      setEntries(prev => ({
        ...prev,
        [materialId]: quantity
      }));
      
      // Auto-save toast (optional)
      // toast.success('Entry saved');
    } catch (error) {
      console.error('Failed to update entry:', error);
      toast.error('Failed to save entry');
    }
  };

  const completeStocktake = async () => {
    if (!currentStocktake) return;
    
    // Check if all materials have been counted
    const uncountedMaterials = materials.filter(material => 
      !entries[material.id] && entries[material.id] !== '0'
    );
    
    if (uncountedMaterials.length > 0) {
      toast.error(`Please count all materials. ${uncountedMaterials.length} materials remaining.`);
      return;
    }
    
    try {
      setCompleting(true);
      await apiHelpers.completeStocktake(currentStocktake.id);
      
      setCurrentStocktake(prev => ({
        ...prev,
        status: 'completed'
      }));
      
      toast.success('Stocktake completed successfully');
    } catch (error) {
      console.error('Failed to complete stocktake:', error);
      toast.error('Failed to complete stocktake');
    } finally {
      setCompleting(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="p-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-700 rounded w-1/4 mb-8"></div>
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  const isFirstBusinessDay = new Date().getDate() === 1; // Simplified check

  return (
    <Layout>
      <div className="p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Monthly Stocktake</h1>
            <p className="text-gray-400">Inventory count for {new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</p>
          </div>
          {isFirstBusinessDay && stocktakeRequired && (
            <div className="bg-red-900/20 border border-red-500 rounded-lg p-3 flex items-center">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-2" />
              <span className="text-red-300 text-sm">Stocktake required today!</span>
            </div>
          )}
        </div>

        {/* Stocktake Status */}
        {!currentStocktake && stocktakeRequired ? (
          // No stocktake - show prompt to start
          <div className="bg-gray-800 rounded-lg p-8 text-center">
            <ClipboardDocumentListIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">Monthly Stocktake Required</h2>
            <p className="text-gray-300 mb-6">
              It's time to conduct the monthly inventory count. This will generate a list of all materials 
              in your inventory for manual counting.
            </p>
            <div className="bg-yellow-900/20 border border-yellow-500 rounded p-4 mb-6">
              <p className="text-yellow-300 text-sm">
                <strong>Note:</strong> Once started, you'll need to count all {materials.length} materials 
                in your inventory. This process can be completed over multiple sessions.
              </p>
            </div>
            <button
              onClick={startStocktake}
              className="misty-button misty-button-primary"
            >
              <CalendarIcon className="h-5 w-5 mr-2" />
              Start Monthly Stocktake
            </button>
          </div>
        ) : currentStocktake && currentStocktake.status === 'completed' ? (
          // Completed stocktake
          <div className="bg-gray-800 rounded-lg p-8 text-center">
            <CheckCircleIcon className="h-16 w-16 text-green-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">Stocktake Completed</h2>
            <p className="text-gray-300 mb-4">
              Monthly stocktake for {new Date(currentStocktake.stocktake_date).toLocaleDateString()} has been completed.
            </p>
            <div className="text-sm text-gray-400">
              Completed on: {new Date(currentStocktake.completed_at || currentStocktake.stocktake_date).toLocaleDateString()}
            </div>
          </div>
        ) : currentStocktake ? (
          // In progress stocktake
          <div className="space-y-6">
            {/* Progress Header */}
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-semibold text-white">Stocktake in Progress</h2>
                <span className="text-sm text-gray-400">
                  Started: {new Date(currentStocktake.stocktake_date).toLocaleDateString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-300">
                  Progress: {Object.keys(entries).length} / {materials.length} materials counted
                </div>
                <button
                  onClick={completeStocktake}
                  disabled={completing || Object.keys(entries).length < materials.length}
                  className="misty-button misty-button-primary disabled:opacity-50"
                >
                  {completing ? 'Completing...' : 'Complete Stocktake'}
                </button>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2 mt-3">
                <div 
                  className="bg-yellow-400 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(Object.keys(entries).length / materials.length) * 100}%` }}
                ></div>
              </div>
            </div>

            {/* Materials List */}
            <div className="bg-gray-800 rounded-lg">
              <div className="p-4 border-b border-gray-700">
                <h3 className="text-lg font-semibold text-white">Material Count</h3>
                <p className="text-sm text-gray-400">Enter the current quantity on hand for each material (up to 2 decimal places)</p>
              </div>
              
              <div className="divide-y divide-gray-700">
                {materials.map((material) => (
                  <div key={material.id} className="p-4 flex items-center justify-between">
                    <div className="flex-1">
                      <div className="font-medium text-white">{material.name || `${material.supplier} - ${material.product_code}`}</div>
                      <div className="text-sm text-gray-400">Unit: {material.unit}</div>
                    </div>
                    
                    <div className="flex items-center space-x-3">
                      <div className="w-32">
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          placeholder="0.00"
                          value={entries[material.id] || ''}
                          onChange={(e) => {
                            const value = e.target.value;
                            setEntries(prev => ({ ...prev, [material.id]: value }));
                          }}
                          onBlur={(e) => {
                            const value = e.target.value;
                            if (value !== '') {
                              updateEntry(material.id, value);
                            }
                          }}
                          className="misty-input w-full text-right"
                        />
                      </div>
                      
                      <div className="w-6 flex justify-center">
                        {entries[material.id] !== undefined && entries[material.id] !== '' ? (
                          <CheckCircleIcon className="h-5 w-5 text-green-400" />
                        ) : (
                          <div className="h-2 w-2 bg-gray-500 rounded-full"></div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Instructions */}
            <div className="bg-blue-900/20 border border-blue-500 rounded-lg p-4">
              <h4 className="font-medium text-blue-300 mb-2">Instructions:</h4>
              <ul className="text-sm text-blue-200 space-y-1">
                <li>• Count each material carefully and enter the exact quantity on hand</li>
                <li>• You can enter up to 2 decimal places (e.g., 15.75)</li>
                <li>• Entries are automatically saved when you move to the next field</li>
                <li>• All materials must be counted before completing the stocktake</li>
                <li>• The stocktake can be completed over multiple sessions</li>
              </ul>
            </div>
          </div>
        ) : (
          // No stocktake required
          <div className="bg-gray-800 rounded-lg p-8 text-center">
            <ClipboardDocumentListIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-white mb-2">No Stocktake Required</h2>
            <p className="text-gray-300 mb-4">
              The monthly stocktake for {new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })} 
              has already been completed or is not yet required.
            </p>
            <p className="text-sm text-gray-400">
              Stocktakes are automatically prompted on the first business day of each month.
            </p>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Stocktake;