import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  CalculatorIcon,
  CalendarIcon,
  CubeIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

const Calculators = () => {
  const [activeCalculator, setActiveCalculator] = useState(null);
  const [loading, setLoading] = useState(false);
  const [clients, setClients] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [productSpecs, setProductSpecs] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [clientsRes, materialsRes, specsRes] = await Promise.all([
        apiHelpers.getClients(),
        apiHelpers.getMaterials(),
        apiHelpers.getProductSpecifications()
      ]);
      setClients(clientsRes.data);
      setMaterials(materialsRes.data);
      setProductSpecs(specsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load calculator data');
    }
  };

  const calculators = [
    {
      id: 'material-consumption-client',
      name: 'Material Consumption by Client',
      description: 'Calculate material consumption for client orders within date range',
      icon: CalendarIcon
    },
    {
      id: 'material-permutation',
      name: 'Material Permutation',
      description: 'Calculate all slit-cut patterns for master rolls with cost, waste, and yield optimization',
      icon: CubeIcon
    },
    {
      id: 'spiral-core-consumption',
      name: 'Spiral Paper Core Consumption',
      description: 'Calculate material usage for Spiral Paper Core manufacturing',
      icon: CalculatorIcon
    }
  ];

  return (
    <Layout>
      <div className="p-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">Manufacturing Calculators</h1>
          <p className="text-gray-400">Advanced calculation tools for manufacturing processes</p>
        </div>

        {!activeCalculator ? (
          // Calculator Selection
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {calculators.map((calc) => (
              <div
                key={calc.id}
                onClick={() => setActiveCalculator(calc.id)}
                className="bg-gray-800 rounded-lg p-6 cursor-pointer hover:bg-gray-700 transition-colors border border-gray-700 hover:border-yellow-400"
              >
                <div className="flex items-center mb-4">
                  <calc.icon className="h-8 w-8 text-yellow-400 mr-3" />
                  <h3 className="text-lg font-semibold text-white">{calc.name}</h3>
                </div>
                <p className="text-gray-300 text-sm">{calc.description}</p>
                <div className="mt-4">
                  <span className="text-yellow-400 text-sm font-medium">Click to open →</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          // Active Calculator
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">
                {calculators.find(c => c.id === activeCalculator)?.name}
              </h2>
              <button
                onClick={() => setActiveCalculator(null)}
                className="misty-button misty-button-secondary"
              >
                ← Back to Calculators
              </button>
            </div>

            {activeCalculator === 'material-consumption-client' && (
              <MaterialConsumptionByClient 
                clients={clients} 
                materials={materials}
                loading={loading}
                setLoading={setLoading}
              />
            )}

            {activeCalculator === 'material-permutation' && (
              <MaterialPermutation 
                loading={loading}
                setLoading={setLoading}
              />
            )}

            {activeCalculator === 'spiral-core-consumption' && (
              <SpiralCoreConsumption 
                productSpecs={productSpecs.filter(spec => spec.product_type === 'Spiral Paper Core')}
                loading={loading}
                setLoading={setLoading}
              />
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};

// Material Consumption by Client Calculator
const MaterialConsumptionByClient = ({ clients, materials, loading, setLoading }) => {
  const [formData, setFormData] = useState({
    client_id: '',
    material_id: '',
    start_date: '',
    end_date: ''
  });
  const [results, setResults] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await apiHelpers.calculateMaterialConsumptionByClient(formData);
      setResults(response.data.data);
      toast.success('Calculation completed successfully');
    } catch (error) {
      console.error('Calculation failed:', error);
      toast.error('Calculation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Client</label>
          <select
            value={formData.client_id}
            onChange={(e) => setFormData({...formData, client_id: e.target.value})}
            className="misty-select w-full"
            required
          >
            <option value="">Select client</option>
            {clients.map(client => (
              <option key={client.id} value={client.id}>{client.company_name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Material</label>
          <select
            value={formData.material_id}
            onChange={(e) => setFormData({...formData, material_id: e.target.value})}
            className="misty-select w-full"
            required
          >
            <option value="">Select material</option>
            {materials.map(material => (
              <option key={material.id} value={material.id}>
                {material.supplier} - {material.product_code}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Start Date</label>
          <input
            type="date"
            value={formData.start_date}
            onChange={(e) => setFormData({...formData, start_date: e.target.value})}
            className="misty-input w-full"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">End Date</label>
          <input
            type="date"
            value={formData.end_date}
            onChange={(e) => setFormData({...formData, end_date: e.target.value})}
            className="misty-input w-full"
            required
          />
        </div>

        <div className="md:col-span-2">
          <button
            type="submit"
            disabled={loading}
            className="misty-button misty-button-primary"
          >
            {loading ? (
              <>
                <ArrowPathIcon className="animate-spin h-4 w-4 mr-2" />
                Calculating...
              </>
            ) : (
              'Calculate Consumption'
            )}
          </button>
        </div>
      </form>

      {results && (
        <div className="bg-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-4">Calculation Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">{results.results.total_consumption}</div>
              <div className="text-sm text-gray-300">{results.results.unit} Total Consumption</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{results.results.order_count}</div>
              <div className="text-sm text-gray-300">Orders Analyzed</div>
            </div>
            <div className="text-center">
              <div className="text-lg font-semibold text-green-400">{results.results.material_name}</div>
              <div className="text-sm text-gray-300">Material</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Raw Material Permutation and Yield Calculator
const MaterialPermutation = ({ loading, setLoading }) => {
  const [rawMaterials, setRawMaterials] = useState([]);
  const [formData, setFormData] = useState({
    material_id: '',
    waste_allowance_mm: 5,
    desired_slit_widths: [''],
    quantity_master_rolls: 1
  });
  const [results, setResults] = useState(null);
  const [sortBy, setSortBy] = useState('yield'); // yield, waste, cost
  const [selectedMaterial, setSelectedMaterial] = useState(null);

  useEffect(() => {
    loadRawMaterials();
  }, []);

  const loadRawMaterials = async () => {
    try {
      // Try materials endpoint first (has all required fields)
      let response = await fetch('/api/materials', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        // Materials endpoint returns array directly
        setRawMaterials(data);
        return;
      }
      
      // Fallback to stock/raw-materials endpoint
      response = await fetch('/api/stock/raw-materials', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const result = await response.json();
        // Stock endpoint returns StandardResponse format
        setRawMaterials(result.data || []);
      }
    } catch (error) {
      console.error('Failed to load raw materials:', error);
      toast.error('Failed to load raw materials');
    }
  };

  const handleMaterialChange = (materialId) => {
    // Materials endpoint uses 'id', raw materials use 'material_id'
    const material = rawMaterials.find(m => m.id === materialId || m.material_id === materialId);
    setSelectedMaterial(material);
    setFormData({ ...formData, material_id: materialId });
  };

  const addSlitWidth = () => {
    setFormData({
      ...formData,
      desired_slit_widths: [...formData.desired_slit_widths, '']
    });
  };

  const removeSlitWidth = (index) => {
    const newWidths = formData.desired_slit_widths.filter((_, i) => i !== index);
    setFormData({ ...formData, desired_slit_widths: newWidths });
  };

  const updateSlitWidth = (index, value) => {
    const newWidths = formData.desired_slit_widths.map((w, i) => 
      i === index ? value : w
    );
    setFormData({ ...formData, desired_slit_widths: newWidths });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Filter out empty widths and convert to numbers
      const validWidths = formData.desired_slit_widths
        .filter(w => w !== '' && !isNaN(parseFloat(w)))
        .map(w => parseFloat(w));
      
      if (validWidths.length === 0) {
        toast.error('Please enter at least one slit width');
        setLoading(false);
        return;
      }

      const requestData = {
        material_id: formData.material_id,
        waste_allowance_mm: parseFloat(formData.waste_allowance_mm),
        desired_slit_widths: validWidths,
        quantity_master_rolls: parseInt(formData.quantity_master_rolls)
      };

      const response = await fetch('/api/calculators/material-permutation', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data.data);
        toast.success(data.message);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Calculation failed');
      }
    } catch (error) {
      console.error('Calculation failed:', error);
      toast.error('Permutation calculation failed');
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    if (!results) return;
    
    const headers = ['Pattern', 'Used Width (mm)', 'Waste (mm)', 'Yield (%)', 'Slits/Roll', 'Total Rolls', 'Linear Meters', 'Weight (kg)', 'Cost/Pattern (AUD)', 'Total Cost (AUD)'];
    const rows = results.permutations.map(p => [
      p.pattern_description,
      p.used_width_mm,
      p.waste_mm,
      p.yield_percentage,
      p.slits_per_master_roll,
      p.total_finished_rolls,
      p.linear_meters_per_slit,
      p.total_pattern_weight_kg,
      p.total_pattern_cost_aud,
      p.total_cost_all_rolls_aud
    ]);
    
    const csvContent = [
      ['Raw Material Permutation and Yield Calculator'],
      ['Material: ' + results.material_info.material_name],
      ['Master Width: ' + results.material_info.master_width_mm + 'mm'],
      [],
      headers,
      ...rows
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `material-permutation-${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    toast.success('CSV exported successfully');
  };

  const printResults = () => {
    window.print();
  };

  const getSortedPermutations = () => {
    if (!results) return [];
    
    const perms = [...results.permutations];
    
    switch (sortBy) {
      case 'waste':
        return perms.sort((a, b) => a.waste_mm - b.waste_mm);
      case 'cost':
        return perms.sort((a, b) => a.total_cost_all_rolls_aud - b.total_cost_all_rolls_aud);
      case 'yield':
      default:
        return perms.sort((a, b) => b.yield_percentage - a.yield_percentage);
    }
  };

  return (
    <div>
      <div className="bg-blue-900 bg-opacity-20 border border-blue-500 border-opacity-30 rounded-lg p-4 mb-6">
        <h3 className="text-blue-200 font-medium mb-2">📐 Raw Material Permutation & Yield Calculator</h3>
        <p className="text-sm text-blue-300">
          Calculate all possible slit-cut patterns for converting master rolls into smaller widths. 
          Find the most efficient patterns to minimize waste, maximize yield, and optimize costs.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 mb-6">
        {/* Material Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            1. Select Raw Material <span className="text-red-400">*</span>
          </label>
          <select
            value={formData.material_id}
            onChange={(e) => handleMaterialChange(e.target.value)}
            className="misty-select w-full"
            required
          >
            <option value="">Select a material...</option>
            {rawMaterials.map(material => {
              const materialId = material.id || material.material_id;
              const width = material.width_mm || material.master_deckle_width_mm || 0;
              const supplier = material.supplier || material.material_description || 'Unknown';
              const code = material.product_code || 'N/A';
              const gsm = material.gsm || 0;
              
              return (
                <option key={materialId} value={materialId}>
                  {supplier} - {code} ({width}mm, {gsm} GSM)
                </option>
              );
            })}
          </select>
          
          {selectedMaterial && (
            <div className="mt-3 bg-gray-700 rounded-lg p-4">
              <h4 className="text-sm font-medium text-yellow-400 mb-2">Material Details</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <span className="text-gray-400">Master Width:</span>
                  <p className="text-white font-medium">
                    {selectedMaterial.width_mm || selectedMaterial.master_deckle_width_mm || 0} mm
                  </p>
                </div>
                <div>
                  <span className="text-gray-400">GSM:</span>
                  <p className="text-white font-medium">{selectedMaterial.gsm || 0}</p>
                </div>
                <div>
                  <span className="text-gray-400">Cost/Tonne:</span>
                  <p className="text-white font-medium">
                    ${(selectedMaterial.cost_per_tonne || selectedMaterial.price || 0).toFixed(2)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-400">Tonnage:</span>
                  <p className="text-white font-medium">{selectedMaterial.tonnage || '0'} tonnes</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              2. Waste Allowance (mm) <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={formData.waste_allowance_mm}
              onChange={(e) => setFormData({...formData, waste_allowance_mm: e.target.value})}
              className="misty-input w-full"
              placeholder="e.g., 5"
              required
            />
            <p className="text-xs text-gray-400 mt-1">Maximum acceptable leftover width</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Quantity of Master Rolls
            </label>
            <input
              type="number"
              min="1"
              value={formData.quantity_master_rolls}
              onChange={(e) => setFormData({...formData, quantity_master_rolls: e.target.value})}
              className="misty-input w-full"
              required
            />
            <p className="text-xs text-gray-400 mt-1">Number of rolls available for conversion</p>
          </div>
        </div>

        {/* Desired Slit Widths */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            3. Desired Slit Widths (mm) <span className="text-red-400">*</span>
          </label>
          {formData.desired_slit_widths.map((width, index) => (
            <div key={index} className="flex items-center space-x-2 mb-2">
              <input
                type="number"
                step="0.1"
                min="1"
                placeholder="Width (mm), e.g., 50, 75, 100"
                value={width}
                onChange={(e) => updateSlitWidth(index, e.target.value)}
                className="misty-input flex-1"
                required
              />
              {formData.desired_slit_widths.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeSlitWidth(index)}
                  className="text-red-400 hover:text-red-300 px-3 py-2"
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={addSlitWidth}
            className="text-yellow-400 hover:text-yellow-300 text-sm font-medium"
          >
            + Add Slit Width
          </button>
        </div>

        {/* Calculate Button */}
        <button
          type="submit"
          disabled={loading}
          className="misty-button misty-button-primary w-full md:w-auto"
        >
          {loading ? (
            <>
              <ArrowPathIcon className="animate-spin h-5 w-5 mr-2" />
              Calculating All Permutations...
            </>
          ) : (
            '🔍 Calculate All Permutations'
          )}
        </button>
      </form>

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-gradient-to-r from-green-900/30 to-blue-900/30 border border-green-500 border-opacity-30 rounded-lg p-6">
            <h3 className="text-xl font-bold text-white mb-4">📊 Calculation Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <span className="text-sm text-gray-300">Total Patterns Found</span>
                <p className="text-2xl font-bold text-green-400">{results.total_permutations_found}</p>
              </div>
              <div>
                <span className="text-sm text-gray-300">Best Yield</span>
                <p className="text-2xl font-bold text-green-400">{results.best_yield_percentage}%</p>
              </div>
              <div>
                <span className="text-sm text-gray-300">Lowest Waste</span>
                <p className="text-2xl font-bold text-green-400">{results.lowest_waste_mm} mm</p>
              </div>
              <div>
                <span className="text-sm text-gray-300">Linear Meters/Roll</span>
                <p className="text-2xl font-bold text-blue-400">{results.material_info.total_linear_meters} m</p>
              </div>
            </div>
          </div>

          {/* Export Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-300">Sort by:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="misty-select"
              >
                <option value="yield">Highest Yield</option>
                <option value="waste">Lowest Waste</option>
                <option value="cost">Lowest Cost</option>
              </select>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={exportToCSV}
                className="misty-button misty-button-secondary"
              >
                📥 Export CSV
              </button>
              <button
                onClick={printResults}
                className="misty-button misty-button-secondary"
              >
                🖨️ Print
              </button>
            </div>
          </div>

          {/* Results Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Pattern</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Used (mm)</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Waste (mm)</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Yield (%)</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Rolls Out</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Linear m</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Weight (kg)</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Cost (AUD)</th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {getSortedPermutations().map((perm, index) => (
                  <tr 
                    key={index} 
                    className={index < 3 ? 'bg-green-900 bg-opacity-20' : ''}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center">
                        {index < 3 && <span className="text-yellow-400 mr-2">⭐</span>}
                        <span className="text-white font-medium">{perm.pattern_description}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-300">{perm.used_width_mm}</td>
                    <td className="px-4 py-3 text-gray-300">{perm.waste_mm}</td>
                    <td className="px-4 py-3">
                      <span className={`font-medium ${perm.yield_percentage >= 95 ? 'text-green-400' : 'text-yellow-400'}`}>
                        {perm.yield_percentage}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-300">{perm.total_finished_rolls}</td>
                    <td className="px-4 py-3 text-gray-300">{perm.linear_meters_per_slit}</td>
                    <td className="px-4 py-3 text-gray-300">{perm.total_pattern_weight_kg}</td>
                    <td className="px-4 py-3 text-gray-300">
                      ${perm.total_cost_all_rolls_aud.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

// Spiral Core Consumption Calculator
const SpiralCoreConsumption = ({ productSpecs, loading, setLoading }) => {
  const [formData, setFormData] = useState({
    product_specification_id: '',
    core_internal_diameter: '',
    wall_thickness_required: '',
    core_length: '',
    quantity: '',
    master_tube_length: ''
  });
  const [results, setResults] = useState(null);

  // Handle product specification selection and auto-populate fields
  const handleSpecificationChange = (specId) => {
    const selectedSpec = productSpecs.find(spec => spec.id === specId);
    
    if (selectedSpec && selectedSpec.specifications) {
      setFormData(prev => ({
        ...prev,
        product_specification_id: specId,
        core_internal_diameter: selectedSpec.specifications.internal_diameter || '',
        wall_thickness_required: selectedSpec.specifications.wall_thickness_required || ''
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        product_specification_id: specId,
        core_internal_diameter: '',
        wall_thickness_required: ''
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Perform enhanced calculations
      const calculationData = {
        ...formData,
        core_internal_diameter: parseFloat(formData.core_internal_diameter),
        wall_thickness_required: parseFloat(formData.wall_thickness_required),
        core_length: parseFloat(formData.core_length),
        quantity: parseInt(formData.quantity),
        master_tube_length: formData.master_tube_length ? parseFloat(formData.master_tube_length) : null
      };

      // Calculate material consumption and linear meters
      const calculations = calculateConsumption(calculationData);
      setResults(calculations);
      toast.success('Consumption calculated successfully');
    } catch (error) {
      console.error('Calculation failed:', error);
      toast.error('Calculation failed');
    } finally {
      setLoading(false);
    }
  };

  // Enhanced calculation function
  const calculateConsumption = (data) => {
    const { core_internal_diameter, wall_thickness_required, core_length, quantity, master_tube_length } = data;
    
    // Calculate outer diameter
    const outer_diameter = core_internal_diameter + (2 * wall_thickness_required);
    
    // Calculate material consumption (approximate based on core volume)
    const inner_radius = core_internal_diameter / 2;
    const outer_radius = outer_diameter / 2;
    const volume_per_core = Math.PI * (Math.pow(outer_radius, 2) - Math.pow(inner_radius, 2)) * core_length;
    const total_volume = volume_per_core * quantity;
    
    // Calculate linear meters of finished tubes
    const linear_meters_per_core = core_length / 1000; // Convert mm to meters
    const total_linear_meters = linear_meters_per_core * quantity;
    
    // Calculate master tubes required if master tube length is provided
    let master_tubes_required = null;
    if (master_tube_length) {
      master_tubes_required = Math.ceil(total_linear_meters / (master_tube_length / 1000));
    }
    
    return {
      calculations: {
        outer_diameter: outer_diameter.toFixed(2),
        volume_per_core: (volume_per_core / 1000000).toFixed(6), // Convert mm³ to cm³
        total_volume: (total_volume / 1000000).toFixed(6), // Convert mm³ to cm³
        linear_meters_per_core: linear_meters_per_core.toFixed(3),
        total_linear_meters: total_linear_meters.toFixed(3),
        master_tubes_required: master_tubes_required
      },
      input_parameters: data
    };
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-300 mb-1">Product Specification</label>
          <select
            value={formData.product_specification_id}
            onChange={(e) => handleSpecificationChange(e.target.value)}
            className="misty-select w-full"
            required
          >
            <option value="">Select spiral paper core specification</option>
            {productSpecs.map(spec => (
              <option key={spec.id} value={spec.id}>{spec.product_name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Internal Diameter (mm) *</label>
          <input
            type="number"
            step="0.1"
            value={formData.core_internal_diameter}
            onChange={(e) => setFormData({...formData, core_internal_diameter: e.target.value})}
            className="misty-input w-full bg-gray-700"
            placeholder="Auto-populated from product spec"
            readOnly
          />
          <p className="text-xs text-gray-500 mt-1">Automatically filled from selected product specification</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Wall Thickness (mm) *</label>
          <input
            type="number"
            step="0.1"
            value={formData.wall_thickness_required}
            onChange={(e) => setFormData({...formData, wall_thickness_required: e.target.value})}
            className="misty-input w-full bg-gray-700"
            placeholder="Auto-populated from product spec"  
            readOnly
          />
          <p className="text-xs text-gray-500 mt-1">Automatically filled from selected product specification</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Core Length (mm) *</label>
          <input
            type="number"
            step="0.1"
            value={formData.core_length}
            onChange={(e) => setFormData({...formData, core_length: e.target.value})}
            className="misty-input w-full"
            placeholder="Enter core length"
            required
          />
          <p className="text-xs text-gray-500 mt-1">Required input for calculation</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Quantity *</label>
          <input
            type="number"
            min="1"
            value={formData.quantity}
            onChange={(e) => setFormData({...formData, quantity: e.target.value})}
            className="misty-input w-full"
            placeholder="Enter quantity needed"
            required
          />
          <p className="text-xs text-gray-500 mt-1">Required input for calculation</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Master Tube Length (mm)</label>
          <input
            type="number"
            step="0.1"
            value={formData.master_tube_length}
            onChange={(e) => setFormData({...formData, master_tube_length: e.target.value})}
            className="misty-input w-full"
            placeholder="Optional: Calculate master tubes required"
          />
          <p className="text-xs text-gray-500 mt-1">Optional: If provided, calculates quantity of master tubes needed</p>
        </div>

        <div>
          <button
            type="submit"
            disabled={loading}
            className="misty-button misty-button-primary w-full"
          >
            {loading ? (
              <>
                <ArrowPathIcon className="animate-spin h-4 w-4 mr-2" />
                Calculating...
              </>
            ) : (
              'Calculate Consumption'
            )}
          </button>
        </div>
      </form>

      {results && (
        <div className="bg-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">🧮 Spiral Core Consumption Results</h3>
          
          {/* Input Summary */}
          <div className="mb-6 p-4 bg-gray-800 rounded-lg">
            <h4 className="text-md font-semibold text-white mb-3">Input Parameters</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Internal Diameter:</span>
                <div className="text-white font-medium">{results.input_parameters.core_internal_diameter} mm</div>
              </div>
              <div>
                <span className="text-gray-400">Wall Thickness:</span>
                <div className="text-white font-medium">{results.input_parameters.wall_thickness_required} mm</div>
              </div>
              <div>
                <span className="text-gray-400">Core Length:</span>
                <div className="text-white font-medium">{results.input_parameters.core_length} mm</div>
              </div>
              <div>
                <span className="text-gray-400">Quantity:</span>
                <div className="text-white font-medium">{results.input_parameters.quantity}</div>
              </div>
            </div>
          </div>

          {/* Calculation Results */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h4 className="text-md font-semibold text-white">📏 Dimensions & Volume</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-300">Outer Diameter:</span>
                  <span className="text-white font-medium">{results.calculations.outer_diameter} mm</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Volume per Core:</span>
                  <span className="text-white font-medium">{results.calculations.volume_per_core} cm³</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Total Volume:</span>
                  <span className="text-white font-medium">{results.calculations.total_volume} cm³</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h4 className="text-md font-semibold text-white">📐 Linear Measurements</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-300">Length per Core:</span>
                  <span className="text-white font-medium">{results.calculations.linear_meters_per_core} m</span>
                </div>
                <div className="flex justify-between font-bold">
                  <span className="text-yellow-400">Total Linear Meters:</span>
                  <span className="text-yellow-400 font-bold">{results.calculations.total_linear_meters} m</span>
                </div>
                {results.calculations.master_tubes_required && (
                  <div className="flex justify-between font-bold">
                    <span className="text-green-400">Master Tubes Required:</span>
                    <span className="text-green-400 font-bold">{results.calculations.master_tubes_required}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Material Usage Summary */}
          <div className="mt-6 p-4 bg-gradient-to-r from-yellow-900/20 to-orange-900/20 rounded-lg border border-yellow-700/30">
            <h4 className="text-md font-semibold text-yellow-400 mb-2">📋 Material Usage Summary</h4>
            <div className="text-white">
              <p>• <strong>{results.input_parameters.quantity}</strong> spiral cores will require <strong>{results.calculations.total_volume} cm³</strong> of material</p>
              <p>• Total finished tube length: <strong>{results.calculations.total_linear_meters} meters</strong></p>
              {results.calculations.master_tubes_required && (
                <p>• Master tubes needed (based on {(results.input_parameters.master_tube_length/1000).toFixed(1)}m length): <strong>{results.calculations.master_tubes_required} tubes</strong></p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Calculators;