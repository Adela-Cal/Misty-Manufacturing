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
      description: 'Optimize master deckle width arrangements with core IDs and sizes',
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
                productSpecs={productSpecs}
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

// Material Permutation Calculator
const MaterialPermutation = ({ productSpecs, loading, setLoading }) => {
  const [formData, setFormData] = useState({
    core_ids: [],
    sizes_to_manufacture: [{ width: '', priority: 1 }],
    master_deckle_width: '',
    acceptable_waste_percentage: 10
  });
  const [results, setResults] = useState(null);

  const coreIds = [...new Set(productSpecs
    .map(spec => spec.specifications?.core_id)
    .filter(Boolean)
  )];

  const addSize = () => {
    setFormData({
      ...formData,
      sizes_to_manufacture: [...formData.sizes_to_manufacture, { width: '', priority: 1 }]
    });
  };

  const removeSize = (index) => {
    const newSizes = formData.sizes_to_manufacture.filter((_, i) => i !== index);
    setFormData({ ...formData, sizes_to_manufacture: newSizes });
  };

  const updateSize = (index, field, value) => {
    const newSizes = formData.sizes_to_manufacture.map((size, i) => 
      i === index ? { ...size, [field]: field === 'priority' ? parseInt(value) : parseFloat(value) } : size
    );
    setFormData({ ...formData, sizes_to_manufacture: newSizes });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await apiHelpers.calculateMaterialPermutation(formData);
      setResults(response.data.data);
      toast.success('Permutation calculated successfully');
    } catch (error) {
      console.error('Calculation failed:', error);
      toast.error('Permutation calculation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="space-y-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Core IDs</label>
            <select
              multiple
              value={formData.core_ids}
              onChange={(e) => setFormData({...formData, core_ids: Array.from(e.target.selectedOptions, option => option.value)})}
              className="misty-select w-full h-32"
            >
              {coreIds.map(coreId => (
                <option key={coreId} value={coreId}>{coreId}</option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">Hold Ctrl/Cmd to select multiple</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Master Deckle Width (mm)</label>
            <input
              type="number"
              step="0.1"
              value={formData.master_deckle_width}
              onChange={(e) => setFormData({...formData, master_deckle_width: parseFloat(e.target.value)})}
              className="misty-input w-full"
              required
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Acceptable Waste Percentage (%)</label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="50"
            value={formData.acceptable_waste_percentage}
            onChange={(e) => setFormData({...formData, acceptable_waste_percentage: parseFloat(e.target.value)})}
            className="misty-input w-full max-w-xs"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Sizes to Manufacture</label>
          {formData.sizes_to_manufacture.map((size, index) => (
            <div key={index} className="flex items-center space-x-2 mb-2">
              <input
                type="number"
                step="0.1"
                placeholder="Width (mm)"
                value={size.width}
                onChange={(e) => updateSize(index, 'width', e.target.value)}
                className="misty-input flex-1"
              />
              <select
                value={size.priority}
                onChange={(e) => updateSize(index, 'priority', e.target.value)}
                className="misty-select w-24"
              >
                <option value={1}>High</option>
                <option value={2}>Medium</option>
                <option value={3}>Low</option>
              </select>
              {formData.sizes_to_manufacture.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeSize(index)}
                  className="text-red-400 hover:text-red-300"
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            onClick={addSize}
            className="text-yellow-400 hover:text-yellow-300 text-sm"
          >
            + Add Size
          </button>
        </div>

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
            'Calculate Permutation'
          )}
        </button>
      </form>

      {results && (
        <div className="bg-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-4">Permutation Results</h3>
          <p className="text-gray-300 mb-4">Found {results.results.total_options_found} arrangement options</p>
          {results.results.permutation_options?.slice(0, 5).map((option, index) => (
            <div key={index} className="bg-gray-800 rounded p-3 mb-2">
              <div className="flex justify-between items-center">
                <span className="text-white">Option {index + 1}</span>
                <span className="text-green-400 font-medium">{option.efficiency.toFixed(1)}% Efficiency</span>
              </div>
              <div className="text-sm text-gray-300 mt-1">
                Waste: {option.waste_percentage.toFixed(1)}%
              </div>
            </div>
          ))}
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
      const response = await apiHelpers.calculateSpiralCoreConsumption({
        ...formData,
        core_internal_diameter: parseFloat(formData.core_internal_diameter),
        core_length: parseFloat(formData.core_length),
        quantity: parseInt(formData.quantity)
      });
      setResults(response.data.data);
      toast.success('Consumption calculated successfully');
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
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-300 mb-1">Product Specification</label>
          <select
            value={formData.product_specification_id}
            onChange={(e) => setFormData({...formData, product_specification_id: e.target.value})}
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
          <label className="block text-sm font-medium text-gray-300 mb-1">Internal Diameter (mm)</label>
          <input
            type="number"
            step="0.1"
            value={formData.core_internal_diameter}
            onChange={(e) => setFormData({...formData, core_internal_diameter: e.target.value})}
            className="misty-input w-full"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Core Length (mm)</label>
          <input
            type="number"
            step="0.1"
            value={formData.core_length}
            onChange={(e) => setFormData({...formData, core_length: e.target.value})}
            className="misty-input w-full"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Quantity</label>
          <input
            type="number"
            min="1"
            value={formData.quantity}
            onChange={(e) => setFormData({...formData, quantity: e.target.value})}
            className="misty-input w-full"
            required
          />
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
        <div className="bg-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-4">Material Consumption Results</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-300">Material:</span>
                <span className="text-white">{results.results.material_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">GSM:</span>
                <span className="text-white">{results.results.gsm}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Layers Required:</span>
                <span className="text-white">{results.results.layers_required}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Outer Diameter:</span>
                <span className="text-white">{results.results.outer_diameter_mm} mm</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-300">Surface Area per Core:</span>
                <span className="text-white">{results.results.surface_area_m2_per_core} m²</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Weight per Core:</span>
                <span className="text-white">{results.results.material_weight_per_core_kg} kg</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Quantity:</span>
                <span className="text-white">{results.results.quantity}</span>
              </div>
              <div className="flex justify-between font-bold">
                <span className="text-yellow-400">Total Material Required:</span>
                <span className="text-yellow-400">{results.results.total_material_weight_kg} kg</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Calculators;