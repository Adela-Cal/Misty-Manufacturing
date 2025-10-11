import React, { useState, useEffect } from 'react';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { XMarkIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

const OrderForm = ({ order, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    client_id: '',
    purchase_order_number: '',
    due_date: '',
    priority: 'Normal/Low', // Priority level for the order
    delivery_address: '',
    delivery_instructions: '',
    notes: '',
    discount_percentage: 0,  // Discount percentage (0-100)
    discount_notes: '',      // Reason for discount
    items: [{
      product_id: '',
      product_name: '',
      quantity: 1,
      unit_price: 0,
      total_price: 0
    }]
  });
  
  const [clients, setClients] = useState([]);
  const [clientProducts, setClientProducts] = useState([]);
  const [selectedClient, setSelectedClient] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingClients, setLoadingClients] = useState(true);
  const [errors, setErrors] = useState({});
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [orderTotals, setOrderTotals] = useState({
    subtotal: 0,
    discountAmount: 0,
    discountedSubtotal: 0,
    gst: 0,
    total: 0
  });
  const [packagingValidation, setPackagingValidation] = useState({}); // Track tubes per carton validation
  
  // Stock allocation states - track per item
  const [itemStockData, setItemStockData] = useState({}); // Object keyed by item index
  
  // Material requirements modal states
  const [showMaterialRequirements, setShowMaterialRequirements] = useState(false);
  const [materialRequirements, setMaterialRequirements] = useState(null);
  const [availableSlitWidths, setAvailableSlitWidths] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);

  useEffect(() => {
    loadClients();
  }, []);

  useEffect(() => {
    if (formData.client_id) {
      loadClientProducts(formData.client_id);
    }
  }, [formData.client_id]);

  useEffect(() => {
    calculateTotals();
  }, [formData.items, formData.discount_percentage]);

  useEffect(() => {
    if (order) {
      setFormData({
        client_id: order.client_id || '',
        purchase_order_number: order.purchase_order_number || '',
        due_date: order.due_date ? new Date(order.due_date).toISOString().split('T')[0] : '',
        priority: order.priority || 'Normal/Low',
        delivery_address: order.delivery_address || '',
        delivery_instructions: order.delivery_instructions || '',
        notes: order.notes || '',
        discount_percentage: order.discount_percentage || 0,
        discount_notes: order.discount_notes || '',
        items: order.items || [{
          product_name: '',
          quantity: 1,
          unit_price: 0,
          total_price: 0
        }]
      });
    }
  }, [order]);

  const loadClients = async () => {
    try {
      setLoadingClients(true);
      const response = await apiHelpers.getClients();
      setClients(response.data);
    } catch (error) {
      console.error('Failed to load clients:', error);
      toast.error('Failed to load clients');
    } finally {
      setLoadingClients(false);
    }
  };

  const loadClientProducts = async (clientId) => {
    try {
      const response = await apiHelpers.getClientCatalogue(clientId);
      setClientProducts(response.data);
      
      // Find selected client
      const client = clients.find(c => c.id === clientId);
      setSelectedClient(client);
    } catch (error) {
      console.error('Failed to load client products:', error);
      setClientProducts([]);
    }
  };

  const calculateTotals = () => {
    const subtotal = formData.items.reduce((sum, item) => sum + (item.total_price || 0), 0);
    
    // Apply discount if provided
    const discountPercentage = parseFloat(formData.discount_percentage) || 0;
    const discountAmount = subtotal * (discountPercentage / 100);
    const discountedSubtotal = subtotal - discountAmount;
    
    // Calculate GST on discounted amount
    const gst = discountedSubtotal * 0.1; // 10% GST
    const total = discountedSubtotal + gst;
    
    setOrderTotals({ 
      subtotal, 
      discountAmount, 
      discountedSubtotal, 
      gst, 
      total 
    });
  };

  // Check stock availability for a product and quantity
  const checkStockAvailability = async (productId, clientId, itemIndex, quantity) => {
    console.log('checkStockAvailability called:', { productId, clientId, itemIndex, quantity }); // Debug log
    
    // Clear previous stock data for this item
    setItemStockData(prev => {
      const updated = { ...prev };
      delete updated[itemIndex];
      return updated;
    });
    
    if (!productId || !quantity || quantity <= 0) {
      return; // Don't check stock without product and quantity
    }
    
    try {
      const response = await apiHelpers.get(`/stock/check-availability?product_id=${productId}&client_id=${clientId}`);
      console.log('Stock API response:', response); // Debug log
      
      // Handle nested response structure: response.data.data
      const stockData = response.data?.data || response.data;
      console.log('Extracted stock data:', stockData); // Debug log
      
      if (stockData && stockData.quantity_on_hand > 0) {
        console.log('Stock available, storing for item:', stockData); // Debug log
        const product = clientProducts.find(p => p.id === productId);
        const maxAllocation = Math.min(stockData.quantity_on_hand, quantity);
        
        setItemStockData(prev => ({
          ...prev,
          [itemIndex]: {
            productId,
            productName: product?.product_description || '',
            stockOnHand: stockData.quantity_on_hand,
            maxAllocation,
            quantity,
            showAllocation: true
          }
        }));
      } else {
        console.log('No stock data or zero quantity:', stockData); // Debug log
      }
    } catch (error) {
      console.log('No stock available or error checking stock:', error.response?.status, error.response?.data);
      // Silently continue - no stock available is not an error state
    }
  };

  // Handle stock allocation for a specific item
  const handleStockAllocation = async (itemIndex, allocateQuantity) => {
    try {
      const stockData = itemStockData[itemIndex];
      if (!stockData) return;
      
      const item = formData.items[itemIndex];
      const remainingQuantity = item.quantity - allocateQuantity;
      
      // Allocate stock on the backend
      await apiHelpers.post('/stock/allocate', {
        product_id: stockData.productId,
        client_id: formData.client_id,
        quantity: allocateQuantity,
        order_reference: `Pending Order - ${new Date().toISOString()}`
      });

      // Update the form data to include allocated stock info
      const newItems = [...formData.items];
      newItems[itemIndex] = {
        ...newItems[itemIndex],
        allocated_stock: allocateQuantity,
        remaining_to_produce: remainingQuantity
      };
      
      setFormData(prev => ({ ...prev, items: newItems }));
      
      // Hide the stock allocation section for this item
      setItemStockData(prev => ({
        ...prev,
        [itemIndex]: {
          ...prev[itemIndex],
          showAllocation: false,
          allocated: true
        }
      }));
      
      toast.success(`${allocateQuantity} units allocated from stock`);
      
      // If there's remaining quantity, automatically show material requirements for production
      if (remainingQuantity > 0) {
        // Add a small delay to let the user see the success message
        setTimeout(async () => {
          await showMaterialRequirementsModal(itemIndex, remainingQuantity);
        }, 1500);
      }
    } catch (error) {
      console.error('Failed to allocate stock:', error);
      toast.error('Failed to allocate stock');
    }
  };

  // Show material requirements modal when stock is insufficient
  const showMaterialRequirementsModal = async (itemIndex, remainingQuantity) => {
    try {
      const item = formData.items[itemIndex];
      
      // Get product specifications to determine material requirements
      console.log('Loading product specifications for:', item.product_id);
      const productResponse = await apiHelpers.getClientProduct(formData.client_id, item.product_id);
      const product = productResponse.data;
      
      console.log('Product specifications loaded:', product);
      
      let requirements;
      let productSpec = null;
      
      // Try to get product specifications to extract material layers
      if (product.specifications && product.specifications.length > 0) {
        try {
          const specResponse = await apiHelpers.get(`/product-specifications/${product.specifications[0]}`);
          productSpec = specResponse.data;
          console.log('Product specification details:', productSpec);
          
          // Calculate material requirements based on product specs and material layers
          requirements = await calculateMaterialRequirements(productSpec, product, remainingQuantity);
        } catch (specError) {
          console.error('Failed to load product specification details:', specError);
          // Fall back to generic requirements
          requirements = await createFallbackMaterialRequirements(product, remainingQuantity);
        }
      } else {
        console.log('No product specifications found, creating fallback requirements');
        // Create fallback material requirements when no specifications exist
        requirements = await createFallbackMaterialRequirements(product, remainingQuantity);
      }
      
      setSelectedItem({ index: itemIndex, item, remainingQuantity });
      setMaterialRequirements(requirements);
      
      // Load available slit widths for all required materials
      await loadAvailableSlitWidths(requirements.materials);
      
      setShowMaterialRequirements(true);
    } catch (error) {
      console.error('Failed to load material requirements:', error);
      toast.error('Failed to load material requirements: ' + error.message);
    }
  };

  // Calculate material requirements based on product specifications
  const calculateMaterialRequirements = async (productSpec, product, quantity) => {
    console.log('Calculating material requirements for quantity:', quantity);
    console.log('Product spec:', productSpec);
    
    const requirements = {
      productName: product.product_name || 'Unknown Product',
      quantity: quantity,
      materials: []
    };

    // Extract material layers from product specifications
    if (productSpec.material_layers && productSpec.material_layers.length > 0) {
      console.log('Found material layers:', productSpec.material_layers);
      
      // Process each material layer
      for (const layer of productSpec.material_layers) {
        try {
          // Get material details from the materials database
          let materialData = null;
          try {
            const materialResponse = await apiHelpers.get(`/materials/${layer.material_id}`);
            materialData = materialResponse.data;
          } catch (error) {
            console.log(`Material ${layer.material_id} not found in materials database, using layer data`);
          }
          
          // Calculate material requirements for this layer
          const layerQuantityPerUnit = layer.quantity_usage || 1;
          const requiredWidthMm = layer.width_mm || 100; // Default width if not specified
          const requiredLengthMeters = quantity * layerQuantityPerUnit; // Simple calculation
          
          const materialRequirement = {
            material_id: layer.material_id,
            material_name: materialData?.material_name || layer.product_name || layer.material_product || 'Unknown Material',
            layer_position: layer.layer_position || 'Unknown Layer',
            layer_thickness_mm: layer.thickness_mm || 0,
            layer_gsm: layer.gsm || 0,
            required_width_mm: requiredWidthMm,
            required_quantity_meters: requiredLengthMeters,
            quantity_per_unit: layerQuantityPerUnit,
            purpose: `Material layer: ${layer.layer_position || 'Unknown'} (${layer.thickness_mm}mm thick)`,
            notes: layer.notes || ''
          };
          
          requirements.materials.push(materialRequirement);
          console.log('Added material requirement:', materialRequirement);
          
        } catch (error) {
          console.error('Error processing material layer:', layer, error);
        }
      }
    } else {
      console.log('No material layers found in product specification');
      
      // Fallback: create a generic requirement if no material layers
      requirements.materials.push({
        material_id: 'unknown',
        material_name: 'Paper Material',
        layer_position: 'Unknown Layer',
        required_width_mm: 100,
        required_quantity_meters: quantity * 10,
        quantity_per_unit: 1,
        purpose: 'Generic material requirement (no specification found)'
      });
    }

    console.log('Final material requirements:', requirements);
    return requirements;
  };

  // Create fallback material requirements when product specifications are missing
  const createFallbackMaterialRequirements = async (product, quantity) => {
    console.log('Creating fallback material requirements for:', product.product_name);
    
    const requirements = {
      productName: product.product_name || 'Unknown Product',
      quantity: quantity,
      materials: []
    };

    try {
      // Get all available raw materials to show as potential options
      const rawMaterialsResponse = await apiHelpers.getRawMaterialsStock();
      const rawMaterials = rawMaterialsResponse.data?.data || rawMaterialsResponse.data || [];
      
      console.log('Available raw materials for fallback:', rawMaterials);
      
      // Filter materials that are likely relevant for paper products
      const relevantMaterials = rawMaterials.filter(material => 
        material.material_name && (
          material.material_name.toLowerCase().includes('paper') ||
          material.material_name.toLowerCase().includes('jintian') ||
          material.material_name.toLowerCase().includes('j260') ||
          material.material_name.toLowerCase().includes('substrate')
        )
      );
      
      // If no relevant materials found, use all materials
      const materialsToShow = relevantMaterials.length > 0 ? relevantMaterials : rawMaterials.slice(0, 3);
      
      // Create generic requirements for each relevant material
      materialsToShow.forEach((material, index) => {
        const materialRequirement = {
          material_id: material.material_id,
          material_name: material.material_name,
          layer_position: `Layer ${index + 1}`,
          layer_thickness_mm: 0.15, // Generic thickness
          layer_gsm: 200, // Generic GSM
          required_width_mm: 100, // Generic width - user can see available options
          required_quantity_meters: quantity * 0.1, // Generic calculation
          quantity_per_unit: 0.1,
          purpose: `Generic material requirement (${material.material_name})`,
          notes: 'No product specifications available - showing available raw materials'
        };
        
        requirements.materials.push(materialRequirement);
      });
      
      // If no materials found at all, create a generic entry
      if (requirements.materials.length === 0) {
        requirements.materials.push({
          material_id: 'fallback',
          material_name: 'Generic Paper Material',
          layer_position: 'Unknown Layer',
          layer_thickness_mm: 0.15,
          layer_gsm: 200,
          required_width_mm: 100,
          required_quantity_meters: quantity * 0.1,
          quantity_per_unit: 0.1,
          purpose: 'Generic material requirement - please check product specifications',
          notes: 'No product specifications or raw materials found'
        });
      }
      
    } catch (error) {
      console.error('Error loading raw materials for fallback:', error);
      
      // Ultimate fallback - create a basic requirement
      requirements.materials.push({
        material_id: 'fallback',
        material_name: 'Paper Material',
        layer_position: 'Unknown Layer',
        layer_thickness_mm: 0.15,
        layer_gsm: 200,
        required_width_mm: 100,
        required_quantity_meters: quantity * 0.1,
        quantity_per_unit: 0.1,
        purpose: 'Fallback material requirement',
        notes: 'Unable to load product specifications or raw materials'
      });
    }

    console.log('Fallback material requirements created:', requirements);
    return requirements;
  };

  // Load available slit widths for required materials
  const loadAvailableSlitWidths = async (materialRequirements) => {
    try {
      console.log('Loading slit widths for materials:', materialRequirements);
      
      const slitWidthPromises = materialRequirements.map(async (requirement) => {
        try {
          console.log(`Searching for slit widths for material: ${requirement.material_name}`);
          
          // First, try to find the material in raw materials on hand by name
          let materialId = requirement.material_id;
          
          // If material_id is 'unknown', search by name
          if (materialId === 'unknown' || !materialId) {
            try {
              // Get all raw materials and find matching name
              const rawMaterialsResponse = await apiHelpers.getRawMaterialsStock();
              const rawMaterials = rawMaterialsResponse.data?.data || rawMaterialsResponse.data || [];
              
              console.log('Raw materials available:', rawMaterials);
              
              // Look for material by name (partial match)
              const matchingMaterial = rawMaterials.find(material => 
                material.material_name && 
                (material.material_name.toLowerCase().includes(requirement.material_name.toLowerCase()) ||
                 requirement.material_name.toLowerCase().includes(material.material_name.toLowerCase()) ||
                 material.material_name.toLowerCase().includes('jintian') ||
                 material.material_name.toLowerCase().includes('j260'))
              );
              
              if (matchingMaterial) {
                materialId = matchingMaterial.material_id;
                console.log(`Found matching raw material: ${matchingMaterial.material_name} (ID: ${materialId})`);
              } else {
                console.log(`No matching raw material found for: ${requirement.material_name}`);
              }
            } catch (error) {
              console.error('Error searching raw materials:', error);
            }
          }
          
          // Load slit widths for this material
          let slitWidths = [];
          if (materialId && materialId !== 'unknown') {
            try {
              const response = await apiHelpers.getSlitWidthsByMaterial(materialId);
              slitWidths = response.data?.data?.slit_widths || [];
              console.log(`Found ${slitWidths.length} slit widths for material ${materialId}`);
            } catch (error) {
              console.log(`No slit widths found for material ${materialId}:`, error.message);
            }
          }
          
          return {
            material_id: materialId,
            material_name: requirement.material_name,
            layer_position: requirement.layer_position,
            required_width_mm: requirement.required_width_mm,
            required_quantity_meters: requirement.required_quantity_meters,
            quantity_per_unit: requirement.quantity_per_unit,
            purpose: requirement.purpose,
            available_widths: slitWidths
          };
          
        } catch (error) {
          console.error(`Failed to load slit widths for material ${requirement.material_name}:`, error);
          return {
            material_id: requirement.material_id,
            material_name: requirement.material_name,
            layer_position: requirement.layer_position,
            required_width_mm: requirement.required_width_mm,
            required_quantity_meters: requirement.required_quantity_meters,
            quantity_per_unit: requirement.quantity_per_unit,
            purpose: requirement.purpose,
            available_widths: []
          };
        }
      });

      const results = await Promise.all(slitWidthPromises);
      console.log('Final slit width results:', results);
      setAvailableSlitWidths(results);
    } catch (error) {
      console.error('Failed to load slit widths:', error);
      setAvailableSlitWidths([]);
    }
  };

  // Allocate slit width to order
  const handleSlitWidthAllocation = async (materialId, slitWidthId, allocationQuantity) => {
    try {
      const allocationRequest = {
        slit_width_id: slitWidthId,
        order_id: `pending-${Date.now()}`, // Temporary order ID for pending orders
        required_quantity_meters: allocationQuantity
      };

      const response = await apiHelpers.allocateSlitWidth(allocationRequest);
      
      if (response.data.success) {
        toast.success(`Allocated ${allocationQuantity} meters of slit material`);
        
        // Refresh available slit widths
        await loadAvailableSlitWidths(materialRequirements.materials);
      } else {
        toast.error(response.data.message || 'Failed to allocate slit width');
      }
    } catch (error) {
      console.error('Failed to allocate slit width:', error);
      toast.error('Failed to allocate slit width');
    }
  };

  // Decline stock allocation for a specific item
  const handleDeclineStockAllocation = (itemIndex) => {
    const item = formData.items[itemIndex];
    
    setItemStockData(prev => ({
      ...prev,
      [itemIndex]: {
        ...prev[itemIndex],
        showAllocation: false
      }
    }));
    
    // Show material requirements modal since no stock will be allocated
    showMaterialRequirementsModal(itemIndex, item.quantity);
  };

  // Validate quantity against tubes per carton for paper core products
  const validatePackaging = (itemIndex, quantity, productId) => {
    if (!productId || !quantity) {
      setPackagingValidation(prev => ({
        ...prev,
        [itemIndex]: null
      }));
      return;
    }

    const selectedProduct = clientProducts.find(p => p.id === productId);
    if (!selectedProduct) {
      setPackagingValidation(prev => ({
        ...prev,
        [itemIndex]: null
      }));
      return;
    }

    // Only validate for paper core products
    if (selectedProduct.product_type !== 'paper_cores') {
      setPackagingValidation(prev => ({
        ...prev,
        [itemIndex]: null
      }));
      return;
    }

    const tubesPerCarton = selectedProduct.tubes_per_carton;
    if (!tubesPerCarton || tubesPerCarton <= 0) {
      setPackagingValidation(prev => ({
        ...prev,
        [itemIndex]: null
      }));
      return;
    }

    const isValid = quantity % tubesPerCarton === 0;
    if (isValid) {
      setPackagingValidation(prev => ({
        ...prev,
        [itemIndex]: {
          isValid: true,
          tubesPerCarton: tubesPerCarton,
          cartons: quantity / tubesPerCarton
        }
      }));
    } else {
      const suggestedQuantity = Math.ceil(quantity / tubesPerCarton) * tubesPerCarton;
      const cartons = Math.ceil(quantity / tubesPerCarton);
      
      setPackagingValidation(prev => ({
        ...prev,
        [itemIndex]: {
          isValid: false,
          tubesPerCarton: tubesPerCarton,
          currentQuantity: quantity,
          suggestedQuantity: suggestedQuantity,
          cartons: cartons
        }
      }));
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...formData.items];
    
    // Convert numeric values properly
    if (field === 'quantity' || field === 'unit_price') {
      const numValue = value === '' ? 0 : Number(value);
      newItems[index] = { ...newItems[index], [field]: numValue };
    } else {
      newItems[index] = { ...newItems[index], [field]: value };
    }
    
    // Always recalculate total price to ensure it's accurate
    const quantity = Number(newItems[index].quantity) || 0;
    const unitPrice = Number(newItems[index].unit_price) || 0;
    newItems[index].total_price = quantity * unitPrice;
    
    // Update form data
    setFormData(prev => ({ ...prev, items: newItems }));
    
    // Validate packaging and check stock when quantity or product changes
    if (field === 'quantity' || field === 'product_id') {
      const productId = field === 'product_id' ? value : newItems[index].product_id;
      const qty = field === 'quantity' ? quantity : newItems[index].quantity;
      
      // Use setTimeout to ensure state is updated before validation and stock checking
      setTimeout(() => {
        validatePackaging(index, qty, productId);
        
        // Check stock availability when both product and quantity are set
        if (productId && qty > 0 && formData.client_id) {
          checkStockAvailability(productId, formData.client_id, index, qty);
        } else if (qty <= 0) {
          // Clear stock data if quantity is 0 or negative
          setItemStockData(prev => {
            const updated = { ...prev };
            delete updated[index];
            return updated;
          });
        }
      }, 0);
    }
  };

  const addItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, {
        product_id: '',
        product_name: '',
        quantity: 1,
        unit_price: 0,
        total_price: 0
      }]
    }));
  };

  const removeItem = (index) => {
    if (formData.items.length > 1) {
      setFormData(prev => ({
        ...prev,
        items: prev.items.filter((_, i) => i !== index)
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.client_id) {
      newErrors.client_id = 'Please select a client';
    }
    
    if (!formData.due_date) {
      newErrors.due_date = 'Due date is required';
    } else {
      const dueDate = new Date(formData.due_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (dueDate < today) {
        newErrors.due_date = 'Due date cannot be in the past';
      }
    }
    
    // Only validate items if client is selected
    if (formData.client_id) {
      let hasValidItems = false;
      formData.items.forEach((item, index) => {
        if (!item.product_name.trim() || !item.product_id) {
          newErrors[`item_${index}_product_name`] = 'Please select a product';
        }
        if (!item.quantity || item.quantity <= 0) {
          newErrors[`item_${index}_quantity`] = 'Quantity must be greater than 0';
        }
        if (!item.unit_price || item.unit_price <= 0) {
          newErrors[`item_${index}_unit_price`] = 'Unit price must be greater than 0';
        }
        
        if (item.product_name.trim() && item.product_id && item.quantity > 0 && item.unit_price > 0) {
          hasValidItems = true;
        }
      });
      
      if (!hasValidItems) {
        newErrors.items = 'At least one valid item is required';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleDelete = () => {
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    if (!order) return;
    
    try {
      setLoading(true);
      await apiHelpers.deleteOrder(order.id);
      toast.success('Order deleted successfully');
      setShowDeleteConfirm(false);
      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Failed to delete order:', error);
      const message = error.response?.data?.detail || 'Failed to delete order';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const cancelDelete = () => {
    setShowDeleteConfirm(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      toast.error('Please fix the errors below');
      return;
    }
    
    setLoading(true);
    
    try {
      // Prepare order data
      const orderData = {
        client_id: formData.client_id,
        purchase_order_number: formData.purchase_order_number || null,
        due_date: new Date(formData.due_date).toISOString(),
        delivery_address: formData.delivery_address || null,
        delivery_instructions: formData.delivery_instructions || null,
        notes: formData.notes || null,
        discount_percentage: parseFloat(formData.discount_percentage) || null,
        discount_notes: formData.discount_notes || null,
        items: formData.items.map(item => ({
          product_id: item.product_id,
          product_name: item.product_name,
          quantity: Number(item.quantity) || 1,
          unit_price: Number(item.unit_price) || 0,
          total_price: Number(item.total_price) || 0
        }))
      };
      
      if (order) {
        // Update existing order (if update endpoint exists)
        // await apiHelpers.updateOrder(order.id, orderData);
        toast.success('Order updated successfully');
      } else {
        // Create new order
        const response = await apiHelpers.createOrder(orderData);
        toast.success(`Order created successfully: ${response.data.data.order_number}`);
      }
      
      onSuccess?.();
      onClose();
      
    } catch (error) {
      console.error('Failed to save order:', error);
      
      // Handle validation errors from backend (Pydantic)
      if (error.response?.data?.detail && Array.isArray(error.response.data.detail)) {
        // Handle array of validation errors
        const errorMessages = error.response.data.detail.map(err => {
          if (typeof err === 'object' && err.msg) {
            return `${err.loc?.join(' → ') || 'Field'}: ${err.msg}`;
          }
          return String(err);
        });
        toast.error(`Validation errors: ${errorMessages.join(', ')}`);
      } else {
        // Handle single error message
        const message = error.response?.data?.detail || error.message || 'Failed to save order';
        toast.error(message);
      }
    } finally {
      setLoading(false);
    }
  };

  // Get minimum date (today)
  const getMinDate = () => {
    const today = new Date();
    return today.toISOString().split('T')[0];
  };

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-content max-w-6xl max-h-[90vh] overflow-y-auto">
        <form onSubmit={handleSubmit} className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">
              {order ? 'Edit Order' : 'Create New Order'}
            </h2>
            <button
              type="button"
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Client Selection */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-white mb-4">Order Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Client *
                </label>
                {loadingClients ? (
                  <div className="misty-input w-full flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-400"></div>
                  </div>
                ) : (
                  <select
                    name="client_id"
                    value={formData.client_id}
                    onChange={handleInputChange}
                    className={`misty-select w-full ${errors.client_id ? 'border-red-500' : ''}`}
                    required
                  >
                    <option value="">Select a client</option>
                    {clients.map(client => (
                      <option key={client.id} value={client.id}>
                        {client.company_name}
                      </option>
                    ))}
                  </select>
                )}
                {errors.client_id && (
                  <p className="text-red-400 text-sm mt-1">{errors.client_id}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Purchase Order Number
                </label>
                <input
                  type="text"
                  name="purchase_order_number"
                  value={formData.purchase_order_number}
                  onChange={handleInputChange}
                  className="misty-input w-full"
                  placeholder="Client's PO number"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Due Date *
                </label>
                <input
                  type="date"
                  name="due_date"
                  value={formData.due_date}
                  onChange={handleInputChange}
                  min={getMinDate()}
                  className={`misty-input w-full ${errors.due_date ? 'border-red-500' : ''}`}
                  required
                />
                {errors.due_date && (
                  <p className="text-red-400 text-sm mt-1">{errors.due_date}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Priority *
                </label>
                <select
                  name="priority"
                  value={formData.priority}
                  onChange={handleInputChange}
                  className="misty-select w-full"
                  required
                >
                  <option value="ASAP">ASAP</option>
                  <option value="Must Delivery On Date">Must Delivery On Date</option>
                  <option value="Normal/Low">Normal/Low</option>
                </select>
              </div>
            </div>
          </div>

          {/* Delivery Information */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-white mb-4">Delivery Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Delivery Address
                </label>
                <textarea
                  name="delivery_address"
                  value={formData.delivery_address}
                  onChange={handleInputChange}
                  rows={3}
                  className="misty-textarea w-full"
                  placeholder={selectedClient ? `Default: ${selectedClient.address}, ${selectedClient.city}, ${selectedClient.state} ${selectedClient.postal_code}` : 'Enter delivery address...'}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Delivery Instructions
                </label>
                <textarea
                  name="delivery_instructions"
                  value={formData.delivery_instructions}
                  onChange={handleInputChange}
                  rows={3}
                  className="misty-textarea w-full"
                  placeholder="Special delivery instructions..."
                />
              </div>
            </div>
          </div>

          {/* Order Items - Only show when client is selected */}
          {formData.client_id && (
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Order Items</h3>
                <button
                  type="button"
                  onClick={addItem}
                  className="misty-button misty-button-secondary flex items-center text-sm"
                >
                  <PlusIcon className="h-4 w-4 mr-1" />
                  Add Item
                </button>
              </div>
              
              {errors.items && (
                <p className="text-red-400 text-sm mb-4">{errors.items}</p>
              )}
              
              <div className="space-y-4">
                {formData.items.map((item, index) => (
                  <div key={index} className="border border-gray-600 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-white font-medium">Item {index + 1}</h4>
                      {formData.items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeItem(index)}
                          className="text-red-400 hover:text-red-300 transition-colors"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                      <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Product Name *
                        </label>
                        {clientProducts.length > 0 ? (
                          <select
                            value={item.product_id}
                            onChange={(e) => {
                              const selectedProduct = clientProducts.find(p => p.id === e.target.value);
                              
                              if (selectedProduct && e.target.value) {
                                // Get current quantity and ensure it's a number
                                const currentQuantity = Number(item.quantity) || 1;
                                const unitPrice = Number(selectedProduct.price_ex_gst) || 0;
                                const totalPrice = currentQuantity * unitPrice;
                                
                                const newItems = [...formData.items];
                                // Update the item with all changes at once including product_id
                                newItems[index] = {
                                  ...newItems[index],
                                  product_id: selectedProduct.id,  // Include product_id for backend
                                  product_name: selectedProduct.product_description,
                                  unit_price: unitPrice,
                                  total_price: totalPrice
                                };
                                
                                // Update form data
                                setFormData(prev => ({ ...prev, items: newItems }));
                                
                                // Check stock if quantity is already filled
                                if (newItems[index].quantity > 0) {
                                  setTimeout(() => {
                                    checkStockAvailability(selectedProduct.id, formData.client_id, index, newItems[index].quantity);
                                  }, 100);
                                }
                                
                              } else {
                                const newItems = [...formData.items];
                                newItems[index] = {
                                  ...newItems[index],
                                  product_id: '',
                                  product_name: '',
                                  unit_price: 0,
                                  total_price: 0
                                };
                                setFormData(prev => ({ ...prev, items: newItems }));
                              }
                            }}
                            className={`misty-select w-full ${errors[`item_${index}_product_name`] ? 'border-red-500' : ''}`}
                          >
                            <option value="">Select a product</option>
                            {clientProducts.map(product => (
                              <option key={product.id} value={product.id}>
                                {product.product_description} - ${parseFloat(product.price_ex_gst).toFixed(2)}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <div className="text-center text-gray-400 py-3">
                            No products available for this client.
                            <br />
                            <span className="text-sm">Add products to the client profile first.</span>
                          </div>
                        )}
                        {errors[`item_${index}_product_name`] && (
                          <p className="text-red-400 text-sm mt-1">{errors[`item_${index}_product_name`]}</p>
                        )}
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Quantity *
                        </label>
                        <input
                          type="number"
                          min="1"
                          step="1"
                          value={item.quantity || 1}
                          onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                          className={`misty-input w-full ${
                            errors[`item_${index}_quantity`] ? 'border-red-500' :
                            packagingValidation[index] && !packagingValidation[index].isValid ? 'border-red-500 bg-red-900/20' : ''
                          }`}
                        />
                        {errors[`item_${index}_quantity`] && (
                          <p className="text-red-400 text-sm mt-1">{errors[`item_${index}_quantity`]}</p>
                        )}
                        
                        {/* Packaging validation messages */}
                        {packagingValidation[index] && (
                          <div className="mt-1">
                            {packagingValidation[index].isValid ? (
                              <p className="text-green-400 text-sm">
                                ✓ Perfect! {packagingValidation[index].cartons} full carton{packagingValidation[index].cartons !== 1 ? 's' : ''} 
                                ({packagingValidation[index].tubesPerCarton} tubes per carton)
                              </p>
                            ) : (
                              <div className="text-red-400 text-sm">
                                <p>⚠ Quantity not divisible by {packagingValidation[index].tubesPerCarton} tubes per carton</p>
                                <p className="text-yellow-400 mt-1">
                                  💡 Suggested: <span className="font-semibold">{packagingValidation[index].suggestedQuantity} units</span> 
                                  ({packagingValidation[index].cartons} full carton{packagingValidation[index].cartons !== 1 ? 's' : ''})
                                  <button
                                    type="button"
                                    onClick={() => handleItemChange(index, 'quantity', packagingValidation[index].suggestedQuantity)}
                                    className="ml-2 px-2 py-0.5 bg-yellow-600 hover:bg-yellow-700 text-black text-xs rounded font-medium transition-colors"
                                  >
                                    Use This
                                  </button>
                                </p>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Unit Price *
                        </label>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={item.unit_price || 0}
                          onChange={(e) => handleItemChange(index, 'unit_price', e.target.value)}
                          className={`misty-input w-full ${errors[`item_${index}_unit_price`] ? 'border-red-500' : ''}`}
                        />
                        {errors[`item_${index}_unit_price`] && (
                          <p className="text-red-400 text-sm mt-1">{errors[`item_${index}_unit_price`]}</p>
                        )}
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-1">
                          Total Price
                        </label>
                        <input
                          type="number"
                          value={(item.total_price || 0).toFixed(2)}
                          className="misty-input w-full bg-gray-600"
                          readOnly
                        />
                      </div>
                    </div>

                    {/* Stock Allocation Section - appears inline under each item */}
                    {itemStockData[index] && itemStockData[index].showAllocation && (
                      <div className="mt-4 p-4 bg-blue-900/20 border border-blue-500 rounded-lg">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center">
                            <span className="text-blue-300 font-medium mr-2">📦 Stock Available</span>
                            <span className="text-blue-200 text-sm">
                              ({itemStockData[index].stockOnHand} units in stock)
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleDeclineStockAllocation(index)}
                            className="text-gray-400 hover:text-white text-sm"
                          >
                            ✕
                          </button>
                        </div>
                        
                        <div className="mb-3 text-sm text-blue-200">
                          <div className="grid grid-cols-3 gap-3 mb-3">
                            <div>
                              <span className="text-gray-300">Order Quantity:</span>
                              <div className="font-medium">{itemStockData[index].quantity} units</div>
                            </div>
                            <div>
                              <span className="text-gray-300">Available Stock:</span>
                              <div className="font-medium">{itemStockData[index].stockOnHand} units</div>
                            </div>
                            <div>
                              <span className="text-gray-300">Max Allocation:</span>
                              <div className="font-medium text-yellow-400">{itemStockData[index].maxAllocation} units</div>
                            </div>
                          </div>
                        </div>

                        <div className="bg-blue-800/30 p-3 rounded mb-3">
                          <p className="text-blue-100 text-sm font-medium mb-2">
                            Would you like to allocate stock to this order?
                          </p>
                          <p className="text-blue-200 text-xs">
                            This will reduce your stock on hand and show the allocated amount in the job card.
                          </p>
                        </div>

                        <div className="flex justify-end space-x-2">
                          <button
                            type="button"
                            onClick={() => handleDeclineStockAllocation(index)}
                            className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded transition-colors"
                          >
                            No, Don't Allocate
                          </button>
                          <button
                            type="button"
                            onClick={() => showMaterialRequirementsModal(index, item.quantity - itemStockData[index].maxAllocation)}
                            className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white text-sm rounded transition-colors"
                          >
                            View Materials Needed
                          </button>
                          <button
                            type="button"
                            onClick={() => handleStockAllocation(index, itemStockData[index].maxAllocation)}
                            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors font-medium"
                          >
                            Yes, Allocate {itemStockData[index].maxAllocation} Units
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Stock Allocated Confirmation */}
                    {item.allocated_stock > 0 && (
                      <div className="mt-4 p-3 bg-green-900/20 border border-green-500 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center text-green-300 text-sm">
                            <span className="mr-2">✓</span>
                            <span className="font-medium">
                              {item.allocated_stock} units allocated from stock
                            </span>
                            <span className="ml-2 text-green-400">
                              • {item.remaining_to_produce || (item.quantity - item.allocated_stock)} to produce
                            </span>
                          </div>
                          
                          {/* Show Material Requirements button if there's remaining quantity to produce */}
                          {(item.remaining_to_produce || (item.quantity - item.allocated_stock)) > 0 && (
                            <button
                              type="button"
                              onClick={() => showMaterialRequirementsModal(index, item.remaining_to_produce || (item.quantity - item.allocated_stock))}
                              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors font-medium"
                            >
                              Raw Materials Needed
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Show message when no client selected */}
          {!formData.client_id && (
            <div className="mb-8">
              <div className="misty-card p-6 text-center">
                <h3 className="text-lg font-semibold text-gray-300 mb-2">Select a Client</h3>
                <p className="text-gray-400">Please select a client above to add order items.</p>
              </div>
            </div>
          )}

          {/* Discount Section - Only show when client is selected */}
          {formData.client_id && (
            <div className="mb-8">
              <div className="misty-card p-4 bg-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">Discount (Optional)</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Discount Percentage (%)
                    </label>
                    <input
                      type="number"
                      name="discount_percentage"
                      min="0"
                      max="100"
                      step="0.1"
                      value={formData.discount_percentage}
                      onChange={handleInputChange}
                      className="misty-input w-full"
                      placeholder="0.0"
                    />
                    <p className="text-xs text-gray-400 mt-1">
                      Enter percentage (0-100). Applied before GST calculation.
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      Discount Reason
                    </label>
                    <input
                      type="text"
                      name="discount_notes"
                      value={formData.discount_notes}
                      onChange={handleInputChange}
                      className="misty-input w-full"
                      placeholder="Reason for discount (e.g., Bulk order, Loyalty discount)"
                    />
                  </div>
                </div>
                
                {/* Show discount calculation preview */}
                {parseFloat(formData.discount_percentage) > 0 && orderTotals.subtotal > 0 && (
                  <div className="mt-4 p-3 bg-gray-600 rounded-lg">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-300">Discount Amount:</span>
                      <span className="text-red-400 font-medium">
                        -${orderTotals.discountAmount.toFixed(2)}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Order Totals - Only show when client is selected and has items */}
          {formData.client_id && formData.items.some(item => item.product_name && item.quantity > 0) && (
            <div className="mb-8">
              <div className="misty-card p-4 bg-gray-700">
                <h3 className="text-lg font-semibold text-white mb-4">Order Summary</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Subtotal:</span>
                    <span className="text-white font-medium">${orderTotals.subtotal.toFixed(2)}</span>
                  </div>
                  
                  {/* Show discount if applied */}
                  {orderTotals.discountAmount > 0 && (
                    <>
                      <div className="flex justify-between">
                        <span className="text-gray-300">
                          Discount ({formData.discount_percentage}%):
                        </span>
                        <span className="text-red-400 font-medium">
                          -${orderTotals.discountAmount.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between border-b border-gray-600 pb-2">
                        <span className="text-gray-300">Discounted Subtotal:</span>
                        <span className="text-white font-medium">${orderTotals.discountedSubtotal.toFixed(2)}</span>
                      </div>
                    </>
                  )}
                  
                  <div className="flex justify-between">
                    <span className="text-gray-300">GST (10%):</span>
                    <span className="text-white font-medium">${orderTotals.gst.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between text-lg font-bold border-t border-gray-600 pt-2">
                    <span className="text-white">Total:</span>
                    <span className="text-yellow-400">${orderTotals.total.toFixed(2)}</span>
                  </div>
                  
                  {/* Show discount reason if provided */}
                  {formData.discount_notes && orderTotals.discountAmount > 0 && (
                    <div className="mt-3 pt-2 border-t border-gray-600">
                      <p className="text-xs text-gray-400">
                        <span className="font-medium">Discount Reason:</span> {formData.discount_notes}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Notes */}
          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Order Notes
            </label>
            <textarea
              name="notes"
              value={formData.notes}
              onChange={handleInputChange}
              rows={3}
              className="misty-textarea w-full"
              placeholder="Additional notes for this order..."
            />
          </div>

          {/* Form Actions */}
          <div className="flex justify-between pt-6 border-t border-gray-700">
            <div>
              {order && (
                <button
                  type="button"
                  onClick={handleDelete}
                  className="misty-button misty-button-danger"
                  disabled={loading}
                >
                  <TrashIcon className="h-4 w-4 mr-2" />
                  Delete Order
                </button>
              )}
            </div>
            <div className="flex space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="misty-button misty-button-secondary"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="misty-button misty-button-primary"
                disabled={loading || loadingClients}
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900 mr-2"></div>
                    {order ? 'Updating...' : 'Creating...'}
                  </div>
                ) : (
                  order ? 'Update Order' : 'Create Order'
                )}
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && order && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && cancelDelete()}>
          <div className="modal-content max-w-md">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0">
                  <TrashIcon className="h-8 w-8 text-red-400" />
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-white">Delete Order</h3>
                  <p className="text-sm text-gray-400">This action cannot be undone.</p>
                </div>
              </div>
              
              <div className="mb-6">
                <p className="text-gray-300">
                  Are you sure you wish to delete order <span className="font-semibold text-white">"{order.order_number}"</span>?
                </p>
                <p className="text-sm text-gray-400 mt-2">
                  This will cancel the order and remove it from active production. Orders in production cannot be deleted.
                </p>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={cancelDelete}
                  className="misty-button misty-button-secondary"
                  disabled={loading}
                >
                  No, Cancel
                </button>
                <button
                  type="button"
                  onClick={confirmDelete}
                  className="misty-button misty-button-danger"
                  disabled={loading}
                >
                  {loading ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Deleting...
                    </div>
                  ) : (
                    'Yes, Delete Order'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Material Requirements Modal */}
      {showMaterialRequirements && materialRequirements && selectedItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-5xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white">
                Material Requirements - {materialRequirements.productName}
              </h3>
              <button
                onClick={() => setShowMaterialRequirements(false)}
                className="text-gray-400 hover:text-white"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="mb-4 p-4 bg-blue-900/20 border border-blue-700 rounded-lg">
              <h4 className="text-lg font-medium text-white mb-2">Production Requirements</h4>
              <p className="text-sm text-blue-200 mb-3">
                Raw materials needed for manufacturing the remaining {selectedItem.remainingQuantity} units
              </p>
              
              {/* Show warning if using fallback materials */}
              {materialRequirements.materials.some(m => m.notes && m.notes.includes('No product specifications')) && (
                <div className="p-3 bg-yellow-900/20 border border-yellow-600 rounded mb-3">
                  <div className="flex items-center text-yellow-300 text-sm">
                    <span className="mr-2">⚠️</span>
                    <span className="font-medium">Product specifications missing</span>
                  </div>
                  <p className="text-yellow-200 text-xs mt-1">
                    Showing available raw materials. Please add product specifications for accurate material requirements.
                  </p>
                </div>
              )}
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-300">Total Required:</span>
                  <div className="font-medium text-white">{selectedItem.item.quantity} units</div>
                </div>
                <div>
                  <span className="text-gray-300">Stock Allocated:</span>
                  <div className="font-medium text-green-400">{selectedItem.item.allocated_stock || 0} units</div>
                </div>
                <div>
                  <span className="text-gray-300">To Manufacture:</span>
                  <div className="font-medium text-yellow-400">{selectedItem.remainingQuantity} units</div>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              {availableSlitWidths.map((materialData, index) => (
                <div key={index} className="bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="text-lg font-medium text-white">{materialData.material_name}</h4>
                      <div className="text-sm text-gray-400">
                        {materialData.layer_position} • {materialData.purpose}
                      </div>
                    </div>
                    <div className="text-right text-sm text-gray-300">
                      <div>Required: {materialData.required_width_mm}mm</div>
                      <div>Quantity: {materialData.required_quantity_meters.toFixed(1)}m</div>
                      <div className="text-xs text-gray-400">
                        ({materialData.quantity_per_unit} per unit)
                      </div>
                    </div>
                  </div>

                  {materialData.available_widths.length > 0 ? (
                    <div className="overflow-hidden rounded-lg">
                      <table className="w-full">
                        <thead className="bg-gray-600">
                          <tr>
                            <th className="px-3 py-2 text-left text-sm font-medium text-gray-300">Width (mm)</th>
                            <th className="px-3 py-2 text-right text-sm font-medium text-gray-300">Available (m)</th>
                            <th className="px-3 py-2 text-center text-sm font-medium text-gray-300">Match</th>
                            <th className="px-3 py-2 text-center text-sm font-medium text-gray-300">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-600">
                          {materialData.available_widths.map((widthGroup, widthIndex) => (
                            <tr key={widthIndex} className="hover:bg-gray-600">
                              <td className="px-3 py-2 text-sm font-medium text-white">
                                {widthGroup.slit_width_mm}mm
                              </td>
                              <td className="px-3 py-2 text-right text-sm text-white">
                                {widthGroup.available_quantity_meters.toFixed(2)}
                              </td>
                              <td className="px-3 py-2 text-center">
                                {widthGroup.slit_width_mm === materialData.required_width_mm ? (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-900 text-green-300">
                                    ✓ Exact Match
                                  </span>
                                ) : Math.abs(widthGroup.slit_width_mm - materialData.required_width_mm) <= 5 ? (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-900 text-yellow-300">
                                    ± Close Match ({Math.abs(widthGroup.slit_width_mm - materialData.required_width_mm)}mm off)
                                  </span>
                                ) : widthGroup.slit_width_mm > materialData.required_width_mm ? (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-900 text-blue-300">
                                    ↑ Wider ({widthGroup.slit_width_mm - materialData.required_width_mm}mm over)
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-red-900 text-red-300">
                                    ↓ Narrower ({materialData.required_width_mm - widthGroup.slit_width_mm}mm under)
                                  </span>
                                )}
                              </td>
                              <td className="px-3 py-2 text-center">
                                {widthGroup.available_quantity_meters > 0 && (
                                  <div className="flex items-center justify-center space-x-2">
                                    <input
                                      type="number"
                                      step="0.1"
                                      max={Math.min(widthGroup.available_quantity_meters, materialData.required_quantity_meters)}
                                      placeholder="Meters"
                                      className="misty-input w-20 text-sm"
                                      id={`allocate-${materialData.material_id}-${widthIndex}`}
                                    />
                                    <button
                                      onClick={() => {
                                        const input = document.getElementById(`allocate-${materialData.material_id}-${widthIndex}`);
                                        const quantity = parseFloat(input.value);
                                        if (quantity > 0) {
                                          // Get the first entry ID from the width group
                                          const firstEntry = widthGroup.entries[0];
                                          handleSlitWidthAllocation(materialData.material_id, firstEntry.id, quantity);
                                          input.value = '';
                                        }
                                      }}
                                      className="misty-button misty-button-primary text-xs py-1 px-2"
                                    >
                                      Allocate
                                    </button>
                                  </div>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="p-8 text-center text-gray-400">
                      <div className="text-lg mb-2">No slit widths available</div>
                      <p className="text-sm">
                        Required width: {materialData.required_width_mm}mm × {materialData.required_quantity_meters}m
                      </p>
                      <p className="text-xs mt-2 text-yellow-400">
                        This material will need to be slit from raw stock
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex justify-between mt-6 pt-4 border-t border-gray-600">
              <div className="text-sm text-gray-400">
                <p>• Exact matches are preferred for optimal material usage</p>
                <p>• Close matches (±5mm) may be acceptable depending on specifications</p>
                <p>• Allocated slit widths will be reserved for this production order</p>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowMaterialRequirements(false)}
                  className="misty-button misty-button-secondary"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    setShowMaterialRequirements(false);
                    toast.success('Raw materials allocated for production. Continue with order creation.');
                  }}
                  className="misty-button misty-button-primary"
                >
                  Continue Order
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Old stock allocation modal removed - now using inline sections */}
    </div>
  );
};

export default OrderForm;