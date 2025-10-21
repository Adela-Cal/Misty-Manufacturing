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
  ArrowDownIcon,
  ClockIcon,
  CubeIcon,
  PrinterIcon,
  DocumentArrowDownIcon
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
  const [availableMaterials, setAvailableMaterials] = useState([]); // Materials from database
  const [clientProducts, setClientProducts] = useState([]); // Products from selected client's catalogue
  
  // Stock grouping and history states
  const [groupedProducts, setGroupedProducts] = useState([]);
  const [showStockHistory, setShowStockHistory] = useState(false);
  const [selectedStockHistory, setSelectedStockHistory] = useState(null);
  const [stockAllocations, setStockAllocations] = useState([]);
  const [archivedAllocations, setArchivedAllocations] = useState([]);
  const [showArchivedAllocations, setShowArchivedAllocations] = useState(false);
  const [currentAllocationProduct, setCurrentAllocationProduct] = useState(null);

  // Manual Stock Take states
  const [showManualStockTake, setShowManualStockTake] = useState(false);
  const [manualStockTakeMonth, setManualStockTakeMonth] = useState('');
  const [manualStockTakeItems, setManualStockTakeItems] = useState([]);
  const [manualStockTakeLoading, setManualStockTakeLoading] = useState(false);
  const [stockTakeModifications, setStockTakeModifications] = useState({});
  
  // Archived Stocktakes states
  const [showArchivedStocktakes, setShowArchivedStocktakes] = useState(false);
  const [archivedStocktakes, setArchivedStocktakes] = useState([]);
  const [loadingArchived, setLoadingArchived] = useState(false);
  const [viewingStocktake, setViewingStocktake] = useState(null);

  // Slit widths modal states
  const [showSlitWidthsModal, setShowSlitWidthsModal] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [materialSlitWidths, setMaterialSlitWidths] = useState([]);
  const [showAddSlitWidthForm, setShowAddSlitWidthForm] = useState(false);
  const [editingSlitWidth, setEditingSlitWidth] = useState(null);
  const [slitWidthForm, setSlitWidthForm] = useState({
    slit_width_mm: '',
    quantity_meters: '',
    source_job_id: 'manual-entry',
    source_order_id: 'manual-entry'
  });

  // Modal states
  const [showSubstrateModal, setShowSubstrateModal] = useState(false);
  const [showMaterialModal, setShowMaterialModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [editingField, setEditingField] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedItemType, setSelectedItemType] = useState(null); // 'substrate' or 'material'

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
    loadClients();
    loadStockAlerts();
    loadAvailableMaterials();
  }, []);

  useEffect(() => {
    if (activeTab === 'raw_substrates') {
      loadRawSubstrates();
    } else if (activeTab === 'raw_materials') {
      loadRawMaterialsStock();
    }
  }, [activeTab, selectedClient]);

  // Group products whenever rawSubstrates changes
  useEffect(() => {
    const loadGroupedProducts = async () => {
      if (rawSubstrates && rawSubstrates.length > 0) {
        const filtered = selectedClient === 'all' 
          ? rawSubstrates 
          : rawSubstrates.filter(substrate => substrate.client_id === selectedClient);
        
        const grouped = await groupProductsByItem(filtered);
        setGroupedProducts(grouped);
      } else {
        setGroupedProducts([]);
      }
    };
    
    loadGroupedProducts();
  }, [rawSubstrates, selectedClient]);

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

  const loadClients = async () => {
    try {
      const response = await apiHelpers.getClients();
      setClients(response.data || []);
    } catch (error) {
      console.error('Failed to load clients:', error);
    }
  };

  const loadStockAlerts = async () => {
    try {
      const response = await apiHelpers.get('/stock/alerts');
      // Handle StandardResponse format: response.data.data contains the actual array
      const data = response.data?.data || response.data || [];
      const alerts = Array.isArray(data) ? data : [];
      setStockAlerts(alerts);
      setShowStockAlert(alerts.length > 0);
    } catch (error) {
      console.error('Failed to load stock alerts:', error);
      setStockAlerts([]); // Ensure it's always an array
      setShowStockAlert(false);
    }
  };

  const loadRawSubstrates = async () => {
    try {
      const response = await apiHelpers.get(`/stock/raw-substrates${selectedClient !== 'all' ? `?client_id=${selectedClient}` : ''}`);
      // Handle StandardResponse format: response.data.data contains the actual array
      const data = response.data?.data || response.data || [];
      setRawSubstrates(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load raw substrates:', error);
      toast.error('Failed to load raw substrates');
      setRawSubstrates([]); // Ensure it's always an array
    }
  };

  const loadRawMaterialsStock = async () => {
    try {
      const response = await apiHelpers.get('/stock/raw-materials');
      // Handle StandardResponse format: response.data.data contains the actual array
      const data = response.data?.data || response.data || [];
      setRawMaterialsStock(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load raw materials stock:', error);
      toast.error('Failed to load raw materials stock');
      setRawMaterialsStock([]); // Ensure it's always an array
    }
  };

  const loadAvailableMaterials = async () => {
    try {
      const response = await apiHelpers.getMaterials();
      const data = response.data || [];
      setAvailableMaterials(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load available materials:', error);
      setAvailableMaterials([]);
    }
  };

  // Load slit widths for a specific material
  const loadSlitWidths = async (materialId, materialName) => {
    try {
      const response = await apiHelpers.getSlitWidthsByMaterial(materialId);
      const data = response.data?.data || response.data || {};
      
      setSelectedMaterial({
        id: materialId,
        name: materialName
      });
      setMaterialSlitWidths(data.slit_widths || []);
      setShowSlitWidthsModal(true);
    } catch (error) {
      console.error('Failed to load slit widths:', error);
      toast.error('Failed to load slit widths for this material');
      setMaterialSlitWidths([]);
    }
  };

  // Add new slit width manually
  const handleAddSlitWidth = async () => {
    if (!slitWidthForm.slit_width_mm || !slitWidthForm.quantity_meters) {
      toast.error('Please enter both width and quantity');
      return;
    }

    try {
      const slitWidthData = {
        raw_material_id: selectedMaterial.id,
        raw_material_name: selectedMaterial.name,
        slit_width_mm: parseFloat(slitWidthForm.slit_width_mm),
        quantity_meters: parseFloat(slitWidthForm.quantity_meters),
        source_job_id: 'manual-entry',
        source_order_id: 'manual-entry',
        created_from_additional_widths: false,
        material_specifications: {}
      };

      const response = await apiHelpers.createSlitWidth(slitWidthData);
      
      if (response.data.success) {
        toast.success('Slit width added successfully');
        setSlitWidthForm({
          slit_width_mm: '',
          quantity_meters: '',
          source_job_id: 'manual-entry',
          source_order_id: 'manual-entry'
        });
        setShowAddSlitWidthForm(false);
        // Reload slit widths
        await loadSlitWidths(selectedMaterial.id, selectedMaterial.name);
      } else {
        toast.error(response.data.message || 'Failed to add slit width');
      }
    } catch (error) {
      console.error('Failed to add slit width:', error);
      toast.error('Failed to add slit width');
    }
  };

  // Update slit width quantity
  const handleUpdateSlitWidthQuantity = async (slitWidthId, newQuantity) => {
    if (newQuantity < 0) {
      toast.error('Quantity cannot be negative');
      return;
    }

    try {
      const updateData = {
        quantity_meters: parseFloat(newQuantity),
        remaining_quantity: parseFloat(newQuantity)
      };

      const response = await apiHelpers.updateSlitWidth(slitWidthId, updateData);
      
      if (response.data.success) {
        toast.success('Slit width updated successfully');
        setEditingSlitWidth(null);
        // Reload slit widths
        await loadSlitWidths(selectedMaterial.id, selectedMaterial.name);
      } else {
        toast.error(response.data.message || 'Failed to update slit width');
      }
    } catch (error) {
      console.error('Failed to update slit width:', error);
      toast.error('Failed to update slit width');
    }
  };

  // Delete slit width entry
  const handleDeleteSlitWidth = async (slitWidthId) => {
    console.log('Delete button clicked for slit width ID:', slitWidthId);
    
    if (!slitWidthId) {
      toast.error('Invalid slit width ID');
      console.error('Slit width ID is missing or undefined');
      return;
    }
    
    if (!window.confirm('Are you sure you want to delete this slit width entry?')) {
      console.log('Delete cancelled by user');
      return;
    }

    try {
      console.log('Attempting to delete slit width:', slitWidthId);
      const response = await apiHelpers.deleteSlitWidth(slitWidthId);
      
      console.log('Delete response:', response);
      
      // Check if response has data property and success field
      const success = response.data?.success || response.success;
      const message = response.data?.message || response.message;
      
      if (success) {
        toast.success(message || 'Slit width deleted successfully');
        // Reload slit widths
        if (selectedMaterial && selectedMaterial.id) {
          await loadSlitWidths(selectedMaterial.id, selectedMaterial.name);
          console.log('Slit widths reloaded after deletion');
        } else {
          console.warn('Cannot reload slit widths - selectedMaterial not available');
        }
      } else {
        console.error('Delete failed:', response);
        toast.error(message || 'Failed to delete slit width');
      }
    } catch (error) {
      console.error('Failed to delete slit width:', error);
      
      // Check if it's an HTTP error response
      if (error.response) {
        const errorMessage = error.response.data?.message || error.response.data?.detail || 'Failed to delete slit width';
        
        // Special handling for allocated slit widths
        if (error.response.status === 400 && errorMessage.includes('allocated')) {
          toast.error('Cannot delete: This slit width is allocated to an order. Remove allocation first.');
        } else {
          toast.error(errorMessage);
        }
        
        // Log more details for debugging
        console.error('Error status:', error.response.status);
        console.error('Error data:', error.response.data);
      } else if (error.request) {
        toast.error('Network error: Could not reach server');
        console.error('No response received:', error.request);
      } else {
        toast.error('Error: ' + error.message);
        console.error('Error setting up request:', error.message);
      }
    }
  };

  // Adjust slit width quantity (add or subtract)
  const handleAdjustSlitWidth = async (slitWidthId, currentQuantity, adjustment) => {
    const newQuantity = currentQuantity + adjustment;
    if (newQuantity < 0) {
      toast.error('Adjustment would result in negative quantity');
      return;
    }
    await handleUpdateSlitWidthQuantity(slitWidthId, newQuantity);
  };

  // Group products by product_id + client_id combination
  const groupProductsByItem = async (substrates) => {
    const groups = {};
    
    substrates.forEach(substrate => {
      const key = `${substrate.product_id}-${substrate.client_id}`;
      if (!groups[key]) {
        groups[key] = {
          ...substrate,
          total_quantity: 0,
          entries: [],
          allocated_quantity: 0,
          available_quantity: 0
        };
      }
      
      groups[key].total_quantity += substrate.quantity_on_hand;
      groups[key].entries.push(substrate);
    });

    // Load allocated quantities for each group
    const groupKeys = Object.keys(groups);
    for (const key of groupKeys) {
      try {
        const [productId, clientId] = key.split('-');
        const response = await apiHelpers.get(`/stock/allocations?product_id=${productId}&client_id=${clientId}`);
        const allocations = response.data?.data?.allocations || [];
        groups[key].allocated_quantity = allocations.reduce((sum, alloc) => sum + Math.abs(alloc.quantity), 0);
      } catch (error) {
        console.log('Failed to load allocations for', key, error);
        groups[key].allocated_quantity = 0;
      }
    }

    // Calculate available vs allocated for each group
    Object.keys(groups).forEach(key => {
      groups[key].available_quantity = groups[key].total_quantity - groups[key].allocated_quantity;
    });

    return Object.values(groups);
  };

  // Load stock history for a specific product
  const loadStockHistory = async (productId, clientId) => {
    try {
      const response = await apiHelpers.get(`/stock/history?product_id=${productId}&client_id=${clientId}`);
      setSelectedStockHistory(response.data);
      setShowStockHistory(true);
    } catch (error) {
      console.error('Failed to load stock history:', error);
      toast.error('Failed to load stock history');
    }
  };

  // Load stock allocations for a specific product
  const loadStockAllocations = async (productId, clientId) => {
    try {
      const response = await apiHelpers.get(`/stock/allocations?product_id=${productId}&client_id=${clientId}`);
      // Extract allocations from nested data structure
      const allocations = response.data?.data?.allocations || [];
      setStockAllocations(allocations);
      setCurrentAllocationProduct({ productId, clientId });
      console.log('Loaded allocations:', allocations);
    } catch (error) {
      console.error('Failed to load stock allocations:', error);
      toast.error('Failed to load stock allocations');
    }
  };

  // Load archived allocations for a specific product
  const loadArchivedAllocations = async () => {
    if (!currentAllocationProduct) return;
    
    try {
      const response = await apiHelpers.get(`/stock/allocations/archived?product_id=${currentAllocationProduct.productId}&client_id=${currentAllocationProduct.clientId}`);
      const archived = response.data?.data?.allocations || [];
      setArchivedAllocations(archived);
      setShowArchivedAllocations(true);
      
      if (archived.length === 0) {
        toast.info('No archived allocations found for this product');
      }
      
      console.log('Loaded archived allocations:', archived);
    } catch (error) {
      console.error('Failed to load archived allocations:', error);
      toast.error('Failed to load archived allocations');
    }
  };

  const loadClientProducts = async (clientId) => {
    try {
      const response = await apiHelpers.get(`/clients/${clientId}/catalog`);
      const data = response.data || [];
      console.log('Loaded client products:', data); // Debug log
      setClientProducts(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load client products:', error);
      setClientProducts([]);
    }
  };

  const handleDoubleClick = (itemId, field) => {
    setEditingItem(itemId);
    setEditingField(field);
  };

  const handleFieldSave = async (itemId, field, value, itemType) => {
    try {
      const endpoint = itemType === 'substrate' ? `/stock/raw-substrates/${itemId}` : `/stock/raw-materials/${itemId}`;
      await apiHelpers.put(endpoint, { [field]: parseFloat(value) });
      
      setEditingItem(null);
      setEditingField(null);
      
      if (itemType === 'substrate') {
        loadRawSubstrates();
      } else {
        loadRawMaterialsStock();
      }
      
      toast.success(`${field} updated successfully`);
    } catch (error) {
      console.error(`Failed to update ${field}:`, error);
      toast.error(`Failed to update ${field}`);
    }
  };

  const acknowledgeAlert = async (alertId, snoozeHours = null) => {
    try {
      await apiHelpers.post(`/stock/alerts/${alertId}/acknowledge`, {
        snooze_hours: snoozeHours
      });
      
      loadStockAlerts();
      toast.success(snoozeHours ? `Alert snoozed for ${snoozeHours} hours` : 'Alert acknowledged');
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
      toast.error('Failed to acknowledge alert');
    }
  };

  const checkLowStock = async () => {
    try {
      const response = await apiHelpers.post('/stock/check-low-stock');
      loadStockAlerts();
      toast.success(response.message || 'Stock check completed');
    } catch (error) {
      console.error('Failed to check low stock:', error);
      toast.error('Failed to check low stock');
    }
  };

  const handleViewItem = (item, itemType) => {
    setSelectedItem(item);
    setSelectedItemType(itemType);
    setShowViewModal(true);
  };

  const handleEditItem = (item, itemType) => {
    setSelectedItem(item);
    setSelectedItemType(itemType);
    setShowEditModal(true);
  };

  const handleDeleteItem = (item, itemType) => {
    setSelectedItem(item);
    setSelectedItemType(itemType);
    setShowDeleteConfirm(true);
  };

  const confirmDelete = async () => {
    try {
      console.log('Deleting item:', selectedItem);
      console.log('Item type:', selectedItemType);
      
      if (!selectedItem || !selectedItem.id) {
        toast.error('No item selected for deletion');
        return;
      }
      
      const endpoint = selectedItemType === 'substrate' 
        ? `/stock/raw-substrates/${selectedItem.id}` 
        : `/stock/raw-materials/${selectedItem.id}`;
      
      console.log('Delete endpoint:', endpoint);
      
      const response = await apiHelpers.delete(endpoint);
      console.log('Delete response:', response);
      
      if (selectedItemType === 'substrate') {
        await loadRawSubstrates();
      } else {
        await loadRawMaterialsStock();
      }
      
      setShowDeleteConfirm(false);
      setSelectedItem(null);
      toast.success(`${selectedItemType === 'substrate' ? 'Substrate' : 'Material'} deleted successfully`);
    } catch (error) {
      console.error('Failed to delete item:', error);
      console.error('Error details:', error.response?.data);
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to delete item';
      toast.error(`Delete failed: ${errorMsg}`);
    }
  };

  const handleEditSave = async (updatedData) => {
    try {
      const endpoint = selectedItemType === 'substrate' 
        ? `/stock/raw-substrates/${selectedItem.id}` 
        : `/stock/raw-materials/${selectedItem.id}`;
      
      await apiHelpers.put(endpoint, updatedData);
      
      if (selectedItemType === 'substrate') {
        loadRawSubstrates();
      } else {
        loadRawMaterialsStock();
      }
      
      setShowEditModal(false);
      setSelectedItem(null);
      toast.success(`${selectedItemType === 'substrate' ? 'Substrate' : 'Material'} updated successfully`);
    } catch (error) {
      console.error('Failed to update item:', error);
      toast.error('Failed to update item');
    }
  };

  // Manual Stock Take Functions
  const loadManualStockTakeItems = async () => {
    try {
      setManualStockTakeLoading(true);
      
      // Load all products on hand (raw substrates)
      const substratesResponse = await apiHelpers.get('/stock/raw-substrates');
      const substrates = substratesResponse.data?.data || substratesResponse.data || [];
      
      // Load all raw materials on hand
      const materialsResponse = await apiHelpers.get('/stock/raw-materials');
      const materials = materialsResponse.data?.data || materialsResponse.data || [];
      
      // Combine and format items
      const allItems = [
        ...substrates.map(item => ({
          id: item.id,
          type: 'product',
          name: `${item.product_code} - ${item.product_description}`,
          client_name: item.client_name,
          quantity_on_hand: item.quantity_on_hand || 0,
          purchase_cost: item.purchase_cost || 0,
          unit_of_measure: item.unit_of_measure || 'units',
          width_mm: item.width_mm || 0,
          product_type: item.product_type,
          original_data: item
        })),
        ...materials.map(item => ({
          id: item.material_id || item.id,
          type: 'material',
          name: `${item.product_code || ''} - ${item.material_description || item.supplier || 'Unknown'}`,
          supplier: item.supplier,
          quantity_on_hand: item.quantity_on_hand || 0,
          purchase_cost: item.cost_per_tonne || item.price || 0,
          unit_of_measure: item.unit_of_measure || 'kg',
          width_mm: item.width_mm || item.master_deckle_width_mm || 0,
          original_data: item
        }))
      ];
      
      setManualStockTakeItems(allItems);
      setStockTakeModifications({});
    } catch (error) {
      console.error('Failed to load stock take items:', error);
      toast.error('Failed to load stock items');
    } finally {
      setManualStockTakeLoading(false);
    }
  };

  const confirmQuantity = async (itemId) => {
    const item = manualStockTakeItems.find(i => i.id === itemId);
    if (!item) return;
    
    toast.success(`Quantity confirmed for ${item.name}`);
    
    // Mark as confirmed in UI
    setStockTakeModifications(prev => ({
      ...prev,
      [itemId]: { confirmed: true, modified: false }
    }));
  };

  const modifyStockOnHand = async (itemId) => {
    const item = manualStockTakeItems.find(i => i.id === itemId);
    const newQuantity = stockTakeModifications[itemId]?.newQuantity;
    
    if (!item || newQuantity === undefined || newQuantity === '') {
      toast.error('Please enter a valid quantity');
      return;
    }
    
    try {
      const endpoint = item.type === 'product' 
        ? `/stock/raw-substrates/${item.id}`
        : `/stock/raw-materials/${item.id}`;
      
      const updateData = {
        ...item.original_data,
        quantity_on_hand: parseFloat(newQuantity)
      };
      
      await apiHelpers.put(endpoint, updateData);
      
      // Update local state
      setManualStockTakeItems(prev => prev.map(i => 
        i.id === itemId ? { ...i, quantity_on_hand: parseFloat(newQuantity) } : i
      ));
      
      setStockTakeModifications(prev => ({
        ...prev,
        [itemId]: { confirmed: true, modified: true, newQuantity: undefined }
      }));
      
      toast.success(`Stock updated for ${item.name}`);
    } catch (error) {
      console.error('Failed to update stock:', error);
      toast.error('Failed to update stock quantity');
    }
  };

  const saveManualStockTake = async () => {
    if (!manualStockTakeMonth) {
      toast.error('Please select a month for this stock take');
      return;
    }
    
    const confirmedCount = Object.values(stockTakeModifications).filter(m => m.confirmed).length;
    const totalCount = manualStockTakeItems.length;
    
    if (confirmedCount < totalCount) {
      const proceed = window.confirm(
        `Only ${confirmedCount} out of ${totalCount} items have been confirmed. Do you want to save anyway?`
      );
      if (!proceed) return;
    }
    
    try {
      // Calculate spiral cores summary
      const coresSummary = calculateSpiralCoresSummary();
      
      // Prepare stocktake data
      const stocktakeData = {
        month: manualStockTakeMonth,
        items: manualStockTakeItems.map(item => ({
          ...item,
          confirmed: stockTakeModifications[item.id]?.confirmed || false,
          modified: stockTakeModifications[item.id]?.modified || false
        })),
        summary: {
          total_items: totalCount,
          confirmed_count: confirmedCount,
          modified_count: Object.values(stockTakeModifications).filter(m => m.modified).length
        },
        spiral_cores_summary: coresSummary
      };
      
      const response = await fetch('/api/stock/manual-stocktakes', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(stocktakeData)
      });
      
      if (response.ok) {
        toast.success(`Manual stock take for ${manualStockTakeMonth} saved successfully`);
        setShowManualStockTake(false);
        // Reset form
        setManualStockTakeItems([]);
        setStockTakeModifications({});
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to save stocktake');
      }
    } catch (error) {
      console.error('Failed to save stocktake:', error);
      toast.error('Failed to save stocktake');
    }
  };

  const loadArchivedStocktakes = async () => {
    try {
      setLoadingArchived(true);
      const response = await fetch('/api/stock/manual-stocktakes', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setArchivedStocktakes(data.data || []);
      }
    } catch (error) {
      console.error('Failed to load archived stocktakes:', error);
      toast.error('Failed to load archived stocktakes');
    } finally {
      setLoadingArchived(false);
    }
  };

  const viewStocktake = async (stocktakeId) => {
    try {
      const response = await fetch(`/api/stock/manual-stocktakes/${stocktakeId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setViewingStocktake(data.data);
      }
    } catch (error) {
      console.error('Failed to load stocktake:', error);
      toast.error('Failed to load stocktake');
    }
  };

  const editStocktake = async (stocktakeId) => {
    try {
      const response = await fetch(`/api/stock/manual-stocktakes/${stocktakeId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        const stocktake = data.data;
        
        // Load stocktake into manual stock take form
        setManualStockTakeMonth(stocktake.month);
        setManualStockTakeItems(stocktake.items);
        
        // Restore modifications
        const modifications = {};
        stocktake.items.forEach(item => {
          if (item.confirmed || item.modified) {
            modifications[item.id] = {
              confirmed: item.confirmed,
              modified: item.modified
            };
          }
        });
        setStockTakeModifications(modifications);
        
        setShowArchivedStocktakes(false);
        setShowManualStockTake(true);
      }
    } catch (error) {
      console.error('Failed to load stocktake for editing:', error);
      toast.error('Failed to load stocktake');
    }
  };

  const deleteStocktake = async (stocktakeId) => {
    if (!window.confirm('Are you sure you want to delete this stocktake? This action cannot be undone.')) {
      return;
    }
    
    try {
      const response = await fetch(`/api/stock/manual-stocktakes/${stocktakeId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.ok) {
        toast.success('Stocktake deleted successfully');
        loadArchivedStocktakes(); // Reload list
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to delete stocktake');
      }
    } catch (error) {
      console.error('Failed to delete stocktake:', error);
      toast.error('Failed to delete stocktake');
    }
  };

  const exportArchivedStocktakeToCSV = (stocktake) => {
    const headers = ['Type', 'Item Name', 'Client/Supplier', 'Quantity On Hand', 'Purchase Cost', 'Unit', 'Status'];
    const rows = stocktake.items.map(item => [
      item.type === 'product' ? 'Product' : 'Material',
      item.name,
      item.client_name || item.supplier || '',
      item.quantity_on_hand,
      item.purchase_cost || 0,
      item.unit_of_measure,
      item.confirmed ? 'Confirmed' : 'Pending'
    ]);
    
    // Add spiral cores summary if available
    if (stocktake.spiral_cores_summary && stocktake.spiral_cores_summary.length > 0) {
      rows.push([]);
      rows.push(['SPIRAL PAPER CORES SUMMARY']);
      rows.push(['Width (mm)', 'Quantity', 'Total m²', '% of Master Deckle']);
      stocktake.spiral_cores_summary.forEach(group => {
        rows.push([
          group.width_mm,
          group.quantity,
          group.total_m2.toFixed(2),
          group.percent_of_master.toFixed(2) + '%'
        ]);
      });
    }
    
    const csvContent = [
      ['Manual Stock Take - ' + stocktake.month],
      ['Created: ' + new Date(stocktake.created_at).toLocaleString()],
      [],
      headers,
      ...rows
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `stock-take-${stocktake.month}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    toast.success('CSV exported successfully');
  };

  const exportArchivedStocktakeToPDF = (stocktake) => {
    const printWindow = window.open('', '_blank');
    
    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Manual Stock Take - ${stocktake.month}</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          h1 { color: #333; }
          h2 { color: #666; margin-top: 30px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #4CAF50; color: white; }
          tr:nth-child(even) { background-color: #f2f2f2; }
          .confirmed { background-color: #d4edda; }
          .summary { background-color: #fff3cd; }
          .total-row { font-weight: bold; background-color: #e9ecef; }
        </style>
      </head>
      <body>
        <h1>Manual Stock Take</h1>
        <p><strong>Month:</strong> ${stocktake.month}</p>
        <p><strong>Created:</strong> ${new Date(stocktake.created_at).toLocaleString()}</p>
        <p><strong>Total Items:</strong> ${stocktake.summary.total_items}</p>
        <p><strong>Confirmed:</strong> ${stocktake.summary.confirmed_count}</p>
        
        <h2>Products On Hand</h2>
        <table>
          <thead>
            <tr>
              <th>Product</th>
              <th>Client</th>
              <th>Quantity</th>
              <th>Purchase Cost</th>
              <th>Unit</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${stocktake.items.filter(i => i.type === 'product').map(item => `
              <tr class="${item.confirmed ? 'confirmed' : ''}">
                <td>${item.name}</td>
                <td>${item.client_name || ''}</td>
                <td>${item.quantity_on_hand}</td>
                <td>$${(item.purchase_cost || 0).toFixed(2)}</td>
                <td>${item.unit_of_measure}</td>
                <td>${item.confirmed ? '✓ Confirmed' : 'Pending'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        
        <h2>Raw Materials On Hand</h2>
        <table>
          <thead>
            <tr>
              <th>Material</th>
              <th>Supplier</th>
              <th>Quantity</th>
              <th>Purchase Cost</th>
              <th>Unit</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${stocktake.items.filter(i => i.type === 'material').map(item => `
              <tr class="${item.confirmed ? 'confirmed' : ''}">
                <td>${item.name}</td>
                <td>${item.supplier || ''}</td>
                <td>${item.quantity_on_hand}</td>
                <td>$${(item.purchase_cost || 0).toFixed(2)}</td>
                <td>${item.unit_of_measure}</td>
                <td>${item.confirmed ? '✓ Confirmed' : 'Pending'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        
        ${stocktake.spiral_cores_summary && stocktake.spiral_cores_summary.length > 0 ? `
          <h2>Spiral Paper Cores Summary</h2>
          <table>
            <thead>
              <tr>
                <th>Width (mm)</th>
                <th>Quantity</th>
                <th>Total m²</th>
                <th>% of Master Deckle (1500mm)</th>
              </tr>
            </thead>
            <tbody>
              ${stocktake.spiral_cores_summary.map(group => `
                <tr class="summary">
                  <td>${group.width_mm} mm</td>
                  <td>${group.quantity}</td>
                  <td>${group.total_m2.toFixed(2)} m²</td>
                  <td>${group.percent_of_master.toFixed(2)}%</td>
                </tr>
              `).join('')}
              <tr class="total-row">
                <td>TOTAL</td>
                <td>${stocktake.spiral_cores_summary.reduce((sum, g) => sum + g.quantity, 0)}</td>
                <td>${stocktake.spiral_cores_summary.reduce((sum, g) => sum + g.total_m2, 0).toFixed(2)} m²</td>
                <td>-</td>
              </tr>
            </tbody>
          </table>
        ` : ''}
      </body>
      </html>
    `;
    
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    printWindow.focus();
    
    setTimeout(() => {
      printWindow.print();
    }, 250);
    
    toast.success('PDF generation initiated');
  };

  const calculateSpiralCoresSummary = () => {
    // Filter for Spiral Paper Cores
    const spiralCores = manualStockTakeItems.filter(item => 
      item.type === 'product' && 
      (item.product_type === 'Spiral Paper Core' || item.name.toLowerCase().includes('core'))
    );
    
    // Group by width
    const widthGroups = {};
    spiralCores.forEach(core => {
      const width = core.width_mm || 0;
      if (width > 0) {
        if (!widthGroups[width]) {
          widthGroups[width] = {
            width_mm: width,
            quantity: 0,
            items: []
          };
        }
        widthGroups[width].quantity += core.quantity_on_hand;
        widthGroups[width].items.push(core);
      }
    });
    
    // Calculate total m² and % of master deckle (assuming 1500mm standard master deckle)
    const masterDeckleWidth = 1500; // mm
    const results = Object.values(widthGroups).map(group => {
      // Assuming each core has a standard length (e.g., 1m per unit for calculation)
      const assumedLengthPerUnit = 1; // meter
      const totalLength = group.quantity * assumedLengthPerUnit;
      const totalM2 = (group.width_mm / 1000) * totalLength;
      const percentOfMasterDeckle = (group.width_mm / masterDeckleWidth) * 100;
      
      return {
        ...group,
        total_m2: totalM2,
        percent_of_master: percentOfMasterDeckle
      };
    });
    
    return results.sort((a, b) => a.width_mm - b.width_mm);
  };

  const exportStockTakeToCSV = () => {
    const headers = ['Type', 'Item Name', 'Client/Supplier', 'Quantity On Hand', 'Purchase Cost', 'Unit', 'Status'];
    const rows = manualStockTakeItems.map(item => [
      item.type === 'product' ? 'Product' : 'Material',
      item.name,
      item.client_name || item.supplier || '',
      item.quantity_on_hand,
      item.purchase_cost || 0,
      item.unit_of_measure,
      stockTakeModifications[item.id]?.confirmed ? 'Confirmed' : 'Pending'
    ]);
    
    // Add spiral cores summary
    const coresSummary = calculateSpiralCoresSummary();
    if (coresSummary.length > 0) {
      rows.push([]);
      rows.push(['SPIRAL PAPER CORES SUMMARY']);
      rows.push(['Width (mm)', 'Quantity', 'Total m²', '% of Master Deckle']);
      coresSummary.forEach(group => {
        rows.push([
          group.width_mm,
          group.quantity,
          group.total_m2.toFixed(2),
          group.percent_of_master.toFixed(2) + '%'
        ]);
      });
    }
    
    const csvContent = [
      ['Manual Stock Take - ' + manualStockTakeMonth],
      ['Generated: ' + new Date().toLocaleString()],
      [],
      headers,
      ...rows
    ].map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `stock-take-${manualStockTakeMonth}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
    toast.success('CSV exported successfully');
  };

  const exportStockTakeToPDF = () => {
    // Create printable content
    const printWindow = window.open('', '_blank');
    const coresSummary = calculateSpiralCoresSummary();
    
    const htmlContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Manual Stock Take - ${manualStockTakeMonth}</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 20px; }
          h1 { color: #333; }
          h2 { color: #666; margin-top: 30px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #4CAF50; color: white; }
          tr:nth-child(even) { background-color: #f2f2f2; }
          .confirmed { background-color: #d4edda; }
          .summary { background-color: #fff3cd; }
          .total-row { font-weight: bold; background-color: #e9ecef; }
        </style>
      </head>
      <body>
        <h1>Manual Stock Take</h1>
        <p><strong>Month:</strong> ${manualStockTakeMonth}</p>
        <p><strong>Generated:</strong> ${new Date().toLocaleString()}</p>
        <p><strong>Progress:</strong> ${Object.values(stockTakeModifications).filter(m => m.confirmed).length} / ${manualStockTakeItems.length} items confirmed</p>
        
        <h2>Products On Hand</h2>
        <table>
          <thead>
            <tr>
              <th>Product</th>
              <th>Client</th>
              <th>Quantity</th>
              <th>Purchase Cost</th>
              <th>Unit</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${manualStockTakeItems.filter(i => i.type === 'product').map(item => `
              <tr class="${stockTakeModifications[item.id]?.confirmed ? 'confirmed' : ''}">
                <td>${item.name}</td>
                <td>${item.client_name || ''}</td>
                <td>${item.quantity_on_hand}</td>
                <td>$${(item.purchase_cost || 0).toFixed(2)}</td>
                <td>${item.unit_of_measure}</td>
                <td>${stockTakeModifications[item.id]?.confirmed ? '✓ Confirmed' : 'Pending'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        
        <h2>Raw Materials On Hand</h2>
        <table>
          <thead>
            <tr>
              <th>Material</th>
              <th>Supplier</th>
              <th>Quantity</th>
              <th>Purchase Cost</th>
              <th>Unit</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            ${manualStockTakeItems.filter(i => i.type === 'material').map(item => `
              <tr class="${stockTakeModifications[item.id]?.confirmed ? 'confirmed' : ''}">
                <td>${item.name}</td>
                <td>${item.supplier || ''}</td>
                <td>${item.quantity_on_hand}</td>
                <td>$${(item.purchase_cost || 0).toFixed(2)}</td>
                <td>${item.unit_of_measure}</td>
                <td>${stockTakeModifications[item.id]?.confirmed ? '✓ Confirmed' : 'Pending'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        
        ${coresSummary.length > 0 ? `
          <h2>Spiral Paper Cores Summary</h2>
          <table>
            <thead>
              <tr>
                <th>Width (mm)</th>
                <th>Quantity</th>
                <th>Total m²</th>
                <th>% of Master Deckle (1500mm)</th>
              </tr>
            </thead>
            <tbody>
              ${coresSummary.map(group => `
                <tr class="summary">
                  <td>${group.width_mm} mm</td>
                  <td>${group.quantity}</td>
                  <td>${group.total_m2.toFixed(2)} m²</td>
                  <td>${group.percent_of_master.toFixed(2)}%</td>
                </tr>
              `).join('')}
              <tr class="total-row">
                <td>TOTAL</td>
                <td>${coresSummary.reduce((sum, g) => sum + g.quantity, 0)}</td>
                <td>${coresSummary.reduce((sum, g) => sum + g.total_m2, 0).toFixed(2)} m²</td>
                <td>-</td>
              </tr>
            </tbody>
          </table>
        ` : ''}
      </body>
      </html>
    `;
    
    printWindow.document.write(htmlContent);
    printWindow.document.close();
    printWindow.focus();
    
    setTimeout(() => {
      printWindow.print();
    }, 250);
    
    toast.success('PDF generation initiated');
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
            <h1 className="text-3xl font-bold text-white mb-2">Stock Management System</h1>
            <p className="text-gray-400">Manage inventory, stocktakes, and stock alerts</p>
          </div>
          <div className="flex items-center space-x-4">
            {stockAlerts.length > 0 && (
              <div className="bg-red-900/20 border border-red-500 rounded-lg p-3 flex items-center">
                <BellIcon className="h-5 w-5 text-red-400 mr-2" />
                <span className="text-red-300 text-sm">{(stockAlerts || []).length} stock alert{(stockAlerts || []).length > 1 ? 's' : ''}</span>
              </div>
            )}
            {isFirstBusinessDay && stocktakeRequired && (
              <div className="bg-yellow-900/20 border border-yellow-500 rounded-lg p-3 flex items-center">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mr-2" />
                <span className="text-yellow-300 text-sm">Stocktake required today!</span>
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <nav className="flex space-x-1 bg-gray-800 p-1 rounded-lg">
            {[
              { id: 'monthly', label: 'Monthly Stocktake', icon: CalendarIcon },
              { id: 'raw_substrates', label: 'Products On Hand', icon: ClipboardDocumentListIcon },
              { id: 'raw_materials', label: 'Raw Materials On Hand', icon: CheckCircleIcon }
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === id
                    ? 'bg-yellow-500 text-black'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700'
                }`}
              >
                <Icon className="h-4 w-4 mr-2" />
                {label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'monthly' && (
          <div className="space-y-6">
            {/* Manual Stock Take & Archived Stocktakes Buttons */}
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-1">Manual Stock Take</h3>
                  <p className="text-sm text-gray-400">Conduct a manual inventory count for any month</p>
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={() => {
                      setShowManualStockTake(true);
                      loadManualStockTakeItems();
                      // Set default month to current month
                      const now = new Date();
                      setManualStockTakeMonth(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`);
                    }}
                    className="misty-button misty-button-secondary"
                  >
                    <ClipboardDocumentListIcon className="h-5 w-5 mr-2" />
                    Manual Stock Take
                  </button>
                  <button
                    onClick={() => {
                      setShowArchivedStocktakes(true);
                      loadArchivedStocktakes();
                    }}
                    className="misty-button misty-button-secondary"
                  >
                    <CubeIcon className="h-5 w-5 mr-2" />
                    Archived Stocktakes
                  </button>
                </div>
              </div>
            </div>

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
        )}

        {/* Raw Substrates Tab */}
        {activeTab === 'raw_substrates' && (
          <div className="space-y-6">
            {/* Header with filter and actions */}
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-white">Products On Hand</h2>
                <div className="flex items-center space-x-4">
                  <button
                    onClick={checkLowStock}
                    className="misty-button misty-button-secondary"
                  >
                    <BellIcon className="h-4 w-4 mr-2" />
                    Check Low Stock
                  </button>
                  <button
                    onClick={() => setShowSubstrateModal(true)}
                    className="misty-button misty-button-primary"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add Product Entry
                  </button>
                </div>
              </div>

              {/* Client Filter */}
              <div className="flex items-center space-x-4">
                <label className="text-sm text-gray-300">Filter by Client:</label>
                <select
                  value={selectedClient}
                  onChange={(e) => setSelectedClient(e.target.value)}
                  className="misty-select w-48"
                >
                  <option value="all">All Clients</option>
                  {clients.map(client => (
                    <option key={client.id} value={client.id}>{client.company_name}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Grouped Stock Table */}
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              <div className="p-4 border-b border-gray-700">
                <h3 className="text-lg font-semibold text-white">Grouped Products ({groupedProducts.length})</h3>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Client</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Product</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Code</th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-300">Available</th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-300">Allocated</th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-300">Total</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Unit</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {groupedProducts.map((product) => (
                      <tr key={`${product.product_id}-${product.client_id}`} className="hover:bg-gray-700">
                        <td className="px-4 py-3 text-sm text-white">{product.client_name}</td>
                        <td className="px-4 py-3">
                          <div className="text-sm text-white">{product.product_description}</div>
                          {product.is_shared_product && (
                            <div className="text-xs text-blue-400">Shared Product</div>
                          )}
                          <div className="text-xs text-gray-400">{product.entries.length} stock entries</div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-300">{product.product_code}</td>
                        <td className="px-4 py-3 text-right">
                          <span className={`text-sm font-medium ${
                            product.available_quantity <= product.minimum_stock_level ? 'text-red-400' : 'text-green-400'
                          }`}>
                            {product.available_quantity}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className="text-sm text-yellow-400 font-medium">
                            {product.allocated_quantity}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className="text-sm text-white font-medium">
                            {product.total_quantity}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-300">{product.unit_of_measure}</td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex items-center justify-center space-x-2">
                            <button 
                              className="text-blue-400 hover:text-blue-300 flex items-center text-xs"
                              onClick={() => loadStockHistory(product.product_id, product.client_id)}
                              title="View Stock History"
                            >
                              <ClockIcon className="h-4 w-4 mr-1" />
                              History
                            </button>
                            <button 
                              className="text-purple-400 hover:text-purple-300 flex items-center text-xs"
                              onClick={() => loadStockAllocations(product.product_id, product.client_id)}
                              title="View Allocations"
                            >
                              <CubeIcon className="h-4 w-4 mr-1" />
                              Allocations
                            </button>
                            <button 
                              className="text-yellow-400 hover:text-yellow-300"
                              onClick={() => {
                                setSelectedItem(product);
                                setSelectedItemType('substrate');
                                setShowEditModal(true);
                              }}
                              title="Edit"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                {(!groupedProducts || groupedProducts.length === 0) && (
                  <div className="p-8 text-center text-gray-400">
                    <ClipboardDocumentListIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No grouped products found</p>
                    <p className="text-sm">Add stock entries from Job Card excess production or manually</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Raw Materials Tab */}
        {activeTab === 'raw_materials' && (
          <div className="space-y-6">
            {/* Header with actions */}
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-white">Raw Materials On Hand</h2>
                <div className="flex items-center space-x-4">
                  <button
                    onClick={checkLowStock}
                    className="misty-button misty-button-secondary"
                  >
                    <BellIcon className="h-4 w-4 mr-2" />
                    Check Low Stock
                  </button>
                  <button
                    onClick={() => setShowMaterialModal(true)}
                    className="misty-button misty-button-primary"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add Material Stock
                  </button>
                </div>
              </div>
            </div>

            {/* Materials Stock Table */}
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              <div className="p-4 border-b border-gray-700">
                <h3 className="text-lg font-semibold text-white">Materials ({(rawMaterialsStock || []).length})</h3>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Material</th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-300">Quantity</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">Unit</th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-300">Min Level</th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-300">Usage/Month</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Alert Days</th>
                      <th className="px-4 py-3 text-center text-sm font-medium text-gray-300">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {(rawMaterialsStock || []).map((material) => (
                      <tr key={material.id} className="hover:bg-gray-700">
                        <td className="px-4 py-3 text-sm">
                          <span 
                            className="text-white cursor-pointer hover:bg-gray-600 px-2 py-1 rounded transition-colors duration-200"
                            onDoubleClick={() => loadSlitWidths(material.material_id, material.material_name)}
                            title="Double-click to view slit widths"
                          >
                            {material.material_name}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          {editingItem === material.id && editingField === 'quantity_on_hand' ? (
                            <input
                              type="number"
                              defaultValue={material.quantity_on_hand}
                              onBlur={(e) => handleFieldSave(material.id, 'quantity_on_hand', e.target.value, 'material')}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  handleFieldSave(material.id, 'quantity_on_hand', e.target.value, 'material');
                                }
                              }}
                              className="misty-input w-20 text-right text-sm"
                              autoFocus
                            />
                          ) : (
                            <span
                              className={`text-sm cursor-pointer hover:bg-gray-600 px-2 py-1 rounded ${
                                material.quantity_on_hand <= material.minimum_stock_level ? 'text-red-400' : 'text-white'
                              }`}
                              onDoubleClick={() => handleDoubleClick(material.id, 'quantity_on_hand')}
                            >
                              {material.quantity_on_hand}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-300">{material.unit_of_measure}</td>
                        <td className="px-4 py-3 text-right">
                          {editingItem === material.id && editingField === 'minimum_stock_level' ? (
                            <input
                              type="number"
                              defaultValue={material.minimum_stock_level}
                              onBlur={(e) => handleFieldSave(material.id, 'minimum_stock_level', e.target.value, 'material')}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  handleFieldSave(material.id, 'minimum_stock_level', e.target.value, 'material');
                                }
                              }}
                              className="misty-input w-20 text-right text-sm"
                              autoFocus
                            />
                          ) : (
                            <span
                              className="text-sm text-gray-300 cursor-pointer hover:bg-gray-600 px-2 py-1 rounded"
                              onDoubleClick={() => handleDoubleClick(material.id, 'minimum_stock_level')}
                            >
                              {material.minimum_stock_level || 0}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right text-sm text-gray-300">
                          {material.usage_rate_per_month || 0}
                        </td>
                        <td className="px-4 py-3 text-center text-sm text-gray-300">
                          {material.alert_threshold_days || 7}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <div className="flex items-center justify-center space-x-2">
                            <button 
                              className="text-blue-400 hover:text-blue-300"
                              onClick={() => handleViewItem(material, 'material')}
                              title="View Details"
                            >
                              <EyeIcon className="h-4 w-4" />
                            </button>
                            <button 
                              className="text-yellow-400 hover:text-yellow-300"
                              onClick={() => handleEditItem(material, 'material')}
                              title="Edit"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button 
                              className="text-red-400 hover:text-red-300"
                              onClick={() => handleDeleteItem(material, 'material')}
                              title="Delete"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                
                {(!rawMaterialsStock || rawMaterialsStock.length === 0) && (
                  <div className="p-8 text-center text-gray-400">
                    <CheckCircleIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>No raw materials found</p>
                    <p className="text-sm">Select from your materials database to track stock levels</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Stock Alerts Panel */}
        {(stockAlerts || []).length > 0 && showStockAlert && (
          <div className="fixed bottom-4 right-4 bg-red-900 border border-red-500 rounded-lg p-4 max-w-sm shadow-lg z-50">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <BellIcon className="h-5 w-5 text-red-400 mr-2" />
                <h4 className="font-medium text-white">Stock Alerts</h4>
              </div>
              <button
                onClick={() => setShowStockAlert(false)}
                className="text-gray-400 hover:text-white"
              >
                ×
              </button>
            </div>
            <div className="space-y-2 mb-3">
              {(stockAlerts || []).slice(0, 3).map((alert) => (
                <div key={alert.id} className="text-sm text-red-200">
                  {alert.message}
                </div>
              ))}
              {(stockAlerts || []).length > 3 && (
                <div className="text-xs text-gray-400">
                  +{(stockAlerts || []).length - 3} more alerts
                </div>
              )}
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => acknowledgeAlert(stockAlerts[0]?.id)}
                className="text-xs bg-red-700 hover:bg-red-600 text-white px-2 py-1 rounded"
              >
                Acknowledge
              </button>
              <button
                onClick={() => acknowledgeAlert(stockAlerts[0]?.id, 24)}
                className="text-xs bg-gray-700 hover:bg-gray-600 text-white px-2 py-1 rounded"
              >
                Snooze 24h
              </button>
            </div>
          </div>
        )}

        {/* View Details Modal */}
        {showViewModal && selectedItem && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-white">
                  {selectedItemType === 'substrate' ? 'Raw Substrate Details' : 'Raw Material Details'}
                </h3>
                <button
                  onClick={() => setShowViewModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                {selectedItemType === 'substrate' ? (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">Client</label>
                        <div className="text-white bg-gray-700 p-2 rounded">{selectedItem.client_name}</div>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">Product Code</label>
                        <div className="text-white bg-gray-700 p-2 rounded">{selectedItem.product_code}</div>
                      </div>
                      <div className="col-span-2">
                        <label className="block text-sm text-gray-300 mb-1">Product Description</label>
                        <div className="text-white bg-gray-700 p-2 rounded">{selectedItem.product_description}</div>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">Quantity on Hand</label>
                        <div className="text-white bg-gray-700 p-2 rounded">{selectedItem.quantity_on_hand} {selectedItem.unit_of_measure}</div>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">Minimum Stock Level</label>
                        <div className="text-white bg-gray-700 p-2 rounded">{selectedItem.minimum_stock_level} {selectedItem.unit_of_measure}</div>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">Source Order</label>
                        <div className="text-white bg-gray-700 p-2 rounded">{selectedItem.source_order_id}</div>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">Shared Product</label>
                        <div className="text-white bg-gray-700 p-2 rounded">
                          {selectedItem.is_shared_product ? 'Yes' : 'No'}
                          {selectedItem.is_shared_product && selectedItem.shared_with_clients && selectedItem.shared_with_clients.length > 0 && (
                            <div className="text-xs text-gray-300 mt-1">
                              Shared with: {selectedItem.shared_with_clients.map(clientId => {
                                const client = clients.find(c => c.id === clientId);
                                return client ? client.company_name : clientId;
                              }).join(', ')}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="col-span-2">
                        <label className="block text-sm text-gray-300 mb-1">Created</label>
                        <div className="text-white bg-gray-700 p-2 rounded">
                          {selectedItem.created_at ? new Date(selectedItem.created_at).toLocaleDateString() : 'N/A'}
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="col-span-2">
                        <label className="block text-sm text-gray-300 mb-1">Material Name</label>
                        <div className="text-white bg-gray-700 p-2 rounded">{selectedItem.material_name}</div>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">Quantity on Hand</label>
                        <div className="text-white bg-gray-700 p-2 rounded">{selectedItem.quantity_on_hand} {selectedItem.unit_of_measure}</div>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">Minimum Stock Level</label>
                        <div className="text-white bg-gray-700 p-2 rounded">{selectedItem.minimum_stock_level} {selectedItem.unit_of_measure}</div>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">Usage per Month</label>
                        <div className="text-white bg-gray-700 p-2 rounded">{selectedItem.usage_rate_per_month} {selectedItem.unit_of_measure}</div>
                      </div>
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">Alert Threshold (Days)</label>
                        <div className="text-white bg-gray-700 p-2 rounded">{selectedItem.alert_threshold_days}</div>
                      </div>
                      <div className="col-span-2">
                        <label className="block text-sm text-gray-300 mb-1">Created</label>
                        <div className="text-white bg-gray-700 p-2 rounded">
                          {selectedItem.created_at ? new Date(selectedItem.created_at).toLocaleDateString() : 'N/A'}
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setShowViewModal(false)}
                  className="misty-button misty-button-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit Modal */}
        {showEditModal && selectedItem && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-white">
                  Edit {selectedItemType === 'substrate' ? 'Raw Substrate' : 'Raw Material'}
                </h3>
                <button
                  onClick={() => setShowEditModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ×
                </button>
              </div>

              <form onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const updatedData = {};
                
                // Handle shared_with_clients array
                const sharedWithClients = [];
                
                for (let [key, value] of formData.entries()) {
                  if (key.includes('quantity') || key.includes('minimum') || key.includes('usage') || key.includes('alert')) {
                    updatedData[key] = parseFloat(value) || 0;
                  } else if (key === 'is_shared_product') {
                    updatedData[key] = formData.get('is_shared_product') === 'on';
                  } else if (key === 'shared_with_clients') {
                    sharedWithClients.push(value);
                  } else {
                    updatedData[key] = value;
                  }
                }
                
                // Add shared_with_clients array to updatedData
                if (selectedItemType === 'substrate') {
                  updatedData.shared_with_clients = updatedData.is_shared_product ? sharedWithClients : [];
                }
                
                handleEditSave(updatedData);
              }}>
                <div className="space-y-4">
                  {selectedItemType === 'substrate' ? (
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm text-gray-300 mb-1">Quantity on Hand</label>
                          <input
                            type="number"
                            step="0.01"
                            name="quantity_on_hand"
                            defaultValue={selectedItem.quantity_on_hand}
                            className="misty-input w-full"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-sm text-gray-300 mb-1">Minimum Stock Level</label>
                          <input
                            type="number"
                            step="0.01"
                            name="minimum_stock_level"
                            defaultValue={selectedItem.minimum_stock_level}
                            className="misty-input w-full"
                          />
                        </div>
                      </div>
                      
                      {/* Shared Product Section */}
                      <div className="col-span-2 space-y-4">
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            id="is_shared_product"
                            name="is_shared_product"
                            defaultChecked={selectedItem.is_shared_product}
                            className="w-4 h-4 text-yellow-500 bg-gray-700 border-gray-600 rounded focus:ring-yellow-500 focus:ring-2"
                            onChange={(e) => {
                              const sharedSection = document.getElementById('shared-clients-section');
                              if (e.target.checked) {
                                sharedSection.style.display = 'block';
                              } else {
                                sharedSection.style.display = 'none';
                                // Uncheck all client checkboxes
                                const clientCheckboxes = sharedSection.querySelectorAll('input[type="checkbox"]');
                                clientCheckboxes.forEach(cb => cb.checked = false);
                              }
                            }}
                          />
                          <label htmlFor="is_shared_product" className="ml-2 text-sm text-gray-300">
                            This is a shared product (available to multiple clients)
                          </label>
                        </div>
                        
                        <div 
                          id="shared-clients-section" 
                          style={{ display: selectedItem.is_shared_product ? 'block' : 'none' }}
                          className="bg-gray-700 p-4 rounded-lg"
                        >
                          <label className="block text-sm text-gray-300 mb-3">
                            Select clients to share this product with:
                          </label>
                          <div className="max-h-40 overflow-y-auto space-y-2">
                            {(clients || []).filter(client => client.id !== selectedItem.client_id).map((client) => (
                              <div key={client.id} className="flex items-center">
                                <input
                                  type="checkbox"
                                  id={`client_${client.id}`}
                                  name="shared_with_clients"
                                  value={client.id}
                                  defaultChecked={(selectedItem.shared_with_clients || []).includes(client.id)}
                                  className="w-4 h-4 text-yellow-500 bg-gray-600 border-gray-500 rounded focus:ring-yellow-500 focus:ring-2"
                                />
                                <label htmlFor={`client_${client.id}`} className="ml-2 text-sm text-white">
                                  {client.company_name}
                                </label>
                              </div>
                            ))}
                            {(!clients || clients.length <= 1) && (
                              <p className="text-gray-400 text-sm italic">No other clients available to share with</p>
                            )}
                          </div>
                          <div className="mt-3 p-2 bg-blue-900/20 border border-blue-500 rounded text-xs text-blue-200">
                            <strong>Note:</strong> Shared products will appear in the selected clients' inventories and can be used for their orders.
                          </div>
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      {/* Material Selection (for reference, read-only in edit mode) */}
                      <div>
                        <label className="block text-sm text-gray-300 mb-1">Selected Material</label>
                        <div className="bg-gray-700 p-3 rounded">
                          <div className="text-white text-sm">{selectedItem.material_name}</div>
                          <div className="text-xs text-gray-400 mt-1">
                            Material ID: {selectedItem.material_id || 'N/A'}
                          </div>
                        </div>
                      </div>

                      {/* Stock Information Grid */}
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm text-gray-300 mb-1">Quantity on Hand *</label>
                          <input
                            type="number"
                            step="0.01"
                            name="quantity_on_hand"
                            defaultValue={selectedItem.quantity_on_hand}
                            className="misty-input w-full"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-sm text-gray-300 mb-1">Unit of Measure *</label>
                          <select
                            name="unit_of_measure"
                            defaultValue={selectedItem.unit_of_measure}
                            className="misty-select w-full"
                          >
                            <option value="kg">Kilograms</option>
                            <option value="tons">Tons</option>
                            <option value="meters">Meters</option>
                            <option value="liters">Liters</option>
                            <option value="units">Units</option>
                            <option value="rolls">Rolls</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm text-gray-300 mb-1">Minimum Stock Level</label>
                          <input
                            type="number"
                            step="0.01"
                            name="minimum_stock_level"
                            defaultValue={selectedItem.minimum_stock_level}
                            className="misty-input w-full"
                          />
                        </div>
                      </div>

                      {/* Usage and Alert Settings Grid */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm text-gray-300 mb-1">Usage Rate (per month)</label>
                          <input
                            type="number"
                            step="0.01"
                            name="usage_rate_per_month"
                            defaultValue={selectedItem.usage_rate_per_month}
                            className="misty-input w-full"
                          />
                        </div>
                        <div>
                          <label className="block text-sm text-gray-300 mb-1">Alert Threshold (Days)</label>
                          <input
                            type="number"
                            name="alert_threshold_days"
                            defaultValue={selectedItem.alert_threshold_days}
                            className="misty-input w-full"
                          />
                        </div>
                      </div>
                    </>
                  )}
                </div>

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="misty-button misty-button-primary"
                  >
                    Save Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && selectedItem && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-white">Confirm Delete</h3>
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ×
                </button>
              </div>

              <div className="mb-6">
                <p className="text-gray-300">
                  Are you sure you want to delete this {selectedItemType === 'substrate' ? 'raw substrate' : 'raw material'}?
                </p>
                <div className="mt-2 p-3 bg-gray-700 rounded">
                  <p className="text-white font-medium">
                    {selectedItemType === 'substrate' ? selectedItem.product_description : selectedItem.material_name}
                  </p>
                  <p className="text-sm text-gray-400">
                    {selectedItem.quantity_on_hand} {selectedItem.unit_of_measure} on hand
                  </p>
                </div>
                <p className="text-red-400 text-sm mt-2">
                  This action cannot be undone. All stock movements and alerts for this item will also be deleted.
                </p>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="misty-button misty-button-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmDelete}
                  className="misty-button misty-button-primary bg-red-600 hover:bg-red-700"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Add Product Entry Modal */}
        {showSubstrateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-white">Add Product Entry</h3>
                <button
                  onClick={() => {
                    setShowSubstrateModal(false);
                    setClientProducts([]); // Reset client products
                  }}
                  className="text-gray-400 hover:text-white"
                >
                  ×
                </button>
              </div>

              <form onSubmit={async (e) => {
                e.preventDefault();
                try {
                  await apiHelpers.post('/stock/raw-substrates', substrateForm);
                  setShowSubstrateModal(false);
                  loadRawSubstrates();
                  toast.success('Product entry added successfully');
                  // Reset form
                  setSubstrateForm({
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
                  setClientProducts([]); // Reset client products
                } catch (error) {
                  console.error('Failed to add product entry:', error);
                  toast.error('Failed to add product entry');
                }
              }}>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">Client *</label>
                      <select
                        value={substrateForm.client_id}
                        onChange={(e) => {
                          const selectedClient = clients.find(c => c.id === e.target.value);
                          console.log('Client selected:', e.target.value, selectedClient); // Debug log
                          setSubstrateForm(prev => {
                            const newForm = {
                              ...prev,
                              client_id: e.target.value,
                              client_name: selectedClient?.company_name || '',
                              product_id: '', // Reset product selection
                              product_code: '',
                              product_description: ''
                            };
                            console.log('Updated substrate form:', newForm); // Debug log
                            return newForm;
                          });
                          // Load products for selected client
                          if (e.target.value) {
                            loadClientProducts(e.target.value);
                          } else {
                            setClientProducts([]);
                          }
                        }}
                        className="misty-select w-full"
                        required
                      >
                        <option value="">Select Client</option>
                        {clients.map(client => (
                          <option key={client.id} value={client.id}>{client.company_name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">Product Code *</label>
                      <input
                        type="text"
                        value={substrateForm.product_code}
                        onChange={(e) => setSubstrateForm(prev => ({ ...prev, product_code: e.target.value }))}
                        className={`misty-input w-full ${substrateForm.product_id ? 'bg-gray-700 text-gray-300' : ''}`}
                        readOnly={substrateForm.product_id ? true : false}
                        placeholder={substrateForm.product_id ? 'Auto-populated from selected product' : 'Enter product code'}
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm text-gray-300 mb-1">Product Description *</label>
                    {substrateForm.client_id && clientProducts.length > 0 ? (
                      <select
                        value={substrateForm.product_id}
                        onChange={(e) => {
                          const selectedProduct = clientProducts.find(p => p.id === e.target.value);
                          if (selectedProduct) {
                            setSubstrateForm(prev => ({
                              ...prev,
                              product_id: e.target.value,
                              product_code: selectedProduct.product_code || '',
                              product_description: selectedProduct.product_description || ''
                            }));
                          } else {
                            setSubstrateForm(prev => ({
                              ...prev,
                              product_id: '',
                              product_code: '',
                              product_description: ''
                            }));
                          }
                        }}
                        className="misty-select w-full"
                        required
                      >
                        <option value="">Select Product from Client Catalogue</option>
                        {clientProducts.map(product => (
                          <option key={product.id} value={product.id}>
                            {product.product_description}
                          </option>
                        ))}
                      </select>
                    ) : substrateForm.client_id && clientProducts.length === 0 ? (
                      <div className="misty-input w-full bg-gray-600 text-gray-300 flex items-center">
                        Loading products...
                      </div>
                    ) : (
                      <div className="misty-input w-full bg-gray-700 text-gray-400 flex items-center">
                        Please select a client first to see their product catalogue
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">Quantity on Hand *</label>
                      <input
                        type="number"
                        step="0.01"
                        value={substrateForm.quantity_on_hand}
                        onChange={(e) => setSubstrateForm(prev => ({ ...prev, quantity_on_hand: parseFloat(e.target.value) || 0 }))}
                        className="misty-input w-full"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">Unit of Measure *</label>
                      <select
                        value={substrateForm.unit_of_measure}
                        onChange={(e) => setSubstrateForm(prev => ({ ...prev, unit_of_measure: e.target.value }))}
                        className="misty-select w-full"
                      >
                        <option value="units">Units</option>
                        <option value="pieces">Pieces</option>
                        <option value="cores">Cores</option>
                        <option value="tubes">Tubes</option>
                        <option value="meters">Meters</option>
                        <option value="kg">Kilograms</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">Minimum Stock Level</label>
                      <input
                        type="number"
                        step="0.01"
                        value={substrateForm.minimum_stock_level}
                        onChange={(e) => setSubstrateForm(prev => ({ ...prev, minimum_stock_level: parseFloat(e.target.value) || 0 }))}
                        className="misty-input w-full"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm text-gray-300 mb-1">Source Order ID</label>
                    <input
                      type="text"
                      value={substrateForm.source_order_id}
                      onChange={(e) => setSubstrateForm(prev => ({ ...prev, source_order_id: e.target.value }))}
                      className="misty-input w-full"
                      placeholder="Order that created this stock (optional)"
                    />
                  </div>
                </div>

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => {
                      setShowSubstrateModal(false);
                      setClientProducts([]); // Reset client products
                    }}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="misty-button misty-button-primary"
                  >
                    Add Entry
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Add Material Stock Modal */}
        {showMaterialModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-white">Add Raw Material Stock</h3>
                <button
                  onClick={() => setShowMaterialModal(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ×
                </button>
              </div>

              <form onSubmit={async (e) => {
                e.preventDefault();
                try {
                  await apiHelpers.post('/stock/raw-materials', materialForm);
                  setShowMaterialModal(false);
                  loadRawMaterialsStock();
                  toast.success('Raw material stock added successfully');
                  // Reset form
                  setMaterialForm({
                    material_id: '',
                    material_name: '',
                    quantity_on_hand: 0,
                    unit_of_measure: 'kg',
                    minimum_stock_level: 0,
                    alert_threshold_days: 7,
                    supplier_id: '',
                    usage_rate_per_month: 0
                  });
                } catch (error) {
                  console.error('Failed to add raw material stock:', error);
                  toast.error('Failed to add raw material stock');
                }
              }}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-300 mb-1">Select Material *</label>
                    <select
                      value={materialForm.material_id}
                      onChange={(e) => {
                        const selectedMaterial = availableMaterials.find(m => m.id === e.target.value);
                        if (selectedMaterial) {
                          setMaterialForm(prev => ({
                            ...prev,
                            material_id: e.target.value,
                            material_name: `${selectedMaterial.supplier} - ${selectedMaterial.product_code}`,
                            unit_of_measure: selectedMaterial.unit || 'kg'
                          }));
                        }
                      }}
                      className="misty-select w-full"
                      required
                    >
                      <option value="">Select Material from Database</option>
                      {availableMaterials.map(material => (
                        <option key={material.id} value={material.id}>
                          {material.supplier} - {material.product_code} ({material.gsm}GSM {material.thickness}mm)
                        </option>
                      ))}
                    </select>
                  </div>
                  {materialForm.material_name && (
                    <div className="bg-gray-700 p-3 rounded">
                      <label className="block text-sm text-gray-300 mb-1">Selected Material</label>
                      <div className="text-white text-sm">{materialForm.material_name}</div>
                    </div>
                  )}

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">Quantity on Hand *</label>
                      <input
                        type="number"
                        step="0.01"
                        value={materialForm.quantity_on_hand}
                        onChange={(e) => setMaterialForm(prev => ({ ...prev, quantity_on_hand: parseFloat(e.target.value) || 0 }))}
                        className="misty-input w-full"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">Unit of Measure *</label>
                      <select
                        value={materialForm.unit_of_measure}
                        onChange={(e) => setMaterialForm(prev => ({ ...prev, unit_of_measure: e.target.value }))}
                        className="misty-select w-full"
                      >
                        <option value="kg">Kilograms</option>
                        <option value="tons">Tons</option>
                        <option value="meters">Meters</option>
                        <option value="liters">Liters</option>
                        <option value="units">Units</option>
                        <option value="rolls">Rolls</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">Minimum Stock Level</label>
                      <input
                        type="number"
                        step="0.01"
                        value={materialForm.minimum_stock_level}
                        onChange={(e) => setMaterialForm(prev => ({ ...prev, minimum_stock_level: parseFloat(e.target.value) || 0 }))}
                        className="misty-input w-full"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">Usage Rate (per month)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={materialForm.usage_rate_per_month}
                        onChange={(e) => setMaterialForm(prev => ({ ...prev, usage_rate_per_month: parseFloat(e.target.value) || 0 }))}
                        className="misty-input w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-sm text-gray-300 mb-1">Alert Threshold (Days)</label>
                      <input
                        type="number"
                        value={materialForm.alert_threshold_days}
                        onChange={(e) => setMaterialForm(prev => ({ ...prev, alert_threshold_days: parseInt(e.target.value) || 7 }))}
                        className="misty-input w-full"
                      />
                    </div>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowMaterialModal(false)}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="misty-button misty-button-primary"
                  >
                    Add Material
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Stock History Modal */}
        {showStockHistory && selectedStockHistory && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-white">Stock History</h3>
                <button
                  onClick={() => setShowStockHistory(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="mb-4 p-4 bg-gray-700 rounded-lg">
                <h4 className="text-lg font-medium text-white mb-2">Summary</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-300">Total Stock Entries:</span>
                    <div className="font-medium text-white">{selectedStockHistory.total_entries}</div>
                  </div>
                  <div>
                    <span className="text-gray-300">Total Quantity:</span>
                    <div className="font-medium text-white">{selectedStockHistory.total_quantity}</div>
                  </div>
                  <div>
                    <span className="text-gray-300">Total Movements:</span>
                    <div className="font-medium text-white">{selectedStockHistory.movements?.length || 0}</div>
                  </div>
                </div>
              </div>

              <div className="space-y-6">
                {/* Stock Entries */}
                <div>
                  <h4 className="text-lg font-medium text-white mb-3">Stock Entries</h4>
                  <div className="bg-gray-700 rounded-lg overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-gray-600">
                        <tr>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-300">Source Order</th>
                          <th className="px-4 py-2 text-right text-sm font-medium text-gray-300">Quantity</th>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-300">Unit</th>
                          <th className="px-4 py-2 text-left text-sm font-medium text-gray-300">Added Date</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-600">
                        {selectedStockHistory.stock_entries?.map((entry, index) => (
                          <tr key={index} className="hover:bg-gray-600">
                            <td className="px-4 py-2 text-sm text-white">{entry.source_order_id || 'Manual Entry'}</td>
                            <td className="px-4 py-2 text-right text-sm text-white">{entry.quantity_on_hand}</td>
                            <td className="px-4 py-2 text-sm text-gray-300">{entry.unit_of_measure}</td>
                            <td className="px-4 py-2 text-sm text-gray-300">
                              {entry.created_at ? new Date(entry.created_at).toLocaleDateString() : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Stock Movements */}
                {selectedStockHistory.movements && selectedStockHistory.movements.length > 0 && (
                  <div>
                    <h4 className="text-lg font-medium text-white mb-3">Recent Movements</h4>
                    <div className="bg-gray-700 rounded-lg overflow-hidden">
                      <table className="w-full">
                        <thead className="bg-gray-600">
                          <tr>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-300">Type</th>
                            <th className="px-4 py-2 text-right text-sm font-medium text-gray-300">Quantity</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-300">Reference</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-300">Date</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-600">
                          {selectedStockHistory.movements.slice(0, 10).map((movement, index) => (
                            <tr key={index} className="hover:bg-gray-600">
                              <td className="px-4 py-2 text-sm">
                                <span className={`px-2 py-1 rounded text-xs ${
                                  movement.movement_type === 'allocation' ? 'bg-red-600 text-white' :
                                  movement.movement_type === 'adjustment' ? 'bg-blue-600 text-white' :
                                  'bg-green-600 text-white'
                                }`}>
                                  {movement.movement_type}
                                </span>
                              </td>
                              <td className={`px-4 py-2 text-right text-sm font-medium ${
                                movement.quantity < 0 ? 'text-red-400' : 'text-green-400'
                              }`}>
                                {movement.quantity > 0 ? '+' : ''}{movement.quantity}
                              </td>
                              <td className="px-4 py-2 text-sm text-gray-300">{movement.reference}</td>
                              <td className="px-4 py-2 text-sm text-gray-300">
                                {movement.created_at ? new Date(movement.created_at).toLocaleDateString() : 'N/A'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setShowStockHistory(false)}
                  className="misty-button misty-button-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Stock Allocations Modal */}
        {stockAllocations && stockAllocations.length > 0 && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-3xl max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-white">Stock Allocations</h3>
                <button
                  onClick={() => setStockAllocations([])}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="mb-4 p-4 bg-gray-700 rounded-lg">
                <h4 className="text-lg font-medium text-white mb-2">Allocation Summary</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-300">Active Orders:</span>
                    <div className="font-medium text-white">{stockAllocations.length}</div>
                  </div>
                  <div>
                    <span className="text-gray-300">Total Allocated:</span>
                    <div className="font-medium text-yellow-400">
                      {stockAllocations.reduce((sum, alloc) => sum + Math.abs(alloc.quantity), 0)} units
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-gray-700 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-600">
                    <tr>
                      <th className="px-4 py-2 text-left text-sm font-medium text-gray-300">Order Reference</th>
                      <th className="px-4 py-2 text-right text-sm font-medium text-gray-300">Allocated Qty</th>
                      <th className="px-4 py-2 text-left text-sm font-medium text-gray-300">Allocated Date</th>
                      <th className="px-4 py-2 text-center text-sm font-medium text-gray-300">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-600">
                    {stockAllocations.map((allocation, index) => (
                      <tr key={index} className="hover:bg-gray-600">
                        <td className="px-4 py-2 text-sm text-white">{allocation.reference}</td>
                        <td className="px-4 py-2 text-right text-sm text-yellow-400 font-medium">
                          {Math.abs(allocation.quantity)}
                        </td>
                        <td className="px-4 py-2 text-sm text-gray-300">
                          {allocation.created_at ? new Date(allocation.created_at).toLocaleDateString() : 'N/A'}
                        </td>
                        <td className="px-4 py-2 text-center">
                          <span className="px-2 py-1 bg-yellow-600 text-white text-xs rounded">
                            Active
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-between mt-6">
                <button
                  onClick={loadArchivedAllocations}
                  className="misty-button misty-button-primary"
                >
                  View Archived Allocations
                </button>
                <button
                  onClick={() => {
                    setStockAllocations([]);
                    setCurrentAllocationProduct(null);
                  }}
                  className="misty-button misty-button-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Archived Allocations Modal */}
        {showArchivedAllocations && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-3xl max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-white">Archived Stock Allocations</h3>
                <button
                  onClick={() => {
                    setShowArchivedAllocations(false);
                    setArchivedAllocations([]);
                  }}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="mb-4 p-4 bg-gray-700 rounded-lg">
                <h4 className="text-lg font-medium text-white mb-2">Archive Summary</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-300">Completed Orders:</span>
                    <div className="font-medium text-white">{archivedAllocations.length}</div>
                  </div>
                  <div>
                    <span className="text-gray-300">Total Historical Allocations:</span>
                    <div className="font-medium text-blue-400">
                      {archivedAllocations.reduce((sum, alloc) => sum + Math.abs(alloc.quantity), 0)} units
                    </div>
                  </div>
                </div>
              </div>

              {archivedAllocations && archivedAllocations.length > 0 ? (
                <div className="bg-gray-700 rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-600">
                      <tr>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-300">Order Reference</th>
                        <th className="px-4 py-2 text-right text-sm font-medium text-gray-300">Allocated Qty</th>
                        <th className="px-4 py-2 text-left text-sm font-medium text-gray-300">Allocated Date</th>
                        <th className="px-4 py-2 text-center text-sm font-medium text-gray-300">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-600">
                      {archivedAllocations.map((allocation, index) => (
                        <tr key={index} className="hover:bg-gray-600">
                          <td className="px-4 py-2 text-sm text-white">{allocation.reference}</td>
                          <td className="px-4 py-2 text-right text-sm text-blue-400 font-medium">
                            {Math.abs(allocation.quantity)}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-300">
                            {allocation.created_at ? new Date(allocation.created_at).toLocaleDateString() : 'N/A'}
                          </td>
                          <td className="px-4 py-2 text-center">
                            <span className="px-2 py-1 bg-blue-600 text-white text-xs rounded">
                              Completed
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="bg-gray-700 rounded-lg p-8 text-center">
                  <p className="text-gray-300 text-lg">No archived allocations found</p>
                  <p className="text-gray-400 text-sm mt-2">
                    Archived allocations will appear here once orders are completed and invoiced
                  </p>
                </div>
              )}

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => {
                    setShowArchivedAllocations(false);
                    setArchivedAllocations([]);
                  }}
                  className="misty-button misty-button-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Slit Widths Modal */}
        {showSlitWidthsModal && selectedMaterial && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-white">
                  Slit Widths - {selectedMaterial.name}
                </h3>
                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => setShowAddSlitWidthForm(true)}
                    className="misty-button misty-button-primary"
                  >
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Add Width
                  </button>
                  <button
                    onClick={() => setShowSlitWidthsModal(false)}
                    className="text-gray-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>
              </div>

              <div className="mb-4 p-4 bg-gray-700 rounded-lg">
                <h4 className="text-lg font-medium text-white mb-2">Summary</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-300">Total Widths Available:</span>
                    <div className="font-medium text-white">{materialSlitWidths.length}</div>
                  </div>
                  <div>
                    <span className="text-gray-300">Total Available Meters:</span>
                    <div className="font-medium text-white">
                      {materialSlitWidths.reduce((sum, width) => sum + width.available_quantity_meters, 0).toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-300">Width Range:</span>
                    <div className="font-medium text-white">
                      {materialSlitWidths.length > 0 
                        ? `${Math.min(...materialSlitWidths.map(w => w.slit_width_mm))}mm - ${Math.max(...materialSlitWidths.map(w => w.slit_width_mm))}mm`
                        : 'No widths available'
                      }
                    </div>
                  </div>
                </div>
              </div>

              {/* Add Slit Width Form */}
              {showAddSlitWidthForm && (
                <div className="mb-4 p-4 bg-blue-900/20 border border-blue-700 rounded-lg">
                  <h4 className="text-lg font-medium text-white mb-3">Add New Slit Width</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Slit Width (mm)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={slitWidthForm.slit_width_mm}
                        onChange={(e) => setSlitWidthForm(prev => ({
                          ...prev,
                          slit_width_mm: e.target.value
                        }))}
                        className="misty-input"
                        placeholder="e.g. 50.5"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        Quantity (meters)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={slitWidthForm.quantity_meters}
                        onChange={(e) => setSlitWidthForm(prev => ({
                          ...prev,
                          quantity_meters: e.target.value
                        }))}
                        className="misty-input"
                        placeholder="e.g. 100.0"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end space-x-3 mt-4">
                    <button
                      onClick={() => {
                        setShowAddSlitWidthForm(false);
                        setSlitWidthForm({
                          slit_width_mm: '',
                          quantity_meters: '',
                          source_job_id: 'manual-entry',
                          source_order_id: 'manual-entry'
                        });
                      }}
                      className="misty-button misty-button-secondary"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleAddSlitWidth}
                      className="misty-button misty-button-primary"
                    >
                      Add Width
                    </button>
                  </div>
                </div>
              )}

              <div className="bg-gray-700 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-600">
                    <tr>
                      <th className="px-4 py-2 text-left text-sm font-medium text-gray-300">Width (mm)</th>
                      <th className="px-4 py-2 text-right text-sm font-medium text-gray-300">Total Meters</th>
                      <th className="px-4 py-2 text-right text-sm font-medium text-gray-300">Available Meters</th>
                      <th className="px-4 py-2 text-center text-sm font-medium text-gray-300">Source</th>
                      <th className="px-4 py-2 text-center text-sm font-medium text-gray-300">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-600">
                    {materialSlitWidths.length > 0 ? (
                      materialSlitWidths.flatMap((widthGroup) => 
                        widthGroup.entries.map((entry, entryIndex) => (
                          <tr key={`${widthGroup.slit_width_mm}-${entryIndex}`} className="hover:bg-gray-600">
                            <td className="px-4 py-2 text-sm font-medium text-white">
                              {entry.slit_width_mm}mm
                            </td>
                            <td className="px-4 py-2 text-right text-sm text-white">
                              {editingSlitWidth === entry.id ? (
                                <input
                                  type="number"
                                  step="0.1"
                                  defaultValue={entry.quantity_meters}
                                  onBlur={(e) => {
                                    handleUpdateSlitWidthQuantity(entry.id, e.target.value);
                                  }}
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                      handleUpdateSlitWidthQuantity(entry.id, e.target.value);
                                    }
                                    if (e.key === 'Escape') {
                                      setEditingSlitWidth(null);
                                    }
                                  }}
                                  className="misty-input w-20 text-right text-sm"
                                  autoFocus
                                />
                              ) : (
                                <span 
                                  className="cursor-pointer hover:bg-gray-500 px-2 py-1 rounded"
                                  onDoubleClick={() => setEditingSlitWidth(entry.id)}
                                  title="Double-click to edit quantity"
                                >
                                  {entry.quantity_meters.toFixed(2)}
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-2 text-right text-sm">
                              <span className={`${entry.remaining_quantity > 0 ? 'text-green-400' : 'text-red-400'}`}>
                                {entry.remaining_quantity.toFixed(2)}
                              </span>
                            </td>
                            <td className="px-4 py-2 text-center text-sm text-gray-300">
                              {entry.created_from_additional_widths ? (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-900 text-blue-300">
                                  Job Card
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-900 text-green-300">
                                  Manual
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-2 text-center">
                              <div className="flex items-center justify-center space-x-1">
                                <button
                                  onClick={() => handleAdjustSlitWidth(entry.id, entry.remaining_quantity, 10)}
                                  className="text-green-400 hover:text-green-300 text-xs p-1"
                                  title="Add 10 meters"
                                >
                                  <ArrowUpIcon className="h-3 w-3" />
                                </button>
                                <button
                                  onClick={() => handleAdjustSlitWidth(entry.id, entry.remaining_quantity, -10)}
                                  className="text-yellow-400 hover:text-yellow-300 text-xs p-1"
                                  title="Subtract 10 meters"
                                >
                                  <ArrowDownIcon className="h-3 w-3" />
                                </button>
                                <button
                                  onClick={() => setEditingSlitWidth(entry.id)}
                                  className="text-blue-400 hover:text-blue-300 text-xs p-1"
                                  title="Edit quantity"
                                >
                                  <PencilIcon className="h-3 w-3" />
                                </button>
                                <button
                                  onClick={async (e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    
                                    alert('Delete button clicked! ID: ' + entry.id);
                                    
                                    if (!entry.id) {
                                      alert('Error: Entry ID is missing!');
                                      return;
                                    }
                                    
                                    const confirmed = window.confirm(`Are you sure you want to delete this slit width entry?\n\nWidth: ${entry.slit_width_mm}mm\nMeters: ${entry.quantity_meters}m`);
                                    
                                    if (!confirmed) {
                                      return;
                                    }
                                    
                                    try {
                                      alert('Calling delete API for ID: ' + entry.id);
                                      const response = await apiHelpers.deleteSlitWidth(entry.id);
                                      alert('Delete API response: ' + JSON.stringify(response));
                                      
                                      if (response.data?.success || response.success) {
                                        toast.success('Slit width deleted successfully');
                                        await loadSlitWidths(selectedMaterial.id, selectedMaterial.name);
                                      } else {
                                        alert('Delete failed: ' + (response.data?.message || response.message));
                                        toast.error('Failed to delete slit width');
                                      }
                                    } catch (error) {
                                      alert('Error occurred: ' + error.message);
                                      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message;
                                      
                                      if (errorMsg.includes('allocated')) {
                                        toast.error('Cannot delete: This slit width is allocated to an order');
                                      } else {
                                        toast.error('Delete failed: ' + errorMsg);
                                      }
                                    }
                                  }}
                                  className="text-red-400 hover:text-red-300 text-xs p-1 cursor-pointer"
                                  title="Delete entry"
                                  type="button"
                                >
                                  <TrashIcon className="h-3 w-3" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))
                      )
                    ) : (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                          <ClipboardDocumentListIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                          <p>No slit widths available for this material</p>
                          <p className="text-sm">Slit widths are created from slitting jobs</p>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="flex justify-end mt-6">
                <button
                  onClick={() => setShowSlitWidthsModal(false)}
                  className="misty-button misty-button-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Manual Stock Take Modal */}
        {showManualStockTake && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-gray-800 rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
              <div className="p-6 border-b border-gray-700">
                <h2 className="text-2xl font-bold text-white mb-2">Manual Stock Take</h2>
                <p className="text-gray-400">Review and confirm stock quantities for all items</p>
                
                {/* Month Selection */}
                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Select Month for Stock Take <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="month"
                    value={manualStockTakeMonth}
                    onChange={(e) => setManualStockTakeMonth(e.target.value)}
                    className="misty-input w-full md:w-64"
                  />
                </div>
              </div>

              {/* Stock Take Items List */}
              <div className="flex-1 overflow-y-auto p-6">
                {manualStockTakeLoading ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400 mx-auto"></div>
                    <p className="text-gray-400 mt-4">Loading stock items...</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* Products Section */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        <CubeIcon className="h-5 w-5 mr-2 text-yellow-400" />
                        Products On Hand ({manualStockTakeItems.filter(i => i.type === 'product').length})
                      </h3>
                      <div className="bg-gray-900 rounded-lg overflow-hidden">
                        <table className="w-full">
                          <thead className="bg-gray-800">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Product</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Client</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">Current QOH</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">Purchase Cost</th>
                              <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase">Unit</th>
                              <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase">Actions</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-700">
                            {manualStockTakeItems.filter(i => i.type === 'product').map((item) => (
                              <tr key={item.id} className={stockTakeModifications[item.id]?.confirmed ? 'bg-green-900 bg-opacity-20' : ''}>
                                <td className="px-4 py-3 text-sm text-white">{item.name}</td>
                                <td className="px-4 py-3 text-sm text-gray-300">{item.client_name}</td>
                                <td className="px-4 py-3 text-sm text-right text-white font-medium">{item.quantity_on_hand}</td>
                                <td className="px-4 py-3 text-sm text-right text-green-400">${(item.purchase_cost || 0).toFixed(2)}</td>
                                <td className="px-4 py-3 text-sm text-center text-gray-400">{item.unit_of_measure}</td>
                                <td className="px-4 py-3">
                                  <div className="flex items-center justify-center space-x-2">
                                    {!stockTakeModifications[item.id]?.confirmed ? (
                                      <>
                                        <button
                                          onClick={() => confirmQuantity(item.id)}
                                          className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded"
                                        >
                                          ✓ Confirmed
                                        </button>
                                        <input
                                          type="number"
                                          step="0.01"
                                          placeholder="New qty"
                                          value={stockTakeModifications[item.id]?.newQuantity || ''}
                                          onChange={(e) => setStockTakeModifications(prev => ({
                                            ...prev,
                                            [item.id]: { ...prev[item.id], newQuantity: e.target.value }
                                          }))}
                                          className="misty-input w-24 text-sm"
                                        />
                                        <button
                                          onClick={() => modifyStockOnHand(item.id)}
                                          className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white text-xs rounded"
                                        >
                                          Modify SOH
                                        </button>
                                      </>
                                    ) : (
                                      <div className="flex items-center space-x-2">
                                        <CheckCircleIcon className="h-5 w-5 text-green-400" />
                                        <span className="text-sm text-green-400">Confirmed</span>
                                      </div>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Raw Materials Section */}
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                        <CubeIcon className="h-5 w-5 mr-2 text-blue-400" />
                        Raw Materials On Hand ({manualStockTakeItems.filter(i => i.type === 'material').length})
                      </h3>
                      <div className="bg-gray-900 rounded-lg overflow-hidden">
                        <table className="w-full">
                          <thead className="bg-gray-800">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Material</th>
                              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Supplier</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">Current QOH</th>
                              <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">Purchase Cost</th>
                              <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase">Unit</th>
                              <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase">Actions</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-700">
                            {manualStockTakeItems.filter(i => i.type === 'material').map((item) => (
                              <tr key={item.id} className={stockTakeModifications[item.id]?.confirmed ? 'bg-green-900 bg-opacity-20' : ''}>
                                <td className="px-4 py-3 text-sm text-white">{item.name}</td>
                                <td className="px-4 py-3 text-sm text-gray-300">{item.supplier}</td>
                                <td className="px-4 py-3 text-sm text-right text-white font-medium">{item.quantity_on_hand}</td>
                                <td className="px-4 py-3 text-sm text-right text-green-400">${(item.purchase_cost || 0).toFixed(2)}</td>
                                <td className="px-4 py-3 text-sm text-center text-gray-400">{item.unit_of_measure}</td>
                                <td className="px-4 py-3">
                                  <div className="flex items-center justify-center space-x-2">
                                    {!stockTakeModifications[item.id]?.confirmed ? (
                                      <>
                                        <button
                                          onClick={() => confirmQuantity(item.id)}
                                          className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-xs rounded"
                                        >
                                          ✓ Confirmed
                                        </button>
                                        <input
                                          type="number"
                                          step="0.01"
                                          placeholder="New qty"
                                          value={stockTakeModifications[item.id]?.newQuantity || ''}
                                          onChange={(e) => setStockTakeModifications(prev => ({
                                            ...prev,
                                            [item.id]: { ...prev[item.id], newQuantity: e.target.value }
                                          }))}
                                          className="misty-input w-24 text-sm"
                                        />
                                        <button
                                          onClick={() => modifyStockOnHand(item.id)}
                                          className="px-3 py-1 bg-yellow-600 hover:bg-yellow-700 text-white text-xs rounded"
                                        >
                                          Modify SOH
                                        </button>
                                      </>
                                    ) : (
                                      <div className="flex items-center space-x-2">
                                        <CheckCircleIcon className="h-5 w-5 text-green-400" />
                                        <span className="text-sm text-green-400">Confirmed</span>
                                      </div>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Spiral Paper Cores Summary */}
                    {(() => {
                      const coresSummary = calculateSpiralCoresSummary();
                      if (coresSummary.length === 0) return null;
                      
                      return (
                        <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-4">
                          <h4 className="text-purple-300 font-medium mb-3 flex items-center">
                            <CubeIcon className="h-5 w-5 mr-2" />
                            Spiral Paper Cores Summary
                          </h4>
                          <div className="overflow-x-auto">
                            <table className="w-full">
                              <thead className="bg-gray-800">
                                <tr>
                                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-300">Width (mm)</th>
                                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-300">Quantity</th>
                                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-300">Total m²</th>
                                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-300">% of Master Deckle</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-gray-700">
                                {coresSummary.map((group, index) => (
                                  <tr key={index}>
                                    <td className="px-3 py-2 text-sm text-white">{group.width_mm} mm</td>
                                    <td className="px-3 py-2 text-sm text-right text-gray-300">{group.quantity}</td>
                                    <td className="px-3 py-2 text-sm text-right text-yellow-400">{group.total_m2.toFixed(2)} m²</td>
                                    <td className="px-3 py-2 text-sm text-right text-blue-400">{group.percent_of_master.toFixed(2)}%</td>
                                  </tr>
                                ))}
                                <tr className="bg-gray-800 font-bold">
                                  <td className="px-3 py-2 text-sm text-white">TOTAL</td>
                                  <td className="px-3 py-2 text-sm text-right text-white">
                                    {coresSummary.reduce((sum, g) => sum + g.quantity, 0)}
                                  </td>
                                  <td className="px-3 py-2 text-sm text-right text-yellow-400">
                                    {coresSummary.reduce((sum, g) => sum + g.total_m2, 0).toFixed(2)} m²
                                  </td>
                                  <td className="px-3 py-2 text-sm text-right text-gray-400">-</td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                          <p className="text-xs text-gray-400 mt-2">
                            * Based on 1500mm master deckle width
                          </p>
                        </div>
                      );
                    })()}

                    {/* Summary */}
                    <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                      <h4 className="text-blue-300 font-medium mb-2">Stock Take Progress</h4>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-400">Total Items:</span>
                          <span className="text-white ml-2 font-medium">{manualStockTakeItems.length}</span>
                        </div>
                        <div>
                          <span className="text-gray-400">Confirmed:</span>
                          <span className="text-green-400 ml-2 font-medium">
                            {Object.values(stockTakeModifications).filter(m => m.confirmed).length}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-400">Remaining:</span>
                          <span className="text-yellow-400 ml-2 font-medium">
                            {manualStockTakeItems.length - Object.values(stockTakeModifications).filter(m => m.confirmed).length}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Footer Actions */}
              <div className="p-6 border-t border-gray-700 flex justify-between items-center">
                <div className="flex space-x-3">
                  <button
                    onClick={exportStockTakeToPDF}
                    className="misty-button misty-button-secondary flex items-center"
                  >
                    <PrinterIcon className="h-5 w-5 mr-2" />
                    Print PDF
                  </button>
                  <button
                    onClick={exportStockTakeToCSV}
                    className="misty-button misty-button-secondary flex items-center"
                  >
                    <DocumentArrowDownIcon className="h-5 w-5 mr-2" />
                    Generate CSV
                  </button>
                </div>
                <div className="flex space-x-3">
                  <button
                    onClick={() => setShowManualStockTake(false)}
                    className="misty-button misty-button-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveManualStockTake}
                    disabled={!manualStockTakeMonth}
                    className="misty-button misty-button-primary disabled:opacity-50"
                  >
                    Save Stock Take
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Archived Stocktakes Modal */}
        {showArchivedStocktakes && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
              <div className="p-6 border-b border-gray-700">
                <h2 className="text-2xl font-bold text-white">Archived Stocktakes</h2>
                <p className="text-gray-400">View, edit, or export historical stocktakes</p>
              </div>

              <div className="flex-1 overflow-y-auto p-6">
                {loadingArchived ? (
                  <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400 mx-auto"></div>
                    <p className="text-gray-400 mt-4">Loading archived stocktakes...</p>
                  </div>
                ) : archivedStocktakes.length === 0 ? (
                  <div className="text-center py-12">
                    <CubeIcon className="h-16 w-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400">No archived stocktakes found</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {archivedStocktakes.map((stocktake) => (
                      <div key={stocktake.id} className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <h3 className="text-lg font-semibold text-white mb-1">
                              Stocktake for {stocktake.month}
                            </h3>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mt-2">
                              <div>
                                <span className="text-gray-400">Created:</span>
                                <span className="text-white ml-2">{new Date(stocktake.created_at).toLocaleDateString()}</span>
                              </div>
                              <div>
                                <span className="text-gray-400">Total Items:</span>
                                <span className="text-white ml-2">{stocktake.summary.total_items}</span>
                              </div>
                              <div>
                                <span className="text-gray-400">Confirmed:</span>
                                <span className="text-green-400 ml-2">{stocktake.summary.confirmed_count}</span>
                              </div>
                              <div>
                                <span className="text-gray-400">Modified:</span>
                                <span className="text-yellow-400 ml-2">{stocktake.summary.modified_count || 0}</span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-2 ml-4">
                            <button
                              onClick={() => exportArchivedStocktakeToPDF(stocktake)}
                              className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded flex items-center"
                              title="Print PDF"
                            >
                              <PrinterIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => exportArchivedStocktakeToCSV(stocktake)}
                              className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded flex items-center"
                              title="Generate CSV"
                            >
                              <DocumentArrowDownIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => viewStocktake(stocktake.id)}
                              className="px-3 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded"
                            >
                              <EyeIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => editStocktake(stocktake.id)}
                              className="px-3 py-2 bg-yellow-600 hover:bg-yellow-700 text-white text-sm rounded"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => deleteStocktake(stocktake.id)}
                              className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="p-6 border-t border-gray-700 flex justify-end">
                <button
                  onClick={() => setShowArchivedStocktakes(false)}
                  className="misty-button misty-button-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* View Stocktake Modal */}
        {viewingStocktake && (
          <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
              <div className="p-6 border-b border-gray-700">
                <h2 className="text-2xl font-bold text-white">Stocktake for {viewingStocktake.month}</h2>
                <p className="text-gray-400">Created: {new Date(viewingStocktake.created_at).toLocaleString()}</p>
              </div>

              <div className="flex-1 overflow-y-auto p-6">
                <div className="space-y-6">
                  {/* Summary */}
                  <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                    <h4 className="text-blue-300 font-medium mb-2">Summary</h4>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Total Items:</span>
                        <span className="text-white ml-2">{viewingStocktake.summary.total_items}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Confirmed:</span>
                        <span className="text-green-400 ml-2">{viewingStocktake.summary.confirmed_count}</span>
                      </div>
                      <div>
                        <span className="text-gray-400">Modified:</span>
                        <span className="text-yellow-400 ml-2">{viewingStocktake.summary.modified_count || 0}</span>
                      </div>
                    </div>
                  </div>

                  {/* Items */}
                  <div className="bg-gray-900 rounded-lg overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-gray-800">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Item</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">QOH</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">Cost</th>
                          <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-700">
                        {viewingStocktake.items.map((item, index) => (
                          <tr key={index} className={item.confirmed ? 'bg-green-900 bg-opacity-20' : ''}>
                            <td className="px-4 py-3 text-sm text-white">{item.name}</td>
                            <td className="px-4 py-3 text-sm text-right text-white">{item.quantity_on_hand}</td>
                            <td className="px-4 py-3 text-sm text-right text-green-400">${(item.purchase_cost || 0).toFixed(2)}</td>
                            <td className="px-4 py-3 text-sm text-center">
                              {item.confirmed ? (
                                <span className="text-green-400">✓ Confirmed</span>
                              ) : (
                                <span className="text-gray-400">Pending</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>

              <div className="p-6 border-t border-gray-700 flex justify-end">
                <button
                  onClick={() => setViewingStocktake(null)}
                  className="misty-button misty-button-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Stocktake;