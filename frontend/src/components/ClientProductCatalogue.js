import React, { useState, useEffect } from 'react';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  DocumentDuplicateIcon,
  XMarkIcon,
  CheckIcon,
  PrinterIcon
} from '@heroicons/react/24/outline';

// Helper Components for Inline Editing

// Paper Cores Specifications Component
const PaperCoresSpecifications = ({ formData, handleInputChange, handleSpecificationSelection, productSpecifications }) => (
  <div className="bg-purple-900/20 border border-purple-600/30 rounded-lg p-4">
    <h4 className="text-lg font-semibold text-white mb-4">Paper Cores Specifications</h4>
    
    {/* Core Specifications Selection */}
    <div className="mb-6">
      <label className="block text-sm font-medium text-gray-300 mb-3">
        Core Specifications (From Product Specifications)
      </label>
      <div className="max-h-32 overflow-y-auto border border-gray-600 rounded-lg p-3">
        {productSpecifications && productSpecifications.filter(spec => 
          spec.product_type === 'Spiral Paper Core' || spec.product_type === 'Composite Core'
        ).length > 0 ? (
          <div className="space-y-2">
            {productSpecifications
              .filter(spec => spec.product_type === 'Spiral Paper Core' || spec.product_type === 'Composite Core')
              .map((specification) => (
              <label key={specification.id} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.material_used.includes(specification.id)}
                  onChange={(e) => handleSpecificationSelection(specification.id, e.target.checked)}
                  className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                />
                <span className="text-sm text-gray-300">
                  {specification.product_name} ({specification.product_type})
                  {specification.specifications?.id_mm && ` - ID: ${specification.specifications.id_mm}mm`}
                  {specification.specifications?.wall_thickness && ` - Wall: ${specification.specifications.wall_thickness}mm`}
                </span>
              </label>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No core specifications available. Create Spiral Paper Core or Composite Core specifications first.</p>
        )}
      </div>
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">
          Core ID
          <span className="text-xs text-blue-400 ml-2">(Auto-populated from specification)</span>
        </label>
        <input
          type="text"
          name="core_id"
          value={formData.core_id}
          onChange={handleInputChange}
          className="misty-input w-full bg-gray-600"
          placeholder="Select a core specification above"
          readOnly={formData.material_used.length > 0}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">
          Core Width (mm)
          <span className="text-xs text-yellow-400 ml-2">*Manual Entry Required</span>
        </label>
        <input
          type="text"
          name="core_width"
          value={formData.core_width}
          onChange={handleInputChange}
          className="misty-input w-full"
          placeholder="Enter core width (e.g., 1000)"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">
          Core Thickness (mm)
          <span className="text-xs text-blue-400 ml-2">(Auto-populated from specification)</span>
        </label>
        <input
          type="text"
          name="core_thickness"
          value={formData.core_thickness}
          onChange={handleInputChange}
          className="misty-input w-full bg-gray-600"
          placeholder="Select a core specification above"
          readOnly={formData.material_used.length > 0}
        />
      </div>

      <div className="flex items-center space-y-4">
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            name="strength_quality_important"
            checked={formData.strength_quality_important}
            onChange={handleInputChange}
            className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
          />
          <span className="text-white font-medium">Is strength and Quality important?</span>
        </label>

        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            name="delivery_included"
            checked={formData.delivery_included}
            onChange={handleInputChange}
            className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
          />
          <span className="text-white font-medium">Delivery Included?</span>
        </label>
      </div>
    </div>
  </div>
);

// Production Section Component  
const ProductionSection = ({ formData, handleInputChange, setFormData }) => (
  <div className="bg-emerald-900/20 border border-emerald-600/30 rounded-lg p-4">
    <h4 className="text-lg font-semibold text-white mb-4">Production & Makeready Parameters</h4>
    
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Makeready & Setup */}
      <div className="space-y-4">
        <h5 className="text-md font-medium text-emerald-300 mb-3">Setup & Makeready</h5>
        
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Makeready Allowance (%)
          </label>
          <input
            type="number"
            name="makeready_allowance_percent"
            value={formData.makeready_allowance_percent}
            onChange={handleInputChange}
            className="misty-input w-full"
            placeholder="10"
            min="0"
            step="0.1"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Setup Time (minutes)
          </label>
          <input
            type="number"
            name="setup_time_minutes"
            value={formData.setup_time_minutes}
            onChange={handleInputChange}
            className="misty-input w-full"
            placeholder="30"
            min="0"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Waste Percentage (%)
          </label>
          <input
            type="number"
            name="waste_percentage"
            value={formData.waste_percentage}
            onChange={handleInputChange}
            className="misty-input w-full"
            placeholder="5"
            min="0"
            step="0.1"
          />
        </div>
      </div>

      {/* QC Tolerances */}
      <div className="space-y-4">
        <h5 className="text-md font-medium text-emerald-300 mb-3">QC Tolerances</h5>
        
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            ID Tolerance (±mm)
          </label>
          <input
            type="number"
            value={formData.qc_tolerances.id_tolerance}
            onChange={(e) => setFormData(prev => ({
              ...prev,
              qc_tolerances: {
                ...prev.qc_tolerances,
                id_tolerance: parseFloat(e.target.value) || 0
              }
            }))}
            className="misty-input w-full"
            placeholder="0.5"
            min="0"
            step="0.1"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            OD Tolerance (±mm)
          </label>
          <input
            type="number"
            value={formData.qc_tolerances.od_tolerance}
            onChange={(e) => setFormData(prev => ({
              ...prev,
              qc_tolerances: {
                ...prev.qc_tolerances,
                od_tolerance: parseFloat(e.target.value) || 0
              }
            }))}
            className="misty-input w-full"
            placeholder="0.5"
            min="0"
            step="0.1"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Wall Tolerance (±mm)
          </label>
          <input
            type="number"
            value={formData.qc_tolerances.wall_tolerance}
            onChange={(e) => setFormData(prev => ({
              ...prev,
              qc_tolerances: {
                ...prev.qc_tolerances,
                wall_tolerance: parseFloat(e.target.value) || 0
              }
            }))}
            className="misty-input w-full"
            placeholder="0.1"
            min="0"
            step="0.01"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Inspection Interval (min)
          </label>
          <input
            type="number"
            name="inspection_interval_minutes"
            value={formData.inspection_interval_minutes}
            onChange={handleInputChange}
            className="misty-input w-full"
            placeholder="60"
            min="1"
          />
        </div>
      </div>

      {/* Packing & Notes */}
      <div className="space-y-4">
        <h5 className="text-md font-medium text-emerald-300 mb-3">Packing & Instructions</h5>
        
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Tubes per Carton
          </label>
          <input
            type="number"
            name="tubes_per_carton"
            value={formData.tubes_per_carton}
            onChange={handleInputChange}
            className="misty-input w-full"
            placeholder="50"
            min="1"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Cartons per Pallet
          </label>
          <input
            type="number"
            name="cartons_per_pallet"
            value={formData.cartons_per_pallet}
            onChange={handleInputChange}
            className="misty-input w-full"
            placeholder="20"
            min="1"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Special Tooling Notes
          </label>
          <textarea
            name="special_tooling_notes"
            value={formData.special_tooling_notes}
            onChange={handleInputChange}
            className="misty-input w-full h-16 resize-none"
            placeholder="Mandrel size, special tooling requirements..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Packing Instructions
          </label>
          <textarea
            name="packing_instructions"
            value={formData.packing_instructions}
            onChange={handleInputChange}
            className="misty-input w-full h-16 resize-none"
            placeholder="Special handling, customer requirements..."
          />
        </div>
      </div>
    </div>
  </div>
);

// Consumables Section Component
const ConsumablesSection = ({ formData, setFormData, handleAddConsumables, removeConsumable }) => (
  <div className="bg-gray-900/50 border border-gray-600/30 rounded-lg p-4">
    <div className="flex items-center justify-between mb-4">
      <h4 className="text-lg font-semibold text-white">Consumables</h4>
      <button
        type="button"
        onClick={handleAddConsumables}
        className="misty-button misty-button-secondary flex items-center text-sm"
      >
        <PlusIcon className="h-4 w-4 mr-2" />
        Add Consumables
      </button>
    </div>

    {formData.consumables.length > 0 ? (
      <div className="space-y-3">
        {formData.consumables.map((consumable) => (
          <div key={consumable.id} className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
            <div className="flex-1">
              <div className="font-medium text-white">{consumable.specification_name}</div>
              <div className="text-sm text-gray-400">
                Type: {consumable.product_type} | Unit: {consumable.measurement_unit}
                {consumable.quantity_cores_per_carton && ` | ${consumable.quantity_cores_per_carton} cores per carton`}
              </div>
            </div>
            <button
              type="button"
              onClick={() => removeConsumable(consumable.id)}
              className="text-red-400 hover:text-red-300 ml-4"
            >
              <TrashIcon className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    ) : (
      <div className="text-center py-6 text-gray-400">
        <p className="text-sm">No consumables added yet.</p>
        <p className="text-xs">Click "Add Consumables" to add packaging materials like cartons, tapes, and bags.</p>
      </div>
    )}
  </div>
);

// Consumables Selector Component
const ConsumablesSelector = ({ productSpecs, productSection, onAddConsumable, onCancel }) => {
  const [selectedSpec, setSelectedSpec] = useState(null);
  const [measurementUnit, setMeasurementUnit] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [quantityCoresPerCarton, setQuantityCoresPerCarton] = useState('');

  const handleSpecSelection = (spec) => {
    setSelectedSpec(spec);
    setMeasurementUnit('');
    setQuantity(1);
    setQuantityCoresPerCarton('');
  };

  const getMeasurementOptions = () => {
    if (!selectedSpec) return [];

    if (productSection === 'finished_goods') {
      // For finished goods: cartons, tape, bags all have Per unit, Per order, Per Meter
      return ['Per Unit', 'Per Order', 'Per Meter'];
    } else if (productSection === 'paper_cores') {
      // For paper cores: different options based on consumable type
      if (selectedSpec.product_type === 'Cardboard Boxes') {
        return ['Quantity of Cores Per Carton'];
      } else if (selectedSpec.product_type === 'Tapes') {
        return ['Per Meter'];
      } else if (selectedSpec.product_type === 'Plastic Bags') {
        return ['Per Quantity of Cores'];
      }
    }
    return [];
  };

  const handleAdd = () => {
    if (!selectedSpec || !measurementUnit) {
      toast.error('Please select a consumable and measurement unit');
      return;
    }

    const coresPerCarton = measurementUnit === 'Quantity of Cores Per Carton' ? parseInt(quantityCoresPerCarton) || null : null;
    onAddConsumable(selectedSpec, measurementUnit, quantity, coresPerCarton);
  };

  return (
    <div className="space-y-6">
      {/* Available Consumables */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-3">
          Select Consumable Type
        </label>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {productSpecs.length > 0 ? (
            productSpecs.map((spec) => (
              <div
                key={spec.id}
                className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                  selectedSpec?.id === spec.id
                    ? 'border-yellow-400 bg-yellow-400/10'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
                onClick={() => handleSpecSelection(spec)}
              >
                <div className="font-medium text-white">{spec.product_name}</div>
                <div className="text-sm text-gray-400">{spec.product_type}</div>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-400">No consumable specifications available. Create specifications for Cardboard Boxes, Tapes, or Plastic Bags first.</p>
          )}
        </div>
      </div>

      {/* Measurement Unit Options */}
      {selectedSpec && (
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-3">
            Measurement Unit
          </label>
          <div className="space-y-2">
            {getMeasurementOptions().map((option) => (
              <label key={option} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="radio"
                  name="measurement_unit"
                  value={option}
                  checked={measurementUnit === option}
                  onChange={(e) => setMeasurementUnit(e.target.value)}
                  className="text-yellow-400"
                />
                <span className="text-white">{option}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Additional Fields */}
      {measurementUnit === 'Quantity of Cores Per Carton' && (
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Quantity of Cores Per Carton *
          </label>
          <input
            type="number"
            min="1"
            value={quantityCoresPerCarton}
            onChange={(e) => setQuantityCoresPerCarton(e.target.value)}
            className="misty-input w-32"
            placeholder="50"
            required
          />
        </div>
      )}

      {measurementUnit && measurementUnit !== 'Quantity of Cores Per Carton' && (
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Quantity
          </label>
          <input
            type="number"
            min="1"
            value={quantity}
            onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
            className="misty-input w-32"
            placeholder="1"
          />
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end space-x-3 pt-4 border-t border-gray-700">
        <button
          type="button"
          onClick={onCancel}
          className="misty-button misty-button-secondary"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleAdd}
          className="misty-button misty-button-primary"
          disabled={!selectedSpec || !measurementUnit}
        >
          Add Consumable
        </button>
      </div>
    </div>
  );
};

const ClientProductCatalogue = ({ clientId, onClose }) => {
  const [products, setProducts] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [clients, setClients] = useState([]);
  const [productSpecifications, setProductSpecifications] = useState([]);
  const [currentClient, setCurrentClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [showCopyModal, setShowCopyModal] = useState(false);
  const [copyProductId, setCopyProductId] = useState(null);
  const [targetClientId, setTargetClientId] = useState('');
  const [showConsumablesModal, setShowConsumablesModal] = useState(false);
  const [selectedProductForEdit, setSelectedProductForEdit] = useState(null);
  const [isInlineEditing, setIsInlineEditing] = useState(false);
  
  const [formData, setFormData] = useState({
    product_type: 'finished_goods',
    product_code: '',
    product_description: '',
    price_ex_gst: '',
    minimum_order_quantity: '',
    consignment: false,
    // Paper cores specific
    material_used: [],
    core_id: '',
    core_width: '',
    core_thickness: '',
    strength_quality_important: false,
    delivery_included: false,
    // Services and Deliveries specific
    service_delivery_subtype: 'services', // 'services' or 'deliveries'
    service_job_description: '',
    service_time_required: '',
    service_price: '',
    service_functions: [],
    delivery_from_address: '',
    delivery_to_address: '',
    delivery_unit_type: 'Pallets',
    delivery_price_per_unit: '',
    // Consumables
    consumables: [],
    // Shared Product functionality
    is_shared_product: false,
    shared_with_clients: [],
    // Production & Makeready Information
    makeready_allowance_percent: 10, // Default 10%
    setup_time_minutes: 30, // Default setup time
    waste_percentage: 5, // Default waste %
    qc_tolerances: {
      id_tolerance: 0.5, // mm
      od_tolerance: 0.5, // mm  
      wall_tolerance: 0.1 // mm
    },
    inspection_interval_minutes: 60, // Default QC check interval
    tubes_per_carton: 50, // Default packing
    cartons_per_pallet: 20, // Default palletization
    special_tooling_notes: '',
    packing_instructions: ''
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    loadData();
  }, [clientId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [productsRes, materialsRes, clientsRes, productSpecsRes, currentClientRes] = await Promise.all([
        apiHelpers.getClientCatalogue(clientId),
        apiHelpers.getMaterials(),
        apiHelpers.getClients(),
        apiHelpers.getProductSpecifications(),
        apiHelpers.getClient(clientId)
      ]);
      
      setProducts(productsRes.data);
      setMaterials(materialsRes.data);
      setClients(clientsRes.data.filter(client => client.id !== clientId));
      setProductSpecifications(productSpecsRes.data);
      setCurrentClient(currentClientRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
      toast.error('Failed to load product catalogue data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedProduct(null);
    setFormData({
      product_type: 'finished_goods',
      product_code: '',
      product_description: '',
      price_ex_gst: '',
      minimum_order_quantity: '',
      consignment: false,
      material_used: [],
      core_id: '',
      core_width: '',
      core_thickness: '',
      strength_quality_important: false,
      delivery_included: false,
      service_delivery_subtype: 'services',
      service_job_description: '',
      service_time_required: '',
      service_price: '',
      service_functions: [],
      delivery_from_address: '',
      delivery_to_address: '',
      delivery_unit_type: 'Pallets',
      delivery_price_per_unit: '',
      consumables: [],
      is_shared_product: false,
      shared_with_clients: [],
      makeready_allowance_percent: 10,
      setup_time_minutes: 30,
      waste_percentage: 5,
      qc_tolerances: {
        id_tolerance: 0.5,
        od_tolerance: 0.5,
        wall_tolerance: 0.1
      },
      inspection_interval_minutes: 60,
      tubes_per_carton: 50,
      cartons_per_pallet: 20,
      special_tooling_notes: '',
      packing_instructions: ''
    });
    setErrors({});
    setShowModal(true);
  };

  const handleEdit = (product) => {
    setSelectedProduct(product);
    setFormData({
      product_type: product.product_type,
      product_code: product.product_code,
      product_description: product.product_description,
      price_ex_gst: product.price_ex_gst.toString(),
      minimum_order_quantity: product.minimum_order_quantity.toString(),
      consignment: product.consignment || false,
      material_used: product.material_used || [],
      core_id: product.core_id || '',
      core_width: product.core_width || '',
      core_thickness: product.core_thickness || '',
      strength_quality_important: product.strength_quality_important || false,
      delivery_included: product.delivery_included || false,
      consumables: product.consumables || [],
      is_shared_product: product.is_shared_product || false,
      shared_with_clients: product.shared_with_clients || [],
      makeready_allowance_percent: product.makeready_allowance_percent || 10,
      setup_time_minutes: product.setup_time_minutes || 30,
      waste_percentage: product.waste_percentage || 5,
      qc_tolerances: product.qc_tolerances || {
        id_tolerance: 0.5,
        od_tolerance: 0.5,
        wall_tolerance: 0.1
      },
      inspection_interval_minutes: product.inspection_interval_minutes || 60,
      tubes_per_carton: product.tubes_per_carton || 50,
      cartons_per_pallet: product.cartons_per_pallet || 20,
      special_tooling_notes: product.special_tooling_notes || '',
      packing_instructions: product.packing_instructions || ''
    });
    setErrors({});
    setShowModal(true);
  };

  const handleDelete = async (product) => {
    if (window.confirm(`Are you sure you want to delete "${product.product_code}"?`)) {
      try {
        await apiHelpers.deleteClientProduct(clientId, product.id);
        toast.success('Product deleted successfully');
        loadData();
      } catch (error) {
        console.error('Failed to delete product:', error);
        toast.error('Failed to delete product');
      }
    }
  };

  const handleProductDoubleClick = (product) => {
    setSelectedProductForEdit(product);
    setSelectedProduct(product);
    setFormData({
      product_type: product.product_type,
      product_code: product.product_code,
      product_description: product.product_description,
      price_ex_gst: product.price_ex_gst.toString(),
      minimum_order_quantity: product.minimum_order_quantity.toString(),
      consignment: product.consignment,
      material_used: product.material_used || [],
      core_id: product.core_id || '',
      core_width: product.core_width || '',
      core_thickness: product.core_thickness || '',
      strength_quality_important: product.strength_quality_important || false,
      delivery_included: product.delivery_included || false,
      consumables: product.consumables || [],
      is_shared_product: product.is_shared_product || false,
      shared_with_clients: product.shared_with_clients || [],
      makeready_allowance_percent: product.makeready_allowance_percent || 10,
      setup_time_minutes: product.setup_time_minutes || 30,
      waste_percentage: product.waste_percentage || 5,
      qc_tolerances: product.qc_tolerances || {
        id_tolerance: 0.5,
        od_tolerance: 0.5,
        wall_tolerance: 0.1
      },
      inspection_interval_minutes: product.inspection_interval_minutes || 60,
      tubes_per_carton: product.tubes_per_carton || 50,
      cartons_per_pallet: product.cartons_per_pallet || 20,
      special_tooling_notes: product.special_tooling_notes || '',
      packing_instructions: product.packing_instructions || ''
    });
    setIsInlineEditing(true);
    setErrors({});
  };

  const handleInlineSave = async () => {
    console.log('handleInlineSave called');
    console.log('Form data before save:', formData);
    
    // Removed validateForm check since function doesn't exist
    console.log('Starting save process - no validation required');

    try {
      if (isInlineEditing && selectedProductForEdit) {
        console.log('Preparing submitData...');
        
        const submitData = {
          product_type: formData.product_type,
          product_code: formData.product_code,
          product_description: formData.product_description,
          price_ex_gst: parseFloat(formData.price_ex_gst) || 0,
          minimum_order_quantity: parseInt(formData.minimum_order_quantity) || 1,
          consignment: formData.consignment,
          material_used: formData.product_type === 'paper_cores' ? formData.material_used : [],
          core_id: formData.product_type === 'paper_cores' ? formData.core_id || null : null,
          core_width: formData.product_type === 'paper_cores' ? formData.core_width || null : null,
          core_thickness: formData.product_type === 'paper_cores' ? formData.core_thickness || null : null,
          strength_quality_important: formData.product_type === 'paper_cores' ? formData.strength_quality_important : false,
          delivery_included: formData.product_type === 'paper_cores' ? formData.delivery_included : false,
          consumables: formData.consumables || [],
          makeready_allowance_percent: parseFloat(formData.makeready_allowance_percent) || 0,
          setup_time_minutes: parseInt(formData.setup_time_minutes) || 0,
          waste_percentage: parseFloat(formData.waste_percentage) || 0,
          qc_tolerances: formData.qc_tolerances || { id_tolerance: 0, od_tolerance: 0, wall_tolerance: 0 },
          inspection_interval_minutes: parseInt(formData.inspection_interval_minutes) || 0,
          tubes_per_carton: parseInt(formData.tubes_per_carton) || 0,
          cartons_per_pallet: parseInt(formData.cartons_per_pallet) || 0,
          special_tooling_notes: formData.special_tooling_notes || '',
          packing_instructions: formData.packing_instructions || '',
          is_shared_product: formData.is_shared_product || false,
          shared_with_clients: formData.shared_with_clients || [],
        };

        console.log('Submit data with Production & Makeready parameters:', {
          makeready_allowance_percent: submitData.makeready_allowance_percent,
          setup_time_minutes: submitData.setup_time_minutes,
          waste_percentage: submitData.waste_percentage,
          tubes_per_carton: submitData.tubes_per_carton,
          special_tooling_notes: submitData.special_tooling_notes
        });
        
        console.log('Making API call to update product...');
        console.log('API Request details:', {
          clientId,
          productId: selectedProductForEdit.id,
          submitData: submitData
        });
        
        const apiResponse = await apiHelpers.updateClientProduct(clientId, selectedProductForEdit.id, submitData);
        console.log('API Response:', apiResponse.data);
        
        console.log('Product updated successfully');
        toast.success('Product updated successfully');
        
        // Before reloading, let's verify what was actually saved
        console.log('Verifying saved data by fetching updated product...');
        try {
          const verifyResponse = await apiHelpers.getClientProduct(clientId, selectedProductForEdit.id);
          const updatedProduct = verifyResponse.data?.data || verifyResponse.data;
          console.log('Product after save verification:', {
            tubes_per_carton: updatedProduct.tubes_per_carton,
            makeready_allowance_percent: updatedProduct.makeready_allowance_percent,
            setup_time_minutes: updatedProduct.setup_time_minutes,
            waste_percentage: updatedProduct.waste_percentage,
            special_tooling_notes: updatedProduct.special_tooling_notes
          });
        } catch (verifyError) {
          console.error('Failed to verify saved product:', verifyError);
        }
        
        setIsInlineEditing(false);
        setSelectedProductForEdit(null);
        
        // Reload products to refresh the list
        console.log('Reloading products...');
        await loadData();
        
        console.log('Data reload completed');
      } else {
        console.log('Not in inline editing mode or no product selected');
      }
    } catch (error) {
      console.error('Error saving product:', error);
      console.error('Error details:', error.response?.data);
      toast.error('Failed to save product: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleInlineCancel = () => {
    setSelectedProductForEdit(null);
    setSelectedProduct(null);
    setIsInlineEditing(false);
    setFormData({
      product_type: 'finished_goods',
      product_code: '',
      product_description: '',
      price_ex_gst: '',
      minimum_order_quantity: '',
      consignment: false,
      material_used: [],
      core_id: '',
      core_width: '',
      core_thickness: '',
      strength_quality_important: false,
      delivery_included: false,
      consumables: [],
      is_shared_product: false,
      shared_with_clients: [],
      makeready_allowance_percent: 10,
      setup_time_minutes: 30,
      waste_percentage: 5,
      qc_tolerances: {
        id_tolerance: 0.5,
        od_tolerance: 0.5,
        wall_tolerance: 0.1
      },
      inspection_interval_minutes: 60,
      tubes_per_carton: 50,
      cartons_per_pallet: 20,
      special_tooling_notes: '',
      packing_instructions: ''
    });
    setErrors({});
  };

  const handleInlineDelete = async () => {
    if (!selectedProductForEdit) return;

    if (window.confirm('Are you sure you want to delete this product? This action cannot be undone.')) {
      try {
        await apiHelpers.deleteClientProduct(clientId, selectedProductForEdit.id);
        toast.success('Product deleted successfully');
        handleInlineCancel();
        loadData();
      } catch (error) {
        console.error('Failed to delete product:', error);
        toast.error('Failed to delete product');
      }
    }
  };

  const handleInlineDuplicate = () => {
    if (!selectedProductForEdit) return;
    setCopyProductId(selectedProductForEdit.id);
    setTargetClientId('');
    setShowCopyModal(true);
  };

  const handleCopy = (productId) => {
    setCopyProductId(productId);
    setTargetClientId('');
    setShowCopyModal(true);
  };

  const handleCopyConfirm = async () => {
    if (!targetClientId) {
      toast.error('Please select a target client');
      return;
    }

    try {
      await apiHelpers.copyClientProduct(clientId, copyProductId, targetClientId);
      toast.success('Product copied successfully');
      setShowCopyModal(false);
    } catch (error) {
      console.error('Failed to copy product:', error);
      toast.error('Failed to copy product');
    }
  };

  const handlePrint = (product) => {
    const printWindow = window.open('', '_blank');
    const clientName = currentClient?.company_name || 'Client';
    
    const printContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Product Quote - ${product.product_code}</title>
        <style>
          body {
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
            color: #333;
          }
          .header {
            text-align: center;
            border-bottom: 2px solid #333;
            padding-bottom: 20px;
            margin-bottom: 30px;
          }
          .company-name {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
          }
          .quote-title {
            font-size: 18px;
            color: #666;
          }
          .product-info {
            margin-bottom: 30px;
          }
          .product-info h2 {
            background-color: #f5f5f5;
            padding: 10px;
            margin: 0 0 20px 0;
            border-left: 4px solid #007bff;
          }
          .info-row {
            display: flex;
            margin-bottom: 10px;
            border-bottom: 1px dotted #ccc;
            padding-bottom: 5px;
          }
          .info-label {
            font-weight: bold;
            width: 200px;
            flex-shrink: 0;
          }
          .info-value {
            flex: 1;
          }
          .price-section {
            background-color: #f8f9fa;
            border: 2px solid #007bff;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin-top: 20px;
          }
          .price {
            font-size: 28px;
            font-weight: bold;
            color: #007bff;
            margin-bottom: 10px;
          }
          .price-note {
            color: #666;
            font-style: italic;
          }
          .materials-section {
            margin-top: 30px;
          }
          .materials-list {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
          }
          .material-item {
            margin-bottom: 5px;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
          }
          .footer {
            margin-top: 40px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border-top: 1px solid #ccc;
            padding-top: 20px;
          }
          @media print {
            body { margin: 0; }
            .no-print { display: none; }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="company-name">${clientName}</div>
          <div class="quote-title">Product Quote</div>
        </div>

        <div class="product-info">
          <h2>Product Information</h2>
          <div class="info-row">
            <div class="info-label">Product Code:</div>
            <div class="info-value">${product.product_code}</div>
          </div>
          <div class="info-row">
            <div class="info-label">Description:</div>
            <div class="info-value">${product.product_description}</div>
          </div>
          <div class="info-row">
            <div class="info-label">Product Type:</div>
            <div class="info-value">${product.product_type === 'finished_goods' ? 'Finished Goods' : 'Paper Cores'}</div>
          </div>
          <div class="info-row">
            <div class="info-label">Minimum Order Quantity:</div>
            <div class="info-value">${product.minimum_order_quantity} units</div>
          </div>
          <div class="info-row">
            <div class="info-label">Consignment:</div>
            <div class="info-value">${product.consignment ? 'Yes' : 'No'}</div>
          </div>
          ${product.product_type === 'paper_cores' && product.core_id ? `
          <div class="info-row">
            <div class="info-label">Core ID:</div>
            <div class="info-value">${product.core_id}</div>
          </div>` : ''}
          ${product.product_type === 'paper_cores' && product.core_width ? `
          <div class="info-row">
            <div class="info-label">Core Width:</div>
            <div class="info-value">${product.core_width}</div>
          </div>` : ''}
          ${product.product_type === 'paper_cores' && product.core_thickness ? `
          <div class="info-row">
            <div class="info-label">Core Thickness:</div>
            <div class="info-value">${product.core_thickness}</div>
          </div>` : ''}
          ${product.product_type === 'paper_cores' ? `
          <div class="info-row">
            <div class="info-label">Strength & Quality Important:</div>
            <div class="info-value">${product.strength_quality_important ? 'Yes' : 'No'}</div>
          </div>
          <div class="info-row">
            <div class="info-label">Delivery Included:</div>
            <div class="info-value">${product.delivery_included ? 'Yes' : 'No'}</div>
          </div>` : ''}
        </div>

        ${product.product_type === 'paper_cores' && product.material_used && product.material_used.length > 0 ? `
        <div class="materials-section">
          <h2>Materials Used</h2>
          <div class="materials-list">
            ${materials.filter(m => product.material_used.includes(m.id))
              .map(material => `
                <div class="material-item">
                  ${material.supplier} - ${material.product_code}${material.gsm ? ` (${material.gsm} GSM)` : ''}
                </div>
              `).join('')}
          </div>
        </div>` : ''}

        <div class="price-section">
          <div class="price">$${product.price_ex_gst.toFixed(2)}</div>
          <div class="price-note">Price ex GST per unit</div>
        </div>

        <div class="footer">
          <p>Generated on ${new Date().toLocaleDateString()} at ${new Date().toLocaleTimeString()}</p>
          <p>This quote is valid for 30 days from the date of generation.</p>
        </div>

        <script>
          window.onload = function() {
            window.print();
            window.onafterprint = function() {
              window.close();
            }
          }
        </script>
      </body>
      </html>
    `;

    printWindow.document.write(printContent);
    printWindow.document.close();
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleMaterialChange = (materialId, isSelected) => {
    setFormData(prev => ({
      ...prev,
      material_used: isSelected 
        ? [...prev.material_used, materialId]
        : prev.material_used.filter(id => id !== materialId)
    }));
  };

  const handleSpecificationSelection = (specificationId, checked) => {
    if (checked) {
      // Find the selected specification
      const selectedSpec = productSpecifications.find(spec => spec.id === specificationId);
      if (selectedSpec) {
        // Auto-populate Core ID and Core Thickness from the specification
        setFormData(prev => ({
          ...prev,
          material_used: [...prev.material_used, specificationId],
          core_id: selectedSpec.specifications?.id_mm || selectedSpec.core_id || prev.core_id,
          core_thickness: selectedSpec.specifications?.wall_thickness || selectedSpec.core_thickness || prev.core_thickness
        }));
      } else {
        // Just add to material_used if specification not found
        setFormData(prev => ({
          ...prev,
          material_used: [...prev.material_used, specificationId]
        }));
      }
    } else {
      setFormData(prev => ({
        ...prev,
        material_used: prev.material_used.filter(id => id !== specificationId)
      }));
    }
  };

  // Consumables handlers
  const handleAddConsumables = () => {
    setShowConsumablesModal(true);
  };

  const addConsumable = (specification, measurementUnit, quantity = 1, quantityCoresPerCarton = null) => {
    const newConsumable = {
      id: Date.now(), // temporary ID for frontend
      specification_id: specification.id,
      specification_name: specification.product_name,
      product_type: specification.product_type,
      measurement_unit: measurementUnit,
      quantity: quantity,
      quantity_cores_per_carton: quantityCoresPerCarton,
      product_section: formData.product_type // 'finished_goods' or 'paper_cores'
    };

    setFormData(prev => ({
      ...prev,
      consumables: [...prev.consumables, newConsumable]
    }));
    
    setShowConsumablesModal(false);
    toast.success(`${specification.product_name} added as consumable`);
  };

  const removeConsumable = (consumableId) => {
    setFormData(prev => ({
      ...prev,
      consumables: prev.consumables.filter(c => c.id !== consumableId)
    }));
  };

  // Get consumable product specifications (Cardboard Boxes, Plastic Bags, Tapes)
  const getConsumableSpecs = () => {
    return productSpecifications.filter(spec => 
      ['Cardboard Boxes', 'Plastic Bags', 'Tapes'].includes(spec.product_type)
    );
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.product_code.trim()) {
      newErrors.product_code = 'Product code is required';
    }
    
    if (!formData.product_description.trim()) {
      newErrors.product_description = 'Product description is required';
    }
    
    if (!formData.price_ex_gst || parseFloat(formData.price_ex_gst) <= 0) {
      newErrors.price_ex_gst = 'Price must be greater than 0';
    }
    
    if (!formData.minimum_order_quantity || parseInt(formData.minimum_order_quantity) <= 0) {
      newErrors.minimum_order_quantity = 'Minimum order quantity must be greater than 0';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast.error('Please fix the errors below');
      return;
    }
    
    try {
      const submitData = {
        product_type: formData.product_type,
        product_code: formData.product_code,
        product_description: formData.product_description,
        price_ex_gst: parseFloat(formData.price_ex_gst),
        minimum_order_quantity: parseInt(formData.minimum_order_quantity),
        consignment: formData.consignment,
        material_used: formData.product_type === 'paper_cores' ? formData.material_used : [],
        core_id: formData.product_type === 'paper_cores' ? formData.core_id || null : null,
        core_width: formData.product_type === 'paper_cores' ? formData.core_width || null : null,
        core_thickness: formData.product_type === 'paper_cores' ? formData.core_thickness || null : null,
        strength_quality_important: formData.product_type === 'paper_cores' ? formData.strength_quality_important : false,
        delivery_included: formData.product_type === 'paper_cores' ? formData.delivery_included : false,
        consumables: formData.consumables,
        is_shared_product: formData.is_shared_product,
        shared_with_clients: formData.shared_with_clients,
        makeready_allowance_percent: formData.makeready_allowance_percent,
        setup_time_minutes: formData.setup_time_minutes,
        waste_percentage: formData.waste_percentage,
        qc_tolerances: formData.qc_tolerances,
        inspection_interval_minutes: formData.inspection_interval_minutes,
        tubes_per_carton: formData.tubes_per_carton,
        cartons_per_pallet: formData.cartons_per_pallet,
        special_tooling_notes: formData.special_tooling_notes,
        packing_instructions: formData.packing_instructions
      };

      if (selectedProduct) {
        await apiHelpers.updateClientProduct(clientId, selectedProduct.id, submitData);
        toast.success('Product updated successfully');
      } else {
        await apiHelpers.createClientProduct(clientId, submitData);
        toast.success('Product created successfully');
      }
      
      setShowModal(false);
      setSelectedProduct(null);
      // Reset form data
      setFormData({
        product_type: 'finished_goods',
        product_code: '',
        product_description: '',
        price_ex_gst: '',
        minimum_order_quantity: '',
        consignment: false,
        material_used: [],
        core_id: '',
        core_width: '',
        core_thickness: '',
        strength_quality_important: false,
        delivery_included: false,
        consumables: [],
        is_shared_product: false,
        shared_with_clients: [],
        makeready_allowance_percent: 10,
        setup_time_minutes: 30,
        waste_percentage: 5,
        qc_tolerances: {
          id_tolerance: 0.5,
          od_tolerance: 0.5,
          wall_tolerance: 0.1
        },
        inspection_interval_minutes: 60,
        tubes_per_carton: 50,
        cartons_per_pallet: 20,
        special_tooling_notes: '',
        packing_instructions: ''
      });
      loadData();
    } catch (error) {
      console.error('Failed to save product:', error);
      const message = error.response?.data?.detail || 'Failed to save product';
      toast.error(message);
    }
  };

  if (loading) {
    return (
      <div className="modal-overlay">
        <div className="modal-content max-w-6xl max-h-[90vh] overflow-y-auto">
          <div className="p-8">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-700 rounded w-1/3 mb-8"></div>
              <div className="space-y-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-16 bg-gray-700 rounded"></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content max-w-6xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">
              Client Product Catalogue
            </h2>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleCreate}
                className="misty-button misty-button-primary flex items-center"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Add Product
              </button>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
          </div>

          {/* Products Table */}
          {products.length > 0 ? (
            <div className="misty-table">
              <table className="w-full">
                <thead>
                  <tr>
                    <th>Product Code</th>
                    <th>Description</th>
                    <th>Type</th>
                    <th>Price (ex GST)</th>
                    <th>Min Qty</th>
                    <th>Consignment</th>
                    <th>Shared</th>
                  </tr>
                </thead>
                <tbody>
                  {products.map((product) => (
                    <tr 
                      key={product.id}
                      className={`cursor-pointer hover:bg-gray-700/50 transition-colors ${
                        selectedProductForEdit?.id === product.id ? 'bg-blue-900/30 ring-2 ring-blue-500' : ''
                      }`}
                      onDoubleClick={() => handleProductDoubleClick(product)}
                      title="Double-click to edit"
                    >
                      <td className="font-medium">{product.product_code}</td>
                      <td>{product.product_description}</td>
                      <td>
                        <span className={`text-xs px-2 py-1 rounded text-white ${
                          product.product_type === 'finished_goods' 
                            ? 'bg-blue-600' 
                            : 'bg-purple-600'
                        }`}>
                          {product.product_type === 'finished_goods' 
                            ? 'Finished Goods' 
                            : 'Paper Cores'
                          }
                        </span>
                      </td>
                      <td className="text-yellow-400 font-medium">
                        ${product.price_ex_gst.toFixed(2)}
                      </td>
                      <td>{product.minimum_order_quantity}</td>
                      <td>
                        {product.consignment ? (
                          <CheckIcon className="h-4 w-4 text-green-400" />
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td>
                        {product.is_shared_product ? (
                          <div className="flex items-center space-x-1">
                            <CheckIcon className="h-4 w-4 text-green-400" />
                            <span className="text-xs text-green-400">
                              {product.shared_with_clients?.length || 0} clients
                            </span>
                          </div>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="mx-auto h-12 w-12 text-gray-400 mb-4">📦</div>
              <h3 className="text-sm font-medium text-gray-300">
                No products in catalogue
              </h3>
              <p className="mt-1 text-sm text-gray-400">
                Get started by adding your first product.
              </p>
              <div className="mt-6">
                <button
                  onClick={handleCreate}
                  className="misty-button misty-button-primary"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Add Product
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Action Bar - Shows when product is selected for editing */}
        {isInlineEditing && selectedProductForEdit && (
          <div className="fixed bottom-0 left-0 right-0 bg-gray-800 border-t border-gray-700 p-4 shadow-lg z-50">
            <div className="max-w-7xl mx-auto flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="text-white font-medium">
                  Editing: {selectedProductForEdit.product_code} - {selectedProductForEdit.product_description}
                </div>
                <div className="text-xs text-gray-400">
                  Double-click another product to switch, or use the actions below
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <button
                  onClick={handleInlineSave}
                  className="misty-button misty-button-primary flex items-center"
                >
                  <CheckIcon className="h-4 w-4 mr-2" />
                  Save
                </button>
                <button
                  onClick={handleInlineCancel}
                  className="misty-button misty-button-secondary flex items-center"
                >
                  <XMarkIcon className="h-4 w-4 mr-2" />
                  Cancel
                </button>
                <button
                  onClick={handleInlineDelete}
                  className="misty-button bg-red-600 hover:bg-red-700 text-white flex items-center"
                >
                  <TrashIcon className="h-4 w-4 mr-2" />
                  Delete
                </button>
                <button
                  onClick={handleInlineDuplicate}
                  className="misty-button bg-blue-600 hover:bg-blue-700 text-white flex items-center"
                >
                  <DocumentDuplicateIcon className="h-4 w-4 mr-2" />
                  Duplicate
                </button>
                <button
                  onClick={() => handlePrint(selectedProductForEdit)}
                  className="misty-button bg-green-600 hover:bg-green-700 text-white flex items-center"
                >
                  <PrinterIcon className="h-4 w-4 mr-2" />
                  Print
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Inline Edit Form - Shows when product is selected */}
        {isInlineEditing && selectedProductForEdit && (
          <div className="mt-8 mb-20 bg-gray-800 rounded-lg p-6 border-2 border-blue-500">
            <div className="mb-6">
              <h3 className="text-xl font-bold text-white mb-2">
                Edit Product: {selectedProductForEdit.product_code}
              </h3>
              <p className="text-gray-400 text-sm">
                Make your changes below and click Save to update the product.
              </p>
            </div>

            <form className="space-y-6">
              {/* Basic Product Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Product Type
                  </label>
                  <select
                    name="product_type"
                    value={formData.product_type}
                    onChange={handleInputChange}
                    className="misty-select w-full"
                    required
                  >
                    <option value="finished_goods">Finished Goods</option>
                    <option value="paper_cores">Paper Cores</option>
                    <option value="services_and_deliveries">Services and Deliveries</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Product Code *
                  </label>
                  <input
                    type="text"
                    name="product_code"
                    value={formData.product_code}
                    onChange={handleInputChange}
                    className={`misty-input w-full ${errors.product_code ? 'border-red-500' : ''}`}
                    placeholder="Enter product code"
                    required
                  />
                  {errors.product_code && <p className="text-red-400 text-sm mt-1">{errors.product_code}</p>}
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Product Description *
                  </label>
                  <textarea
                    name="product_description"
                    value={formData.product_description}
                    onChange={handleInputChange}
                    className={`misty-input w-full h-20 ${errors.product_description ? 'border-red-500' : ''}`}
                    placeholder="Enter product description"
                    required
                  />
                  {errors.product_description && <p className="text-red-400 text-sm mt-1">{errors.product_description}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Price ex GST *
                  </label>
                  <input
                    type="number"
                    name="price_ex_gst"
                    value={formData.price_ex_gst}
                    onChange={handleInputChange}
                    className={`misty-input w-full ${errors.price_ex_gst ? 'border-red-500' : ''}`}
                    placeholder="0.00"
                    step="0.01"
                    min="0"
                    required
                  />
                  {errors.price_ex_gst && <p className="text-red-400 text-sm mt-1">{errors.price_ex_gst}</p>}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Minimum Order Quantity *
                  </label>
                  <input
                    type="number"
                    name="minimum_order_quantity"
                    value={formData.minimum_order_quantity}
                    onChange={handleInputChange}
                    className={`misty-input w-full ${errors.minimum_order_quantity ? 'border-red-500' : ''}`}
                    placeholder="1"
                    min="1"
                    required
                  />
                  {errors.minimum_order_quantity && <p className="text-red-400 text-sm mt-1">{errors.minimum_order_quantity}</p>}
                </div>

                <div className="flex items-center">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="consignment"
                      checked={formData.consignment}
                      onChange={handleInputChange}
                      className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                    />
                    <span className="text-white font-medium">Consignment?</span>
                  </label>
                </div>

                <div className="flex items-center">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      name="is_shared_product"
                      checked={formData.is_shared_product}
                      onChange={handleInputChange}
                      className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                    />
                    <span className="text-white font-medium">Shared Product?</span>
                  </label>
                </div>
              </div>

              {/* Shared Product Selection */}
              {formData.is_shared_product && (
                <div className="bg-blue-900/20 border border-blue-600/30 rounded-lg p-4">
                  <h4 className="text-lg font-semibold text-white mb-3">Share with Other Clients</h4>
                  <p className="text-sm text-gray-300 mb-4">
                    Select which clients should have access to this shared product.
                  </p>
                  <div className="max-h-32 overflow-y-auto space-y-2">
                    {clients.map((client) => (
                      <label key={client.id} className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.shared_with_clients.includes(client.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData(prev => ({
                                ...prev,
                                shared_with_clients: [...prev.shared_with_clients, client.id]
                              }));
                            } else {
                              setFormData(prev => ({
                                ...prev,
                                shared_with_clients: prev.shared_with_clients.filter(id => id !== client.id)
                              }));
                            }
                          }}
                          className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                        />
                        <span className="text-sm text-gray-300">{client.company_name}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Paper Cores Specifications - Only show if paper_cores type */}
              {formData.product_type === 'paper_cores' && (
                <PaperCoresSpecifications 
                  formData={formData}
                  handleInputChange={handleInputChange}
                  handleSpecificationSelection={handleSpecificationSelection}
                  productSpecifications={productSpecifications}
                />
              )}

              {/* Production & Makeready Section */}
              <ProductionSection 
                formData={formData}
                handleInputChange={handleInputChange}
                setFormData={setFormData}
              />

              {/* Consumables Section */}
              <ConsumablesSection 
                formData={formData}
                setFormData={setFormData}
                handleAddConsumables={handleAddConsumables}
                removeConsumable={removeConsumable}
              />
            </form>
          </div>
        )}

        {/* Product Form Modal */}
        {showModal && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowModal(false)}>
            <div className="modal-content max-w-3xl max-h-[90vh] overflow-y-auto">
              <form onSubmit={handleSubmit} className="p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">
                    {selectedProduct ? 'Edit Product' : 'Add New Product'}
                  </h3>
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>

                {/* Product Type */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Product Type *
                  </label>
                  <div className="grid grid-cols-3 gap-4">
                    <label className="flex items-center space-x-3 p-4 border border-gray-600 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors">
                      <input
                        type="radio"
                        name="product_type"
                        value="finished_goods"
                        checked={formData.product_type === 'finished_goods'}
                        onChange={handleInputChange}
                        className="text-yellow-400"
                      />
                      <div>
                        <div className="font-medium text-white">Finished Goods</div>
                        <div className="text-sm text-gray-400">Complete products ready for delivery</div>
                      </div>
                    </label>
                    <label className="flex items-center space-x-3 p-4 border border-gray-600 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors">
                      <input
                        type="radio"
                        name="product_type"
                        value="paper_cores"
                        checked={formData.product_type === 'paper_cores'}
                        onChange={handleInputChange}
                        className="text-yellow-400"
                      />
                      <div>
                        <div className="font-medium text-white">Paper Cores</div>
                        <div className="text-sm text-gray-400">Paper core products with specifications</div>
                      </div>
                    </label>
                    <label className="flex items-center space-x-3 p-4 border border-gray-600 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors">
                      <input
                        type="radio"
                        name="product_type"
                        value="services_and_deliveries"
                        checked={formData.product_type === 'services_and_deliveries'}
                        onChange={handleInputChange}
                        className="text-yellow-400"
                      />
                      <div>
                        <div className="font-medium text-white">Services & Deliveries</div>
                        <div className="text-sm text-gray-400">Services or delivery charges</div>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Basic Information */}
                <div className="mb-8">
                  <h4 className="text-lg font-semibold text-white mb-4">Basic Information</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Product Code *
                      </label>
                      <input
                        type="text"
                        name="product_code"
                        value={formData.product_code}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.product_code ? 'border-red-500' : ''}`}
                        placeholder="Enter product code"
                        required
                      />
                      {errors.product_code && (
                        <p className="text-red-400 text-sm mt-1">{errors.product_code}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Price ex GST *
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        name="price_ex_gst"
                        value={formData.price_ex_gst}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.price_ex_gst ? 'border-red-500' : ''}`}
                        placeholder="0.00"
                        required
                      />
                      {errors.price_ex_gst && (
                        <p className="text-red-400 text-sm mt-1">{errors.price_ex_gst}</p>
                      )}
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Product Description *
                      </label>
                      <textarea
                        name="product_description"
                        value={formData.product_description}
                        onChange={handleInputChange}
                        rows={3}
                        className={`misty-textarea w-full ${errors.product_description ? 'border-red-500' : ''}`}
                        placeholder="Enter product description"
                        required
                      />
                      {errors.product_description && (
                        <p className="text-red-400 text-sm mt-1">{errors.product_description}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Minimum Order Quantity *
                      </label>
                      <input
                        type="number"
                        min="1"
                        name="minimum_order_quantity"
                        value={formData.minimum_order_quantity}
                        onChange={handleInputChange}
                        className={`misty-input w-full ${errors.minimum_order_quantity ? 'border-red-500' : ''}`}
                        placeholder="1"
                        required
                      />
                      {errors.minimum_order_quantity && (
                        <p className="text-red-400 text-sm mt-1">{errors.minimum_order_quantity}</p>
                      )}
                    </div>

                    <div className="flex items-center">
                      <label className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          name="consignment"
                          checked={formData.consignment}
                          onChange={handleInputChange}
                          className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                        />
                        <span className="text-white font-medium">Consignment?</span>
                      </label>
                    </div>
                  </div>
                </div>

                {/* Paper Cores Specifications */}
                {formData.product_type === 'paper_cores' && (
                  <div className="mb-8">
                    <h4 className="text-lg font-semibold text-white mb-4">Paper Cores Specifications</h4>
                    
                    {/* Core Specifications Selection */}
                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-300 mb-3">
                        Core Specifications (From Product Specifications)
                      </label>
                      <div className="max-h-32 overflow-y-auto border border-gray-600 rounded-lg p-3">
                        {productSpecifications && productSpecifications.filter(spec => 
                          spec.product_type === 'Spiral Paper Core' || spec.product_type === 'Composite Core'
                        ).length > 0 ? (
                          <div className="space-y-2">
                            {productSpecifications
                              .filter(spec => spec.product_type === 'Spiral Paper Core' || spec.product_type === 'Composite Core')
                              .map((specification) => (
                              <label key={specification.id} className="flex items-center space-x-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={formData.material_used.includes(specification.id)}
                                  onChange={(e) => handleSpecificationSelection(specification.id, e.target.checked)}
                                  className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                                />
                                <span className="text-sm text-gray-300">
                                  {specification.product_name} ({specification.product_type})
                                  {specification.specifications?.id_mm && ` - ID: ${specification.specifications.id_mm}mm`}
                                  {specification.specifications?.wall_thickness && ` - Wall: ${specification.specifications.wall_thickness}mm`}
                                </span>
                              </label>
                            ))}
                          </div>
                        ) : (
                          <p className="text-sm text-gray-400">No core specifications available. Create Spiral Paper Core or Composite Core specifications first.</p>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Core ID
                          <span className="text-xs text-blue-400 ml-2">(Auto-populated from specification)</span>
                        </label>
                        <input
                          type="text"
                          name="core_id"
                          value={formData.core_id}
                          onChange={handleInputChange}
                          className="misty-input w-full bg-gray-600"
                          placeholder="Select a core specification above"
                          readOnly={formData.material_used.length > 0}
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Core Width (mm)
                          <span className="text-xs text-yellow-400 ml-2">*Manual Entry Required</span>
                        </label>
                        <input
                          type="text"
                          name="core_width"
                          value={formData.core_width}
                          onChange={handleInputChange}
                          className="misty-input w-full"
                          placeholder="Enter core width (e.g., 1000)"
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Core Thickness (mm)
                          <span className="text-xs text-blue-400 ml-2">(Auto-populated from specification)</span>
                        </label>
                        <input
                          type="text"
                          name="core_thickness"
                          value={formData.core_thickness}
                          onChange={handleInputChange}
                          className="misty-input w-full bg-gray-600"
                          placeholder="Select a core specification above"
                          readOnly={formData.material_used.length > 0}
                        />
                      </div>

                      <div className="flex items-center">
                        <label className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            name="strength_quality_important"
                            checked={formData.strength_quality_important}
                            onChange={handleInputChange}
                            className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                          />
                          <span className="text-white font-medium">Is strength and Quality important?</span>
                        </label>
                      </div>

                      <div className="flex items-center">
                        <label className="flex items-center space-x-2 cursor-pointer">
                          <input
                            type="checkbox"
                            name="delivery_included"
                            checked={formData.delivery_included}
                            onChange={handleInputChange}
                            className="form-checkbox h-4 w-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                          />
                          <span className="text-white font-medium">Delivery Included?</span>
                        </label>
                      </div>
                    </div>
                  </div>
                )}

                {/* Services and Deliveries Specifications */}
                {formData.product_type === 'services_and_deliveries' && (
                  <div className="mb-8">
                    <h4 className="text-lg font-semibold text-white mb-4">Services and Deliveries Details</h4>
                    
                    {/* Subtype Selection */}
                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-300 mb-3">
                        Type *
                      </label>
                      <div className="grid grid-cols-2 gap-4">
                        <label className="flex items-center space-x-3 p-4 border border-gray-600 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors">
                          <input
                            type="radio"
                            name="service_delivery_subtype"
                            value="services"
                            checked={formData.service_delivery_subtype === 'services'}
                            onChange={handleInputChange}
                            className="text-yellow-400"
                          />
                          <div>
                            <div className="font-medium text-white">Services</div>
                            <div className="text-sm text-gray-400">Service-based charges</div>
                          </div>
                        </label>
                        <label className="flex items-center space-x-3 p-4 border border-gray-600 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors">
                          <input
                            type="radio"
                            name="service_delivery_subtype"
                            value="deliveries"
                            checked={formData.service_delivery_subtype === 'deliveries'}
                            onChange={handleInputChange}
                            className="text-yellow-400"
                          />
                          <div>
                            <div className="font-medium text-white">Deliveries</div>
                            <div className="text-sm text-gray-400">Delivery and transport charges</div>
                          </div>
                        </label>
                      </div>
                    </div>

                    {/* Services Form */}
                    {formData.service_delivery_subtype === 'services' && (
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-1">
                            Job Description *
                          </label>
                          <textarea
                            name="service_job_description"
                            value={formData.service_job_description}
                            onChange={handleInputChange}
                            className="misty-input w-full h-20"
                            placeholder="E.g., Demurrage for shipping container"
                            required
                          />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Time Required *
                            </label>
                            <input
                              type="text"
                              name="service_time_required"
                              value={formData.service_time_required}
                              onChange={handleInputChange}
                              className="misty-input w-full"
                              placeholder="E.g., 2 hours, 3 days"
                              required
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Price *
                            </label>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              name="service_price"
                              value={formData.service_price}
                              onChange={handleInputChange}
                              className="misty-input w-full"
                              placeholder="0.00"
                              required
                            />
                          </div>
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Functions Involved
                          </label>
                          <div className="space-y-2 mb-2">
                            {formData.service_functions.map((func, index) => (
                              <div key={index} className="flex items-center space-x-2">
                                <input
                                  type="text"
                                  value={func}
                                  onChange={(e) => {
                                    const newFunctions = [...formData.service_functions];
                                    newFunctions[index] = e.target.value;
                                    setFormData(prev => ({ ...prev, service_functions: newFunctions }));
                                  }}
                                  className="misty-input flex-1"
                                  placeholder="Describe function"
                                />
                                <button
                                  type="button"
                                  onClick={() => {
                                    const newFunctions = formData.service_functions.filter((_, i) => i !== index);
                                    setFormData(prev => ({ ...prev, service_functions: newFunctions }));
                                  }}
                                  className="text-red-400 hover:text-red-300 p-2"
                                >
                                  <TrashIcon className="h-4 w-4" />
                                </button>
                              </div>
                            ))}
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              setFormData(prev => ({
                                ...prev,
                                service_functions: [...prev.service_functions, '']
                              }));
                            }}
                            className="text-yellow-400 hover:text-yellow-300 text-sm flex items-center"
                          >
                            <PlusIcon className="h-4 w-4 mr-1" />
                            Add Function
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Deliveries Form */}
                    {formData.service_delivery_subtype === 'deliveries' && (
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-1">
                            From Address *
                          </label>
                          <textarea
                            name="delivery_from_address"
                            value={formData.delivery_from_address}
                            onChange={handleInputChange}
                            className="misty-input w-full h-20"
                            placeholder="Enter pickup address"
                            required
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-1">
                            To Address *
                          </label>
                          <textarea
                            name="delivery_to_address"
                            value={formData.delivery_to_address}
                            onChange={handleInputChange}
                            className="misty-input w-full h-20"
                            placeholder="Enter delivery address"
                            required
                          />
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                              Unit Type *
                            </label>
                            <select
                              name="delivery_unit_type"
                              value={formData.delivery_unit_type}
                              onChange={handleInputChange}
                              className="misty-select w-full"
                              required
                            >
                              <option value="Pallets">Pallets</option>
                              <option value="Cores">Cores</option>
                              <option value="Voidfill">Voidfill</option>
                              <option value="Blades">Blades</option>
                              <option value="Other">Other</option>
                            </select>
                          </div>

                          <div>
                            <label className="block text="sm font-medium text-gray-300 mb-1">
                              Price Per Unit *
                            </label>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              name="delivery_price_per_unit"
                              value={formData.delivery_price_per_unit}
                              onChange={handleInputChange}
                              className="misty-input w-full"
                              placeholder="0.00"
                              required
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Consumables Section */}
                <div className="mb-8">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-lg font-semibold text-white">Consumables</h4>
                    <button
                      type="button"
                      onClick={handleAddConsumables}
                      className="misty-button misty-button-secondary flex items-center text-sm"
                    >
                      <PlusIcon className="h-4 w-4 mr-2" />
                      Add Consumables
                    </button>
                  </div>

                  {formData.consumables.length > 0 ? (
                    <div className="space-y-3">
                      {formData.consumables.map((consumable) => (
                        <div key={consumable.id} className="flex items-center justify-between p-4 bg-gray-800 rounded-lg">
                          <div className="flex-1">
                            <div className="font-medium text-white">{consumable.specification_name}</div>
                            <div className="text-sm text-gray-400">
                              Type: {consumable.product_type} | Unit: {consumable.measurement_unit}
                              {consumable.quantity_cores_per_carton && ` | ${consumable.quantity_cores_per_carton} cores per carton`}
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => removeConsumable(consumable.id)}
                            className="text-red-400 hover:text-red-300 ml-4"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6 text-gray-400">
                      <p className="text-sm">No consumables added yet.</p>
                      <p className="text-xs">Click "Add Consumables" to add packaging materials like cartons, tapes, and bags.</p>
                    </div>
                  )}
                </div>

                {/* Form Actions */}
                <div className="flex justify-end space-x-3 pt-6 border-t border-gray-700">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="misty-button misty-button-primary"
                  >
                    {selectedProduct ? 'Update Product' : 'Create Product'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Copy Product Modal */}
        {showCopyModal && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowCopyModal(false)}>
            <div className="modal-content max-w-md">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white">Copy Product</h3>
                  <button
                    onClick={() => setShowCopyModal(false)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Copy to client:
                  </label>
                  <select
                    value={targetClientId}
                    onChange={(e) => setTargetClientId(e.target.value)}
                    className="misty-select w-full"
                  >
                    <option value="">Select client...</option>
                    {clients.map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.company_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => setShowCopyModal(false)}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCopyConfirm}
                    className="misty-button misty-button-primary"
                  >
                    Copy Product
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Add Consumables Modal */}
        {showConsumablesModal && (
          <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowConsumablesModal(false)}>
            <div className="modal-content max-w-2xl max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-white">Add Consumables</h3>
                  <button
                    onClick={() => setShowConsumablesModal(false)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>

                <div className="mb-4">
                  <p className="text-sm text-gray-300 mb-2">
                    Product Section: <span className="font-medium text-white">
                      {formData.product_type === 'finished_goods' ? 'Finished Goods' : 'Paper Cores'}
                    </span>
                  </p>
                </div>

                <ConsumablesSelector 
                  productSpecs={getConsumableSpecs()}
                  productSection={formData.product_type}
                  onAddConsumable={addConsumable}
                  onCancel={() => setShowConsumablesModal(false)}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClientProductCatalogue;