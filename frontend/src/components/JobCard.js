import React, { useState, useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import { apiHelpers, api } from '../utils/api';
import { toast } from 'sonner';
import { 
  PrinterIcon, 
  XMarkIcon, 
  ClockIcon, 
  CogIcon,
  ShieldCheckIcon,
  TruckIcon,
  CalculatorIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

// Production Stage Enum (matches backend)
const ProductionStage = {
  ORDER_ENTERED: 'order_entered',
  PENDING_MATERIAL: 'pending_material',
  PAPER_SLITTING: 'paper_slitting',
  WINDING: 'winding',  // NOT 'core_winding'
  FINISHING: 'finishing',  // NOT 'finishing_packing'
  DELIVERY: 'delivery',
  INVOICING: 'invoicing',
  ACCOUNTING_TRANSACTION: 'accounting_transaction',
  CLEARED: 'cleared'
};

// Machine Line Configurations
const MACHINE_LINES = {
  paper_slitting: {
    name: 'Paper Slitting Line',
    machines: ['Slitter A1', 'Slitter B2', 'Slitter C3'],
    standardSetupTime: 45, // minutes
    ratePerMinute: 250 // meters per minute
  },
  winding: {
    name: 'Core Winder Line', 
    machines: ['Core Winder X1', 'Core Winder Y2', 'Core Winder Z3'],
    standardSetupTime: 30,
    ratePerMinute: 180
  },
  finishing: {
    name: 'Cutting/Indexing Line',
    machines: ['Cutter M1', 'Cutter N2', 'Index P3'],
    standardSetupTime: 20,
    ratePerMinute: 120
  },
  delivery: {
    name: 'Packing/Delivery Line',
    machines: ['Pack Station 1', 'Pack Station 2', 'Loading Dock'],
    standardSetupTime: 15,
    ratePerMinute: 60
  }
};

const JobCard = ({ jobId, stage, orderId, onClose, onJobStarted }) => {
  const [jobData, setJobData] = useState(null);
  const [productSpecs, setProductSpecs] = useState(null);
  const [calculations, setCalculations] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedMachine, setSelectedMachine] = useState('');
  const [setupNotes, setSetupNotes] = useState('');
  
  // Job timing states
  const [isJobRunning, setIsJobRunning] = useState(false);
  const [jobStartTime, setJobStartTime] = useState(null);
  const [actualRunTime, setActualRunTime] = useState(0); // in minutes
  const [isEditingRunTime, setIsEditingRunTime] = useState(false);
  const [editedRunTime, setEditedRunTime] = useState(0);
  const [currentTime, setCurrentTime] = useState(Date.now()); // For live timer display only
  
  // Operator sign-off states
  const [signOffs, setSignOffs] = useState({
    setup: { name: '', date: '', isEditing: false },
    production: { name: '', date: '', isEditing: false },
    qc: { name: '', date: '', isEditing: false }
  });
  const [editingSignOff, setEditingSignOff] = useState({ type: '', tempName: '' });

  // Finished production quantity states
  const [finishedQuantity, setFinishedQuantity] = useState(0);
  const [isEditingFinishedQuantity, setIsEditingFinishedQuantity] = useState(false);
  const [editedFinishedQuantity, setEditedFinishedQuantity] = useState(0);

  // Additional Biscuit Widths / Slit Widths states (for core winding and slitting jobs)
  const [masterCores, setMasterCores] = useState([]);
  const [isEditingMasterCore, setIsEditingMasterCore] = useState(false);
  const [newMasterCore, setNewMasterCore] = useState({ width: '', quantity: '', addToStock: false });
  
  // Machine-specific additional production states
  const [additionalProduction, setAdditionalProduction] = useState({
    slittingWidths: [], // For slitting machine: additional widths and meters
    extraMaterial: 0    // General excess material
  });
  const [isEditingAdditionalProduction, setIsEditingAdditionalProduction] = useState(false);
  const [newSlittingWidth, setNewSlittingWidth] = useState({ material_id: '', material_name: '', width: '', meters: '' });
  const [pendingSlitWidths, setPendingSlitWidths] = useState([]); // Store widths before submission
  const [rawMaterials, setRawMaterials] = useState([]); // Available raw materials from inventory

  // Order products completion tracking (for finishing stage)
  const [completedProducts, setCompletedProducts] = useState({});
  
  // Add finished cores to stock (for finishing stage)
  const [finishedCoresToStock, setFinishedCoresToStock] = useState('');
  
  // Label printing state
  const [showLabelPrintModal, setShowLabelPrintModal] = useState(false);
  const [labelTemplates, setLabelTemplates] = useState([]);
  const [selectedLabelTemplate, setSelectedLabelTemplate] = useState(null);
  const [showLabelPreview, setShowLabelPreview] = useState(false);
  const [showPrinterSelection, setShowPrinterSelection] = useState(false);
  const [availablePrinters, setAvailablePrinters] = useState([]);
  const [selectedPrinter, setSelectedPrinter] = useState(null);

  useEffect(() => {
    if (jobId && stage && orderId) {
      loadJobCardData();
      loadJobTiming();
      loadRawMaterials(); // Load raw materials for slit width dropdown
    }
  }, [jobId, stage]);

  // Save job timing data when it changes (debounced to prevent excessive re-renders)
  useEffect(() => {
    if (jobId && stage) {
      const timeoutId = setTimeout(() => {
        const timingKey = `job_timing_${jobId}_${stage}`;
        const timingData = {
          isJobRunning,
          jobStartTime,
          actualRunTime,
          selectedMachine,
          setupNotes,
          signOffs,
          finishedQuantity,
          additionalProduction,
          masterCores,
          completedProducts
        };
        localStorage.setItem(timingKey, JSON.stringify(timingData));
      }, 500); // Debounce by 500ms
      
      return () => clearTimeout(timeoutId);
    }
  }, [isJobRunning, jobStartTime, actualRunTime, selectedMachine, setupNotes, signOffs, finishedQuantity, additionalProduction, completedProducts, jobId, stage]);

  // Update live timer when job is running (without causing form clearing)
  useEffect(() => {
    let interval;
    if (isJobRunning && jobStartTime) {
      interval = setInterval(() => {
        // Only update time display, not form data
        setCurrentTime(Date.now());
      }, 60000); // Update every minute
    }
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [isJobRunning, jobStartTime]);

  const loadJobCardData = async () => {
    try {
      setLoading(true);
      
      console.log('Loading job card data with params:', { jobId, stage, orderId });
      
      // Validate required parameters
      if (!jobId || !stage) {
        console.error('Missing required parameters:', { jobId, stage });
        setLoading(false);
        return;
      }
      
      // Use orderId or jobId to fetch the actual order data
      const orderIdToFetch = orderId || jobId;
      
      // Fetch real order data
      const orderResponse = await apiHelpers.getOrder(orderIdToFetch);
      const orderData = orderResponse.data?.data || orderResponse.data;
      
      console.log('Fetched order data:', orderData);
      
      if (!orderData) {
        throw new Error('Order data not found');
      }
      
      // Create job data structure
      const jobData = {
        id: jobId,
        run_number: 1, // This could be calculated based on production logs
        status: 'in_progress',
        created_date: new Date().toISOString(),
        order: {
          id: orderData.id,
          order_number: orderData.order_number,
          client_name: orderData.client_name,
          quantity: orderData.items && orderData.items.length > 0 ? orderData.items[0].quantity : 0,
          due_date: orderData.due_date,
          priority: orderData.priority || 'Normal/Low',
          items: orderData.items || [],
          other_products: orderData.items ? orderData.items.slice(1) : [] // All items except first as "other products"
        }
      };
      
      // Try to get product specifications for the first item from client catalogue
      let productSpecs = null;
      
      if (orderData.items && orderData.items.length > 0) {
        const firstItem = orderData.items[0];
        
        // First, try to get the product from the client's catalogue
        try {
          const catalogueResponse = await apiHelpers.getClientProduct(orderData.client_id, firstItem.product_id);
          const clientProduct = catalogueResponse.data?.data || catalogueResponse.data;
          
          console.log('Fetched client product:', clientProduct);
          
          if (clientProduct) {
            // The material_used array contains Product Specification IDs, not material IDs
            let materialLayers = [];
            let specificationData = null;
            
            if (clientProduct.material_used && clientProduct.material_used.length > 0) {
              // Fetch the Product Specification which contains the material layers
              try {
                const productSpecId = clientProduct.material_used[0]; // First material_used is the product specification ID
                console.log('Fetching Product Specification:', productSpecId);
                
                const specResponse = await apiHelpers.getProductSpecification(productSpecId);
                specificationData = specResponse.data?.data || specResponse.data;
                
                console.log('Fetched Product Specification:', specificationData);
                
                if (specificationData && specificationData.material_layers) {
                  // Fetch actual material data to get proper names and GSM
                  const materialPromises = specificationData.material_layers.map(async (layer) => {
                    try {
                      const materialResponse = await apiHelpers.getMaterial(layer.material_id);
                      const materialData = materialResponse.data?.data || materialResponse.data;
                      
                      return {
                        ...layer,
                        material_name: materialData?.material_description || layer.material_name || 'Unknown Material',
                        product_name: materialData?.material_description || 'Unknown Product',
                        gsm: materialData?.gsm || layer.gsm || 0,
                        supplier: materialData?.supplier || 'Unknown Supplier'
                      };
                    } catch (error) {
                      console.warn(`Could not fetch material data for ${layer.material_id}:`, error);
                      return {
                        ...layer,
                        material_name: layer.material_name || 'Unknown Material',
                        product_name: layer.material_name || 'Unknown Product',
                        gsm: layer.gsm || 0,
                        supplier: 'Unknown Supplier'
                      };
                    }
                  });
                  
                  materialLayers = await Promise.all(materialPromises);
                  console.log('Enhanced material layers with names and GSM:', materialLayers);
                }
              } catch (error) {
                console.warn(`Could not fetch Product Specification ${clientProduct.material_used[0]}:`, error);
              }
            }
            
            // Build product specs from client catalogue data and Product Specification
            productSpecs = {
              id: clientProduct.id,
              product_code: clientProduct.product_code,
              product_description: clientProduct.product_description,
              product_type: clientProduct.product_type,
              core_id: specificationData?.specifications?.internal_diameter || clientProduct.core_id || 'N/A',
              core_width: clientProduct.core_width || 'N/A',
              core_thickness: specificationData?.specifications?.wall_thickness_required || clientProduct.core_thickness || 'N/A',
              material_layers: materialLayers,
              makeready_allowance_percent: clientProduct.makeready_allowance_percent || 10,
              setup_time_minutes: clientProduct.setup_time_minutes || 45,
              waste_percentage: clientProduct.waste_percentage || 5,
              qc_tolerances: clientProduct.qc_tolerances || {
                id_tolerance: 0.5,
                od_tolerance: 0.5,
                wall_tolerance: 0.1
              },
              inspection_interval_minutes: clientProduct.inspection_interval_minutes || 60,
              tubes_per_carton: clientProduct.tubes_per_carton || 50,
              cartons_per_pallet: clientProduct.cartons_per_pallet || 20,
              special_tooling_notes: clientProduct.special_tooling_notes || specificationData?.manufacturing_notes || 'Standard processing',
              packing_instructions: clientProduct.packing_instructions || 'Handle with care',
              consumables: clientProduct.consumables || []
            };
          }
        } catch (error) {
          console.warn('Could not fetch client product:', error);
        }
        
        // Fallback: Create basic product specs from order item data if client catalogue fetch failed
        if (!productSpecs) {
          productSpecs = {
            id: firstItem.product_id,
            product_code: firstItem.product_name,
            product_description: firstItem.product_name,
            product_type: 'Unknown',
            core_id: 'N/A',
            core_width: 'N/A',
            core_thickness: 'N/A',
            material_layers: [],
            makeready_allowance_percent: 10,
            setup_time_minutes: 45,
            waste_percentage: 5,
            qc_tolerances: {
              id_tolerance: 0.5,
              od_tolerance: 0.5,
              wall_tolerance: 0.1
            },
            inspection_interval_minutes: 60,
            tubes_per_carton: 50,
            cartons_per_pallet: 20,
            special_tooling_notes: 'Standard processing',
            packing_instructions: 'Handle with care',
            consumables: []
          };
        }
      }

      setJobData(jobData);
      setProductSpecs(productSpecs);
      
      // Auto-select first available machine for current stage
      const currentMachineConfig = MACHINE_LINES[stage];
      if (currentMachineConfig && currentMachineConfig.machines.length > 0) {
        setSelectedMachine(currentMachineConfig.machines[0]);
      }

      calculateProduction(jobData, jobData.order, productSpecs);
      
    } catch (error) {
      console.error('Failed to load job card data:', error);
      toast.error(`Failed to load job card data: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadJobTiming = () => {
    if (jobId && stage) {
      const timingKey = `job_timing_${jobId}_${stage}`;
      const savedData = localStorage.getItem(timingKey);
      
      if (savedData) {
        try {
          const timingData = JSON.parse(savedData);
          
          if (timingData.isJobRunning !== undefined) setIsJobRunning(timingData.isJobRunning);
          if (timingData.jobStartTime) setJobStartTime(timingData.jobStartTime);
          if (timingData.actualRunTime !== undefined) setActualRunTime(timingData.actualRunTime);
          if (timingData.selectedMachine) setSelectedMachine(timingData.selectedMachine);
          if (timingData.setupNotes) setSetupNotes(timingData.setupNotes);
          if (timingData.signOffs) setSignOffs(timingData.signOffs);
          if (timingData.finishedQuantity !== undefined) setFinishedQuantity(timingData.finishedQuantity);
          if (timingData.additionalProduction) setAdditionalProduction(timingData.additionalProduction);
          if (timingData.masterCores) setMasterCores(timingData.masterCores);
          if (timingData.completedProducts) setCompletedProducts(timingData.completedProducts);
        } catch (error) {
          console.error('Error loading job timing data:', error);
        }
      }
    }
  };

  const loadRawMaterials = async () => {
    try {
      // Fetch raw materials from the same endpoint that Stocktake uses
      const response = await apiHelpers.get('/stock/raw-materials');
      // Handle StandardResponse format: response.data.data contains the actual array
      const data = response.data?.data || response.data || [];
      const rawMaterialsList = Array.isArray(data) ? data : [];
      
      console.log('Loaded raw materials for slitting dropdown:', rawMaterialsList);
      setRawMaterials(rawMaterialsList);
      
      if (rawMaterialsList.length === 0) {
        console.warn('No raw materials found. Make sure materials are added to Raw Materials stock.');
      }
    } catch (error) {
      console.error('Failed to load raw materials:', error);
      toast.error('Failed to load raw materials list');
      setRawMaterials([]);
    }
  };

  const calculateProduction = (job, order, product) => {
    // Add safety checks for all parameters
    if (!job || !order || !product) {
      console.log('Missing data for calculation:', { job: !!job, order: !!order, product: !!product });
      // Set default calculations if data is missing
      setCalculations({
        goodMaterialLength: 0,
        makereadyLength: 0,
        wasteLength: 0,
        totalLengthRequired: 0,
        setupTime: 30,
        runTime: 0,
        totalProductionTime: 30,
        tubesPerCarton: 50,
        cartonsRequired: 0,
        cartonsPerPallet: 20,
        palletsRequired: 0,
        tapeRollsRequired: 0,
        wastePercentage: '5.0',
        makereadyPercentage: '10.0'
      });
      return;
    }
    
    if (!order.quantity) {
      console.log('Missing order quantity, using default');
      // Set default calculations if quantity is missing
      setCalculations({
        goodMaterialLength: 0,
        makereadyLength: 0,
        wasteLength: 0,
        totalLengthRequired: 0,
        setupTime: 30,
        runTime: 0,
        totalProductionTime: 30,
        tubesPerCarton: 50,
        cartonsRequired: 0,
        cartonsPerPallet: 20,
        palletsRequired: 0,
        tapeRollsRequired: 0,
        wastePercentage: '5.0',
        makereadyPercentage: '10.0'
      });
      return;
    }

    const orderQty = parseInt(order.quantity) || 0;
    const tubeLength = product.core_width ? parseFloat(product.core_width) : 1000; // mm
    const tubeLengthMeters = tubeLength / 1000;

    // Calculate material requirements
    const goodMaterialLength = orderQty * tubeLengthMeters;
    const makereadyAllowance = (product.makeready_allowance_percent || 10) / 100;
    const wastePercentage = (product.waste_percentage || 5) / 100;
    
    const makereadyLength = goodMaterialLength * makereadyAllowance;
    const totalWithMakeready = goodMaterialLength + makereadyLength;
    const wasteLength = totalWithMakeready * wastePercentage;
    const totalLengthRequired = totalWithMakeready + wasteLength;

    // Calculate production times
    const machineConfig = MACHINE_LINES[stage] || {};
    const setupTime = product.setup_time_minutes || machineConfig.standardSetupTime || 30;
    const productionRate = machineConfig.ratePerMinute || 150;
    const runTime = totalLengthRequired / productionRate;
    const totalProductionTime = setupTime + runTime;

    // Calculate consumables
    const tubesPerCarton = product.tubes_per_carton || 50;
    const cartonsRequired = Math.ceil(orderQty / tubesPerCarton);
    const cartonsPerPallet = product.cartons_per_pallet || 20;
    const palletsRequired = Math.ceil(cartonsRequired / cartonsPerPallet);

    // Calculate tape requirements (estimate based on carton sealing)
    const tapeRollsRequired = Math.ceil(cartonsRequired / 25); // Assume 25 cartons per tape roll

    setCalculations({
      goodMaterialLength: Math.round(goodMaterialLength),
      makereadyLength: Math.round(makereadyLength), 
      wasteLength: Math.round(wasteLength),
      totalLengthRequired: Math.round(totalLengthRequired),
      setupTime,
      runTime: Math.round(runTime),
      totalProductionTime: Math.round(totalProductionTime),
      tubesPerCarton,
      cartonsRequired,
      cartonsPerPallet,
      palletsRequired,
      tapeRollsRequired,
      wastePercentage: (wastePercentage * 100).toFixed(1),
      makereadyPercentage: (makereadyAllowance * 100).toFixed(1)
    });
  };

  const handlePrint = () => {
    window.print();
  };

  const handleStartJob = async () => {
    const startTime = new Date();
    setJobStartTime(startTime);
    setIsJobRunning(true);
    toast.success(`Job started at ${startTime.toLocaleTimeString()}`);
    
    // Update the order with production_started_at timestamp
    try {
      await apiHelpers.updateOrder(orderId, {
        production_started_at: startTime.toISOString()
      });
      
      // Notify parent component to refresh
      if (onJobStarted) {
        onJobStarted();
      }
    } catch (error) {
      console.error('Failed to update production start time:', error);
      toast.error('Failed to mark job as started');
    }
  };

  const handleCompleteRun = async () => {
    if (jobStartTime) {
      const endTime = new Date();
      const durationMs = endTime.getTime() - new Date(jobStartTime).getTime();
      const durationMinutes = Math.round(durationMs / (1000 * 60));
      
      setActualRunTime(durationMinutes);
      setIsJobRunning(false);
      
      // Prepare job card data for archiving
      const jobCardData = {
        order_id: orderId,
        job_id: jobId,
        stage: stage,
        machine: selectedMachine,
        setup_notes: setupNotes,
        job_start_time: jobStartTime,
        job_end_time: endTime,
        actual_run_time_minutes: durationMinutes,
        finished_quantity: finishedQuantity,
        additional_production: additionalProduction,
        master_cores: masterCores,
        completed_products: completedProducts,
        operator_signoffs: signOffs,
        product_specs: productSpecs,
        calculations: calculations,
        completed_at: endTime.toISOString(),
        completed_by: localStorage.getItem('user_name') || 'Unknown'
      };
      
      try {
        // Save job card to backend
        await apiHelpers.saveJobCard(jobCardData);
        
        // Move job to next stage
        const stageOrder = [
          ProductionStage.ORDER_ENTERED,
          ProductionStage.PAPER_SLITTING,
          ProductionStage.CORE_WINDING,
          ProductionStage.FINISHING_PACKING,
          ProductionStage.DELIVERY,
          ProductionStage.INVOICING
        ];
        
        const currentStageIndex = stageOrder.indexOf(stage);
        const nextStage = stageOrder[currentStageIndex + 1];
        
        if (nextStage) {
          await apiHelpers.updateOrderStage(orderId, {
            from_stage: stage,
            to_stage: nextStage
          });
          
          toast.success(
            <div>
              <p>Job completed! Actual run time: {Math.floor(durationMinutes / 60)}h {durationMinutes % 60}m</p>
              <p className="text-sm">Job moved to: {nextStage.replace(/_/g, ' ').toUpperCase()}</p>
            </div>,
            { duration: 5000 }
          );
        } else {
          toast.success(`Job completed! Actual run time: ${Math.floor(durationMinutes / 60)}h ${durationMinutes % 60}m`);
        }
        
        // Clear localStorage for this job card
        const timingKey = `jobTiming_${jobId}_${stage}`;
        localStorage.removeItem(timingKey);
        
        // Notify parent and close modal
        if (onJobStarted) {
          onJobStarted(); // This will refresh the production board
        }
        
        // Close the job card after a short delay
        setTimeout(() => {
          onClose();
        }, 2000);
        
      } catch (error) {
        console.error('Failed to complete job card:', error);
        toast.error('Failed to save job card and move to next stage: ' + (error.message || 'Unknown error'));
      }
    }
  };

  const handleEditRunTime = () => {
    setEditedRunTime(actualRunTime);
    setIsEditingRunTime(true);
  };

  const handleSaveRunTime = () => {
    const newRunTime = parseInt(editedRunTime) || 0;
    setActualRunTime(newRunTime);
    setIsEditingRunTime(false);
    toast.success(`Run time updated to ${Math.floor(newRunTime / 60)}h ${newRunTime % 60}m`);
  };

  const handleCancelEditRunTime = () => {
    setIsEditingRunTime(false);
    setEditedRunTime(actualRunTime);
  };

  // Sign-off handlers
  const handleSignOffDoubleClick = (type) => {
    setEditingSignOff({ 
      type, 
      tempName: signOffs[type].name 
    });
  };

  const handleSignOffSave = () => {
    const { type, tempName } = editingSignOff;
    const currentDate = new Date().toLocaleDateString();
    
    setSignOffs(prev => ({
      ...prev,
      [type]: {
        name: tempName.trim(),
        date: currentDate,
        isEditing: false
      }
    }));
    
    setEditingSignOff({ type: '', tempName: '' });
    toast.success(`${type.charAt(0).toUpperCase() + type.slice(1)} sign-off saved`);
  };

  const handleSignOffCancel = () => {
    setEditingSignOff({ type: '', tempName: '' });
  };

  const clearSignOff = (type) => {
    if (window.confirm(`Clear ${type} sign-off?`)) {
      setSignOffs(prev => ({
        ...prev,
        [type]: { name: '', date: '', isEditing: false }
      }));
      toast.success(`${type.charAt(0).toUpperCase() + type.slice(1)} sign-off cleared`);
    }
  };

  // Finished quantity handlers
  const handleEditFinishedQuantity = () => {
    setEditedFinishedQuantity(finishedQuantity);
    setIsEditingFinishedQuantity(true);
  };

  const handleSaveFinishedQuantity = () => {
    const newQuantity = parseInt(editedFinishedQuantity) || 0;
    setFinishedQuantity(newQuantity);
    setIsEditingFinishedQuantity(false);
    
    // Calculate excess for stocktake
    const requiredQuantity = jobData?.order?.quantity || 0;
    const excess = Math.max(0, newQuantity - requiredQuantity);
    
    if (excess > 0) {
      toast.success(`Finished quantity updated: ${newQuantity.toLocaleString()}. Excess: ${excess.toLocaleString()} units for stocktake`);
    } else {
      toast.success(`Finished quantity updated: ${newQuantity.toLocaleString()}`);
    }
  };

  const handleCancelEditFinishedQuantity = () => {
    setIsEditingFinishedQuantity(false);
    setEditedFinishedQuantity(finishedQuantity);
  };

  // Additional slitting widths handlers
  const handleAddSlittingWidth = () => {
    if (newSlittingWidth.material_id && newSlittingWidth.width && newSlittingWidth.meters) {
      const slittingEntry = {
        material_id: newSlittingWidth.material_id,
        material_name: newSlittingWidth.material_name,
        width: parseFloat(newSlittingWidth.width),
        meters: parseFloat(newSlittingWidth.meters),
        id: Date.now() // Simple ID for removal
      };

      // Add to pending list (not saved to DB yet)
      setPendingSlitWidths(prev => [...prev, slittingEntry]);
      
      // Reset form
      setNewSlittingWidth({ material_id: '', material_name: '', width: '', meters: '' });
    }
  };

  // Submit all pending slit widths to database
  const handleSubmitSlitWidths = async () => {
    if (pendingSlitWidths.length === 0) {
      toast.error('No slit widths to submit');
      return;
    }

    try {
      // Save each slit width to the database
      for (const slittingEntry of pendingSlitWidths) {
        console.log('Submitting slit width:', slittingEntry);
        await saveSlittingWidthToDatabase(slittingEntry);
      }

      // Add to job's additional production tracking
      setAdditionalProduction(prev => ({
        ...prev,
        slittingWidths: [...prev.slittingWidths, ...pendingSlitWidths]
      }));

      // Clear pending list
      setPendingSlitWidths([]);
      
      toast.success(`Successfully submitted ${pendingSlitWidths.length} slit width(s) to Raw Materials`);
    } catch (error) {
      console.error('Error submitting slit widths:', error);
      console.error('Error details:', error.message, error.response?.data);
      toast.error(`Failed to submit slit widths: ${error.message || 'Unknown error'}`);
    }
  };

  // Save slitting width to database for material allocation
  const saveSlittingWidthToDatabase = async (slittingEntry) => {
    try {
      console.log('Looking for material with ID:', slittingEntry.material_id);
      console.log('Available raw materials:', rawMaterials);
      
      // Find the raw material stock record to get material specifications
      const rawMaterialStock = rawMaterials.find(
        m => m.material_id === slittingEntry.material_id
      );

      if (!rawMaterialStock) {
        console.error('Selected material not found in raw materials inventory');
        console.error('Looking for material_id:', slittingEntry.material_id);
        throw new Error(`Material not found in inventory (ID: ${slittingEntry.material_id})`);
      }

      console.log('Found raw material stock:', rawMaterialStock);
        
      const slitWidthData = {
        raw_material_id: slittingEntry.material_id,
        raw_material_name: slittingEntry.material_name,
        slit_width_mm: slittingEntry.width,
        quantity_meters: slittingEntry.meters,
        source_job_id: jobId || 'unknown',
        source_order_id: jobData?.order?.id || 'unknown',
        created_from_additional_widths: true,
        material_specifications: {}
      };

      console.log('Posting slit width data:', slitWidthData);

      // Save slit width record
      const slitWidthResponse = await apiHelpers.post('/slit-widths', slitWidthData);
      
      console.log('Slit width response:', slitWidthResponse);
      
      if (!slitWidthResponse.success && !slitWidthResponse.data?.success) {
        const errorMsg = slitWidthResponse.message || slitWidthResponse.data?.message || 'Failed to save slit width';
        console.error('Failed to save slit width:', errorMsg);
        throw new Error(errorMsg);
      }

      console.log('Slit width saved to database successfully');

      // Now update the raw material stock quantity
      // We need to add the meters to the existing quantity
      const newQuantity = rawMaterialStock.quantity_on_hand + slittingEntry.meters;
      
      console.log(`Updating raw material stock from ${rawMaterialStock.quantity_on_hand} to ${newQuantity}`);
      
      const updateResponse = await api.put(`/stock/raw-materials/${rawMaterialStock.id}`, {
        quantity_on_hand: newQuantity,
        notes: `Added ${slittingEntry.meters} meters from slitting job ${jobId} (${slittingEntry.width}mm width)`
      });

      console.log('Stock update response:', updateResponse.data);

      if (!updateResponse.data?.success) {
        console.error('Failed to update raw material stock quantity:', updateResponse.data?.message);
        // Don't throw error here - slit width was already saved
        toast.warning('Slit width saved but stock quantity update failed');
      } else {
        console.log(`Updated raw material stock: ${rawMaterialStock.material_name} quantity increased to ${newQuantity}`);
      }

    } catch (error) {
      console.error('Error saving slit width to database:', error);
      console.error('Error stack:', error.stack);
      throw error;
    }
  };

  const handleRemoveSlittingWidth = (id) => {
    setPendingSlitWidths(prev => prev.filter(width => width.id !== id));
  };

  // Additional Biscuit Widths management functions
  const handleAddMasterCore = () => {
    if (newMasterCore.width && newMasterCore.quantity) {
      const coreEntry = {
        id: Date.now(),
        width: parseFloat(newMasterCore.width),
        quantity: parseInt(newMasterCore.quantity),
        addToStock: newMasterCore.addToStock,
        addedToStock: false // Track if already added to stock
      };
      
      setMasterCores(prev => [...prev, coreEntry]);
      setNewMasterCore({ width: '', quantity: '', addToStock: false });
      
      // If addToStock is true, automatically add excess to stock
      if (coreEntry.addToStock) {
        handleAddToStock(coreEntry);
      }
    }
  };

  const handleRemoveMasterCore = (id) => {
    setMasterCores(prev => prev.filter(core => core.id !== id));
  };

  const handleToggleAddToStock = async (coreId) => {
    const coreEntry = masterCores.find(core => core.id === coreId);
    if (!coreEntry) return;

    if (!coreEntry.addToStock && !coreEntry.addedToStock) {
      // Adding to stock
      const success = await handleAddToStock(coreEntry);
      if (success) {
        setMasterCores(prev => prev.map(core => 
          core.id === coreId 
            ? { ...core, addToStock: true, addedToStock: true }
            : core
        ));
      }
    } else {
      // Just toggle the checkbox (removing from stock would require separate API call)
      setMasterCores(prev => prev.map(core => 
        core.id === coreId 
          ? { ...core, addToStock: !core.addToStock }
          : core
      ));
    }
  };

  const handleAddToStock = async (coreEntry) => {
    if (!jobData?.order || !productSpecs) {
      toast.error('Missing job or product data for stock entry');
      return false;
    }

    try {
      // Calculate total cores produced
      const totalCores = coreEntry.quantity;
      const requiredCores = jobData.order.quantity || 0;
      const excessCores = Math.max(0, totalCores - requiredCores);

      if (excessCores <= 0) {
        toast.info('No excess cores to add to stock');
        return false;
      }

      // Create stock entry data
      const stockData = {
        client_id: jobData.order.client_id,
        client_name: jobData.order.client_name || 'Unknown Client',
        product_id: productSpecs.id,
        product_code: productSpecs.product_code,
        product_description: `${productSpecs.product_code} - Biscuits (${coreEntry.width}mm width)`,
        quantity_on_hand: excessCores,
        unit_of_measure: 'pieces',
        source_order_id: jobData.order.id,
        source_job_id: jobId,
        is_shared_product: false,
        shared_with_clients: [],
        created_from_excess: true,
        material_specifications: {
          biscuit_width: coreEntry.width,
          core_diameter: productSpecs.core_diameter,
          material_layers: productSpecs.material_layers
        },
        minimum_stock_level: 0
      };

      // Add to stock via API
      const response = await apiHelpers.post('/stock/raw-substrates', stockData);
      
      if (response.success) {
        toast.success(`${excessCores} excess biscuit pieces added to Raw Substrates stock`);
        return true;
      } else {
        throw new Error(response.message || 'Failed to add to stock');
      }
    } catch (error) {
      console.error('Failed to add biscuit pieces to stock:', error);
      toast.error('Failed to add biscuit pieces to stock');
      return false;
    }
  };

  // Handle adding finished cores to stock for finishing stage
  const handleAddToStockOnHand = async (core) => {
    if (!jobData?.order || !productSpecs) {
      toast.error('Missing job or product data for stock entry');
      return false;
    }

    try {
      // Create stock entry data for finished products
      const stockData = {
        client_id: jobData.order.client_id,
        client_name: jobData.order.client_name || 'Unknown Client',
        product_id: productSpecs.id,
        product_code: productSpecs.product_code,
        product_description: `${productSpecs.product_code} - Finished Cores (${core.width}mm)`,
        quantity_on_hand: core.quantity,
        unit_of_measure: 'pieces',
        source_order_id: jobData.order.id,
        source_job_id: jobId,
        is_shared_product: false,
        shared_with_clients: [],
        created_from_excess: true,
        material_specifications: {
          core_width: core.width,
          core_diameter: productSpecs.core_diameter || productSpecs.internal_diameter,
          material_layers: productSpecs.material_layers
        },
        minimum_stock_level: 0
      };

      // Add to stock via API
      const response = await apiHelpers.createRawSubstrate(stockData);
      
      if (response.data.success) {
        toast.success(`${core.quantity} finished cores added to stock`);
        
        // Mark the core as added to stock
        setMasterCores(prev => prev.map(c => 
          c.id === core.id ? { ...c, addedToStock: true } : c
        ));
        
        return true;
      } else {
        throw new Error(response.data.message || 'Failed to add to stock');
      }
    } catch (error) {
      console.error('Failed to add finished cores to stock:', error);
      toast.error('Failed to add finished cores to stock');
      return false;
    }
  };

  // Toggle product completion status
  const handleToggleProductCompletion = (productIndex) => {
    setCompletedProducts(prev => ({
      ...prev,
      [productIndex]: !prev[productIndex]
    }));
  };

  // Handle Print Carton Labels button
  const handlePrintCartonLabels = async () => {
    try {
      // Load label templates
      const response = await apiHelpers.getLabelTemplates();
      if (response.data.success) {
        setLabelTemplates(response.data.data || []);
        setShowLabelPrintModal(true);
      } else {
        toast.error('Failed to load label templates');
      }
    } catch (error) {
      console.error('Error loading label templates:', error);
      toast.error('Failed to load label templates');
    }
  };

  const handleSelectTemplate = (template) => {
    setSelectedLabelTemplate(template);
    setShowLabelPrintModal(false);
    setShowLabelPreview(true);
  };

  const handlePrintLabels = async () => {
    try {
      // Load available printers
      const response = await apiHelpers.getPrinters();
      if (response.data.success) {
        setAvailablePrinters(response.data.data || []);
        // Set default printer
        const defaultPrinter = response.data.data.find(p => p.is_default);
        setSelectedPrinter(defaultPrinter || response.data.data[0]);
        setShowLabelPreview(false);
        setShowPrinterSelection(true);
      } else {
        toast.error('Failed to load printers');
      }
    } catch (error) {
      console.error('Error loading printers:', error);
      toast.error('Failed to load printers');
    }
  };

  const handleConfirmPrint = async () => {
    if (!selectedPrinter) {
      toast.error('Please select a printer');
      return;
    }

    try {
      if (selectedPrinter.is_browser) {
        // Use browser print dialog
        window.print();
        toast.success(`Printing ${calculations.cartonsRequired || 0} label(s)...`);
      } else {
        // Send to specific printer
        const response = await apiHelpers.printLabel({
          printer_name: selectedPrinter.name,
          is_browser: false,
          template: selectedLabelTemplate,
          data: getLabelData(),
          copies: calculations.cartonsRequired || 1
        });
        
        if (response.data.success) {
          if (response.data.use_browser_print) {
            window.print();
          }
          toast.success(response.data.message);
        } else {
          toast.error('Failed to print labels');
        }
      }
      setShowPrinterSelection(false);
    } catch (error) {
      console.error('Error printing:', error);
      toast.error('Failed to print labels');
    }
  };

  // Get label data from order
  const getLabelData = () => {
    if (!jobData?.order || !productSpecs) return {};
    
    // Get cores per carton from product specs (tubes_per_carton)
    const coresPerCarton = calculations.tubesPerCarton || productSpecs.tubes_per_carton || 0;
    
    // Get product description - use client's product description if available
    let productDescription = '';
    if (jobData.order.product_description) {
      productDescription = jobData.order.product_description;
    } else if (productSpecs.product_description) {
      productDescription = productSpecs.product_description;
    } else {
      // Fallback to building description from specs
      const productType = productSpecs.product_type || 'Paper Core';
      const id = productSpecs.internal_diameter ? `${productSpecs.internal_diameter}mm ID` : '';
      const thickness = productSpecs.wall_thickness ? `${productSpecs.wall_thickness}mm T` : '';
      const width = productSpecs.width ? `${productSpecs.width}mm W` : '';
      productDescription = `${productType}${id ? ' - ' + id : ''}${thickness ? ' x ' + thickness : ''}${width ? ' x ' + width : ''}`;
    }
    
    return {
      customer: jobData.order.client_name || '',
      order_number: jobData.order.order_number || jobData.order.id || '',
      due_date: jobData.order.due_date ? new Date(jobData.order.due_date).toLocaleDateString() : '',
      product_item: productSpecs.product_code || '',
      product_details: productDescription,
      product_quantity: `${jobData.order.quantity || 0} units`,
      carton_qty: `${coresPerCarton} cores per carton`
    };
  };

  // Handle adding finished cores directly to stock
  const handleAddFinishedCoresToStock = async () => {
    if (!finishedCoresToStock || finishedCoresToStock <= 0) {
      toast.error('Please enter a valid quantity');
      return;
    }

    if (!jobData?.order || !productSpecs) {
      toast.error('Missing job or product data');
      return;
    }

    try {
      const quantity = parseInt(finishedCoresToStock);
      
      // Create stock entry data for finished products
      const stockData = {
        client_id: jobData.order.client_id,
        client_name: jobData.order.client_name || 'Unknown Client',
        product_id: productSpecs.id,
        product_code: productSpecs.product_code,
        product_description: `${productSpecs.product_code} - Finished Cores`,
        quantity_on_hand: quantity,
        unit_of_measure: 'pieces',
        source_order_id: jobData.order.id,
        source_job_id: jobId,
        is_shared_product: false,
        shared_with_clients: [],
        created_from_excess: true,
        material_specifications: {
          core_diameter: productSpecs.core_diameter || productSpecs.internal_diameter,
          wall_thickness: productSpecs.wall_thickness,
          material_layers: productSpecs.material_layers
        },
        minimum_stock_level: 0
      };

      // Add to stock via API
      const response = await apiHelpers.createRawSubstrate(stockData);
      
      if (response.data.success) {
        toast.success(`${quantity} finished cores added to Products on Hand`);
        setFinishedCoresToStock(''); // Clear input
        return true;
      } else {
        throw new Error(response.data.message || 'Failed to add to stock');
      }
    } catch (error) {
      console.error('Failed to add finished cores to stock:', error);
      toast.error('Failed to add finished cores to stock');
      return false;
    }
  };

  const getCurrentStageTitle = () => {
    const stageNames = {
      paper_slitting: 'Paper Slitting Job Card',
      winding: 'Core Winding Job Card', 
      finishing: 'Cutting/Indexing Job Card',
      delivery: 'Packing/Delivery Job Card'
    };
    return stageNames[stage] || 'Job Card';
  };

  const getMachineConfig = () => MACHINE_LINES[stage] || {};

  const getFinishedQuantityTitle = () => {
    switch (stage) {
      case 'winding':
        return 'Additional Biscuit Widths Produced';
      case 'finishing':
        return 'Total Finished Cores';
      case 'paper_slitting':
        return 'Additional Widths & Meters';
      default:
        return 'Finished Production Quantity';
    }
  };

  // Calculate material requirements based on spiral core manufacturing formula
  const calculateMaterialRequirements = (productSpecs, jobData, coreWindingSpec) => {
    if (!productSpecs?.material_layers || productSpecs.material_layers.length === 0) {
      return [];
    }

    // Get core specifications in mm
    const coreIdMm = parseFloat(productSpecs.core_id) || 76; // Inner diameter in mm
    const coreLengthMm = parseFloat(productSpecs.core_width) || parseFloat(productSpecs.width) || 1200; // Core length in mm
    const orderQuantity = jobData?.order?.quantity || 1;
    
    // Convert to meters
    const coreIdM = coreIdMm / 1000;
    const coreLengthM = coreLengthMm / 1000;
    
    // Calculate inner radius
    const innerRadiusM = coreIdM / 2;
    
    // Track current radius position as we build layers
    let currentInnerRadius = innerRadiusM;
    
    const materialRequirements = productSpecs.material_layers.map((layer, index) => {
      const thicknessMm = parseFloat(layer.thickness) || 0; // Thickness per single layer in mm
      const gsm = parseFloat(layer.gsm) || 0; // Grams per square metre
      const numLayers = parseInt(layer.quantity) || 1; // How many layers of this material
      const layerWidthMm = parseFloat(layer.width) || 0; // Width in mm (if material is cut into strips)
      
      // Convert to meters
      const thicknessM = thicknessMm / 1000;
      const layerWidthM = layerWidthMm / 1000;
      
      // Calculate total thickness for this material stream
      const totalStreamThicknessM = thicknessM * numLayers;
      
      // Calculate inner and outer radius for this material stream
      const streamInnerRadius = currentInnerRadius;
      const streamOuterRadius = currentInnerRadius + totalStreamThicknessM;
      
      // Calculate volume using cylinder shell formula
      // Volume = π × core_length × (outer_radius² - inner_radius²)
      const volumeM3 = Math.PI * coreLengthM * (
        (streamOuterRadius ** 2) - (streamInnerRadius ** 2)
      );
      
      // Calculate density from GSM and thickness
      // density = GSM ÷ thickness(mm) gives kg/m³
      const densityKgM3 = (thicknessMm > 0 && gsm > 0) ? (gsm / thicknessMm) : 0;
      
      // Calculate mass: mass = volume × density
      const massKgPerCore = volumeM3 * densityKgM3;
      
      // Calculate surface area: area = volume ÷ thickness
      const areaM2PerCore = (totalStreamThicknessM > 0) ? (volumeM3 / totalStreamThicknessM) : 0;
      
      // Calculate strip length if layer width is provided
      const stripLengthMPerCore = (layerWidthM > 0) ? (areaM2PerCore / layerWidthM) : 0;
      
      // Calculate totals for entire order
      const totalMassKg = massKgPerCore * orderQuantity;
      const totalAreaM2 = areaM2PerCore * orderQuantity;
      const totalStripLengthM = stripLengthMPerCore * orderQuantity;
      
      // Use strip length if available, otherwise use area
      const metersPerCore = stripLengthMPerCore > 0 ? stripLengthMPerCore : areaM2PerCore;
      const totalMeters = metersPerCore * orderQuantity;
      
      // Update current radius for next layer
      currentInnerRadius = streamOuterRadius;

      return {
        ...layer,
        metersPerCore: metersPerCore,
        totalMeters: totalMeters,
        massKgPerCore: massKgPerCore,
        totalMassKg: totalMassKg,
        areaM2PerCore: areaM2PerCore,
        totalAreaM2: totalAreaM2,
        stripLengthMPerCore: stripLengthMPerCore,
        totalStripLengthM: totalStripLengthM,
        lapsPerCore: numLayers,
        streamInnerRadiusMm: streamInnerRadius * 1000,
        streamOuterRadiusMm: streamOuterRadius * 1000,
        volumeM3PerCore: volumeM3,
        densityKgM3: densityKgM3,
        layerOrder: index + 1
      };
    });

    return materialRequirements;
  };

  // Get core winding specification for calculations
  const getCoreWindingSpecForCalculation = () => {
    // Core winding specifications from Machinery Specifications
    const coreWindingSpecs = [
      { id: 'cw_15_20', range: [15, 20], recommendedAngle: '72°', lengthFactor: '3.236' },
      { id: 'cw_21_30', range: [21, 30], recommendedAngle: '70°', lengthFactor: '2.924' },
      { id: 'cw_31_50', range: [31, 50], recommendedAngle: '68°', lengthFactor: '2.670' },
      { id: 'cw_51_70', range: [51, 70], recommendedAngle: '66°', lengthFactor: '2.459' },
      { id: 'cw_71_120', range: [71, 120], recommendedAngle: '65°', lengthFactor: '2.366' },
      { id: 'cw_121_200', range: [121, 200], recommendedAngle: '64°', lengthFactor: '2.281' },
      { id: 'cw_201_plus', range: [201, 999], recommendedAngle: '62°', lengthFactor: '2.130' }
    ];
    
    // First try to use the specified core_winding_spec_id
    if (productSpecs?.core_winding_spec_id) {
      const specById = coreWindingSpecs.find(spec => spec.id === productSpecs.core_winding_spec_id);
      if (specById) return specById;
    }
    
    // If no spec_id or not found, auto-determine based on core diameter (core_id)
    const coreDiameter = parseFloat(productSpecs?.core_id) || 76; // Default to 76mm if not specified
    
    for (const spec of coreWindingSpecs) {
      if (coreDiameter >= spec.range[0] && coreDiameter <= spec.range[1]) {
        return spec;
      }
    }
    
    // Default fallback
    return coreWindingSpecs[4]; // 71-120mm range as default
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400 mx-auto"></div>
          <p className="text-white mt-4">Loading job card...</p>
        </div>
      </div>
    );
  }

  if (!jobData || !jobData.order) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-8">
          <p className="text-white">Failed to load job card data</p>
          <button onClick={onClose} className="misty-button misty-button-secondary mt-4">Close</button>
        </div>
      </div>
    );
  }

  const { order } = jobData;
  const machineConfig = getMachineConfig();

  // Safety checks for required data
  if (!order || (!order.id && !orderId && !jobId)) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-8">
          <p className="text-white">Invalid job card data - missing order ID</p>
          <button onClick={onClose} className="misty-button misty-button-secondary mt-4">Close</button>
        </div>
      </div>
    );
  }

  try {
    return (
      <>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-gray-800 rounded-lg w-[90vw] max-w-4xl max-h-[90vh] overflow-y-auto border border-gray-700">
        {/* Header - No Print */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700 no-print">
          <h2 className="text-xl font-bold text-white">{getCurrentStageTitle()}</h2>
          <div className="flex items-center space-x-2">
            {/* Job Timing Button */}
            {!isJobRunning ? (
              <button
                onClick={handleStartJob}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                <ClockIcon className="h-4 w-4 mr-2" />
                Start Job
              </button>
            ) : (
              <button
                onClick={handleCompleteRun}
                className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              >
                <ClockIcon className="h-4 w-4 mr-2" />
                Complete Run
              </button>
            )}
            
            <button
              onClick={handlePrint}
              className="misty-button misty-button-primary flex items-center"
            >
              <PrinterIcon className="h-4 w-4 mr-2" />
              Print
            </button>
            <button
              onClick={onClose}
              className="misty-button misty-button-secondary flex items-center"
            >
              <XMarkIcon className="h-4 w-4 mr-2" />
              Close
            </button>
          </div>
        </div>

        {/* Printable Content */}
        <div className="p-6 print-content">
          {/* Job Card Header */}
          <div className="text-center mb-6 border-b-2 border-gray-600 pb-4">
            <h1 className="text-2xl font-bold text-white">{getCurrentStageTitle()}</h1>
            <p className="text-gray-400">Generated: {new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}</p>
            {isJobRunning && jobStartTime && (
              <div className="mt-2 inline-flex items-center px-3 py-1 bg-green-600 text-white text-sm rounded-full animate-pulse">
                <ClockIcon className="h-4 w-4 mr-1" />
                Job Running Since: {new Date(jobStartTime).toLocaleTimeString()}
              </div>
            )}
            {!isJobRunning && actualRunTime > 0 && (
              <div className="mt-2 inline-flex items-center px-3 py-1 bg-blue-600 text-white text-sm rounded-full">
                <ClockIcon className="h-4 w-4 mr-1" />
                Completed - Runtime: {Math.floor(actualRunTime / 60)}h {actualRunTime % 60}m
              </div>
            )}
          </div>

          {/* Order Information */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-700 p-4 rounded-lg border border-gray-600">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                <DocumentTextIcon className="h-5 w-5 mr-2" />
                Order Information
              </h3>
              <div className="space-y-2 text-sm">
                <div className="text-gray-300"><strong className="text-white">Order ID:</strong> {jobData?.order?.order_number || `ORD-${orderId || jobId}` || 'N/A'}</div>
                <div className="text-gray-300"><strong className="text-white">Customer:</strong> {jobData?.order?.client_name || 'Unknown Client'}</div>
                <div className="text-gray-300"><strong className="text-white">Quantity:</strong> {(jobData?.order?.quantity || 1000)?.toLocaleString()} units</div>
                
                {/* Stock Allocation Information */}
                {jobData?.order?.items?.some(item => item.allocated_stock > 0) && (
                  <div className="mt-3 p-3 bg-blue-900/20 border border-blue-500 rounded">
                    <div className="text-blue-300 font-medium mb-2">📦 Stock Allocated</div>
                    {jobData.order.items.map((item, index) => 
                      item.allocated_stock > 0 && (
                        <div key={index} className="text-sm space-y-1">
                          <div className="text-blue-200">
                            <strong>Product:</strong> {item.product_name}
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="text-blue-200">
                              <strong>From Stock:</strong> {item.allocated_stock?.toLocaleString()} units
                            </div>
                            <div className="text-blue-200">
                              <strong>To Produce:</strong> {item.remaining_to_produce?.toLocaleString()} units
                            </div>
                          </div>
                          {index < jobData.order.items.filter(i => i.allocated_stock > 0).length - 1 && (
                            <hr className="border-blue-600 my-2" />
                          )}
                        </div>
                      )
                    )}
                  </div>
                )}
                <div className="text-gray-300"><strong className="text-white">Due Date:</strong> {jobData?.order?.due_date ? new Date(jobData.order.due_date).toLocaleDateString() : 'Not set'}</div>
                <div className="text-gray-300"><strong className="text-white">Priority:</strong> 
                  <span className={`ml-2 px-2 py-1 rounded text-xs ${
                    jobData?.order?.priority === 'ASAP' ? 'bg-red-600 text-white' : 
                    jobData?.order?.priority === 'Must Delivery On Date' ? 'bg-orange-600 text-white' : 
                    'bg-green-600 text-white'
                  }`}>
                    {jobData?.order?.priority || 'Normal/Low'}
                  </span>
                </div>
                <div className="text-gray-300"><strong className="text-white">Run Number:</strong> {jobData?.run_number || '1'}</div>
              </div>
            </div>

            {/* Machine Line Selection */}
            <div className="bg-gray-700 p-4 rounded-lg border border-gray-600">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                <CogIcon className="h-5 w-5 mr-2" />
                Machine Line: {machineConfig.name}
              </h3>
              <div className="space-y-3">
                {stage === 'paper_slitting' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">Selected Machine:</label>
                    <select 
                      value={selectedMachine}
                      onChange={(e) => setSelectedMachine(e.target.value)}
                      className="misty-select w-full"
                    >
                      {machineConfig.machines?.map(machine => (
                        <option key={machine} value={machine}>{machine}</option>
                      ))}
                    </select>
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Setup Notes:</label>
                  <textarea
                    value={setupNotes}
                    onChange={(e) => setSetupNotes(e.target.value)}
                    className="misty-input w-full h-16 resize-none"
                    placeholder="Special tooling, mandrel requirements..."
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Product Specifications */}
          {productSpecs && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-3 border-b border-gray-600 pb-2">
                Product Specifications
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-700 p-3 rounded border border-gray-600">
                  <div className="text-sm text-gray-400">Product Code</div>
                  <div className="font-medium text-white">{productSpecs.product_code}</div>
                </div>
                <div className="bg-gray-700 p-3 rounded border border-gray-600">
                  <div className="text-sm text-gray-400">Core ID (mm)</div>
                  <div className="font-medium text-white">{productSpecs.core_id || 'N/A'}</div>
                </div>
                <div className="bg-gray-700 p-3 rounded border border-gray-600">
                  <div className="text-sm text-gray-400">Tube Length (mm)</div>
                  <div className="font-medium text-white">{productSpecs.core_width || 'N/A'}</div>
                </div>
                <div className="bg-gray-700 p-3 rounded border border-gray-600">
                  <div className="text-sm text-gray-400">Wall Thickness (mm)</div>
                  <div className="font-medium text-white">{productSpecs.core_thickness || 'N/A'}</div>
                </div>
                <div className="bg-gray-700 p-3 rounded border border-gray-600">
                  <div className="text-sm text-gray-400">Special Tooling</div>
                  <div className="font-medium text-white text-xs">{productSpecs.special_tooling_notes || 'None'}</div>
                </div>
                <div className="bg-gray-700 p-3 rounded border border-gray-600">
                  <div className="text-sm text-gray-400">Packing Notes</div>
                  <div className="font-medium text-white text-xs">{productSpecs.packing_instructions || 'Standard'}</div>
                </div>
              </div>
            </div>
          )}

          {/* Materials Required Section - Condensed */}
          {(stage === 'paper_slitting' || stage === 'winding') && (
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-white mb-2 border-b border-gray-600 pb-1">
                Materials Required
              </h3>
              <div className="bg-gray-700 p-3 rounded border border-gray-600">
                {productSpecs?.material_layers && productSpecs.material_layers.length > 0 ? (
                  (() => {
                    const coreWindingSpec = getCoreWindingSpecForCalculation();
                    const materialRequirements = calculateMaterialRequirements(productSpecs, jobData, coreWindingSpec);
                    
                    return (
                      <div className="space-y-2">
                        {/* Condensed Material List */}
                        {materialRequirements.map((layer, index) => (
                          <div key={index} className="flex items-center justify-between bg-gray-800 p-2 rounded border border-gray-500">
                            <div className="flex-1">
                              <div className="text-sm text-white font-medium">
                                {layer.product_name || layer.material_name || 'Unknown Product'}
                              </div>
                              <div className="text-xs text-gray-400">
                                {layer.layer_type} • {layer.width || 'N/A'}mm × {layer.thickness || 'N/A'}mm • GSM: {layer.gsm || 'N/A'} • {layer.lapsPerCore} laps
                              </div>
                            </div>
                            <div className="text-right ml-3">
                              <div className="text-sm font-bold text-green-400">
                                {layer.totalMeters.toFixed(1)}m
                              </div>
                              <div className="text-xs text-gray-500">
                                {layer.metersPerCore.toFixed(1)}m/core
                              </div>
                            </div>
                          </div>
                        ))}
                        
                        {/* Compact calculation summary at bottom */}
                        <div className="text-xs text-gray-400 mt-2 pt-2 border-t border-gray-600">
                          Formula: Layer Circumference × Angle Factor {materialRequirements[0]?.lengthFactor || '2.366'} × Laps × {jobData?.order?.quantity || 1} cores
                          <br />
                          <span className="text-gray-500">Layers ordered by width (narrower=inner, wider=outer), each layer calculated at its radius</span>
                        </div>
                      </div>
                    );
                  })()
                ) : (
                  <div className="bg-yellow-600/20 p-2 rounded border border-yellow-600">
                    <div className="text-yellow-200 text-sm">
                      No material layers found in product specifications
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Production Calculations - Hidden for Finishing stage */}
          {stage !== 'finishing' && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-3 border-b border-gray-600 pb-2 flex items-center">
              <CalculatorIcon className="h-5 w-5 mr-2" />
              Production Calculations
            </h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* First Column - Material Requirements */}
              <div>
                <h4 className="font-semibold text-white mb-2">Material Requirements (metres)</h4>
                <table className="w-full text-sm border border-gray-600">
                  <tbody>
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">Good Material Length</td>
                      <td className="p-2 text-right font-medium text-white">{calculations.goodMaterialLength?.toLocaleString()}</td>
                    </tr>
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">Makeready Allowance ({calculations.makereadyPercentage}%)</td>
                      <td className="p-2 text-right font-medium text-white">{calculations.makereadyLength?.toLocaleString()}</td>
                    </tr>
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">Waste Allowance ({calculations.wastePercentage}%)</td>
                      <td className="p-2 text-right font-medium text-white">{calculations.wasteLength?.toLocaleString()}</td>
                    </tr>
                    <tr className="bg-yellow-600 font-bold text-white">
                      <td className="p-2">TOTAL LENGTH REQUIRED</td>
                      <td className="p-2 text-right">{calculations.totalLengthRequired?.toLocaleString()}</td>
                    </tr>
                  </tbody>
                </table>

                {/* Finished Production Quantity Section */}
                <div className="mt-4">
                  <h4 className="font-semibold text-white mb-2">{getFinishedQuantityTitle()}</h4>
                  
                  {stage === 'winding' ? (
                    <div className="bg-green-600 p-3 rounded border border-green-500">
                      <span className="text-white font-medium block mb-2">Additional Biscuit Widths:</span>
                      
                      {/* Simplified Form */}
                      <div className="mb-3 space-y-2">
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <input
                              type="number"
                              step="0.1"
                              placeholder="Width (mm)"
                              value={newMasterCore.width}
                              onChange={(e) => setNewMasterCore(prev => ({ ...prev, width: e.target.value }))}
                              className="w-full px-2 py-1 text-sm bg-gray-600 border border-gray-500 rounded text-white"
                            />
                          </div>
                          <div>
                            <input
                              type="number"
                              placeholder="Quantity"
                              value={newMasterCore.quantity}
                              onChange={(e) => setNewMasterCore(prev => ({ ...prev, quantity: e.target.value }))}
                              className="w-full px-2 py-1 text-sm bg-gray-600 border border-gray-500 rounded text-white"
                            />
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <label className="flex items-center text-sm text-green-100">
                            <input
                              type="checkbox"
                              checked={newMasterCore.addToStock}
                              onChange={(e) => setNewMasterCore(prev => ({ ...prev, addToStock: e.target.checked }))}
                              className="w-4 h-4 text-green-500 bg-gray-600 border-gray-500 rounded mr-2"
                            />
                            Add excess to stock
                          </label>
                          <button
                            onClick={handleAddMasterCore}
                            disabled={!newMasterCore.width || !newMasterCore.quantity}
                            className="px-3 py-1 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700 disabled:opacity-50"
                          >
                            + Add Entry
                          </button>
                        </div>
                      </div>
                      
                      {/* Core Entries - Simple List */}
                      {masterCores.length > 0 && (
                        <div className="space-y-1">
                          <div className="text-xs text-green-100 font-semibold border-b border-green-500 pb-1">
                            Biscuit Width Entries:
                          </div>
                          {masterCores.map((core) => {
                            const requiredQuantity = jobData?.order?.quantity || 0;
                            const excessCores = Math.max(0, core.quantity - requiredQuantity);
                            
                            return (
                              <div key={core.id} className="bg-green-700 p-2 rounded text-sm">
                                <div className="flex justify-between items-center">
                                  <span className="text-white">{core.width}mm × {core.quantity} pieces</span>
                                  <div className="flex items-center space-x-2">
                                    {excessCores > 0 && (
                                      <span className="text-yellow-300 text-xs">+{excessCores} excess</span>
                                    )}
                                    {core.addToStock && <span className="text-yellow-300 text-xs">📦</span>}
                                    <button
                                      onClick={() => handleRemoveMasterCore(core.id)}
                                      className="text-red-300 hover:text-red-200 text-xs"
                                    >
                                      ✕
                                    </button>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                          
                          {/* Compact Summary */}
                          {jobData?.order?.quantity && (
                            <div className="text-xs text-green-100 pt-1 border-t border-green-500">
                              Total: {masterCores.reduce((sum, core) => sum + core.quantity, 0)} pieces | 
                              Required: {jobData.order.quantity} | 
                              Excess: {masterCores.reduce((sum, core) => sum + Math.max(0, core.quantity - jobData.order.quantity), 0)}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ) : stage === 'finishing' ? (
                    <div className="bg-blue-600 p-3 rounded border border-blue-500">
                      <span className="text-white font-medium block mb-2">Finishing Operations:</span>
                      
                      <div className="flex items-center justify-between">
                        <span className="text-white font-medium">Total Finished Cores:</span>
                        <div className="flex items-center">
                          {isEditingFinishedQuantity ? (
                            <div className="flex items-center space-x-2">
                              <input
                                type="number"
                                value={editedFinishedQuantity}
                                onChange={(e) => setEditedFinishedQuantity(e.target.value)}
                                className="w-24 px-2 py-1 text-sm bg-gray-600 border border-gray-500 rounded text-white text-center"
                                min="0"
                                autoFocus
                              />
                              <button
                                onClick={handleSaveFinishedQuantity}
                                className="px-2 py-1 bg-blue-700 text-white text-xs rounded hover:bg-blue-800"
                              >
                                ✓
                              </button>
                              <button
                                onClick={handleCancelEditFinishedQuantity}
                                className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                              >
                                ✕
                              </button>
                            </div>
                          ) : (
                            <span
                              onDoubleClick={handleEditFinishedQuantity}
                              className="cursor-pointer hover:bg-blue-700 px-2 py-1 rounded text-white font-bold"
                              title="Double-click to edit finished quantity"
                            >
                              {finishedQuantity.toLocaleString()} cores
                            </span>
                          )}
                        </div>
                      </div>
                      
                      {/* Show excess calculation if quantity is higher than required */}
                      {finishedQuantity > 0 && jobData?.order?.quantity && (
                        <div className="mt-2 text-sm">
                          <div className="flex justify-between text-blue-100">
                            <span>Required Quantity:</span>
                            <span>{jobData.order.quantity.toLocaleString()}</span>
                          </div>
                          {finishedQuantity > jobData.order.quantity && (
                            <div className="flex justify-between text-yellow-200 font-medium">
                              <span>Excess for Stocktake:</span>
                              <span>{(finishedQuantity - jobData.order.quantity).toLocaleString()}</span>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* Additional Cores Produced Section */}
                      <div className="mt-4 border-t border-blue-500 pt-3">
                        <span className="text-white font-medium block mb-2">Additional Cores Produced:</span>
                        
                        {/* Add new core form */}
                        <div className="mb-3 space-y-2">
                          <div className="grid grid-cols-3 gap-2">
                            <div>
                              <input
                                type="number"
                                step="0.1"
                                placeholder="Width (mm)"
                                value={newMasterCore.width}
                                onChange={(e) => setNewMasterCore(prev => ({ ...prev, width: e.target.value }))}
                                className="w-full px-2 py-1 text-sm bg-gray-600 border border-gray-500 rounded text-white"
                              />
                            </div>
                            <div>
                              <input
                                type="number"
                                placeholder="Quantity"
                                value={newMasterCore.quantity}
                                onChange={(e) => setNewMasterCore(prev => ({ ...prev, quantity: e.target.value }))}
                                className="w-full px-2 py-1 text-sm bg-gray-600 border border-gray-500 rounded text-white"
                              />
                            </div>
                            <div>
                              <button
                                onClick={handleAddMasterCore}
                                disabled={!newMasterCore.width || !newMasterCore.quantity}
                                className="w-full px-3 py-1 bg-blue-700 text-white text-sm rounded hover:bg-blue-800 disabled:opacity-50"
                              >
                                + Add Core
                              </button>
                            </div>
                          </div>
                        </div>
                        
                        {/* Core Entries List */}
                        {masterCores.length > 0 && (
                          <div className="space-y-1">
                            <div className="text-xs text-blue-100 font-semibold border-b border-blue-500 pb-1">
                              Additional Cores Produced:
                            </div>
                            {masterCores.map((core) => (
                              <div key={core.id} className="bg-blue-700 p-2 rounded text-sm">
                                <div className="flex justify-between items-center">
                                  <span className="text-white">{core.width}mm × {core.quantity} cores</span>
                                  <div className="flex items-center space-x-2">
                                    <button
                                      onClick={() => handleAddToStockOnHand(core)}
                                      className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                                      title="Add to Stock on Hand"
                                    >
                                      Add to Stock
                                    </button>
                                    <button
                                      onClick={() => handleRemoveMasterCore(core.id)}
                                      className="text-red-300 hover:text-red-200 text-xs"
                                    >
                                      ✕
                                    </button>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                      
                      {/* Add Additional Finished Cores to Stock Section */}
                      <div className="mt-4 border-t border-blue-500 pt-3">
                        <span className="text-white font-medium block mb-2">Add Additional Finished Cores to Stock:</span>
                        <div className="bg-blue-700/30 p-3 rounded border border-blue-500">
                          <p className="text-xs text-blue-200 mb-2">
                            Enter the quantity of finished cores to add directly to Products on Hand stock list
                          </p>
                          <div className="flex items-center space-x-2">
                            <input
                              type="number"
                              placeholder="Quantity"
                              value={finishedCoresToStock}
                              onChange={(e) => setFinishedCoresToStock(e.target.value)}
                              className="flex-1 px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white"
                              min="1"
                            />
                            <button
                              onClick={handleAddFinishedCoresToStock}
                              disabled={!finishedCoresToStock || finishedCoresToStock <= 0}
                              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              Add to Stock
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-green-600 p-3 rounded border border-green-500">
                      <div className="flex items-center justify-between">
                        <span className="text-white font-medium">
                          {stage === 'paper_slitting' ? 'Additional Production:' : 'Finished Quantity:'}
                        </span>
                        <div className="flex items-center">
                          {isEditingFinishedQuantity ? (
                            <div className="flex items-center space-x-2">
                              <input
                                type="number"
                                value={editedFinishedQuantity}
                                onChange={(e) => setEditedFinishedQuantity(e.target.value)}
                                className="w-24 px-2 py-1 text-sm bg-gray-600 border border-gray-500 rounded text-white text-center"
                                min="0"
                                autoFocus
                              />
                              <button
                                onClick={handleSaveFinishedQuantity}
                                className="px-2 py-1 bg-green-700 text-white text-xs rounded hover:bg-green-800"
                              >
                                ✓
                              </button>
                              <button
                                onClick={handleCancelEditFinishedQuantity}
                                className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                              >
                                ✕
                              </button>
                            </div>
                          ) : (
                            <span
                              onDoubleClick={handleEditFinishedQuantity}
                              className="cursor-pointer hover:bg-green-700 px-2 py-1 rounded text-white font-bold"
                              title="Double-click to edit finished quantity"
                            >
                              {finishedQuantity.toLocaleString()} {stage === 'finishing' ? 'cores' : 'units'}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      {/* Show excess calculation if quantity is higher than required */}
                      {finishedQuantity > 0 && jobData?.order?.quantity && (
                        <div className="mt-2 text-sm">
                          <div className="flex justify-between text-green-100">
                            <span>Required Quantity:</span>
                            <span>{jobData.order.quantity.toLocaleString()}</span>
                          </div>
                          {finishedQuantity > jobData.order.quantity && (
                            <div className="flex justify-between text-yellow-200 font-medium">
                              <span>Excess for Stocktake:</span>
                              <span>{(finishedQuantity - jobData.order.quantity).toLocaleString()}</span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
                
                {stage === 'paper_slitting' && (
                  <div className="mt-3">
                        <div className="text-sm text-green-200 font-medium mb-3">Additional Widths Produced:</div>
                        
                        {/* Add new width form */}
                        <div className="bg-gray-800 p-3 rounded-lg mb-3">
                          <div className="space-y-2">
                            {/* Material dropdown */}
                            <div>
                              <label className="text-xs text-gray-300 block mb-1">Select Material from Raw Materials:</label>
                              <select
                                value={newSlittingWidth.material_id}
                                onChange={(e) => {
                                  const selectedId = e.target.value;
                                  const selectedMat = rawMaterials.find(
                                    m => m.material_id === selectedId
                                  );
                                  setNewSlittingWidth(prev => ({ 
                                    ...prev, 
                                    material_id: selectedId,
                                    material_name: selectedMat ? selectedMat.material_name : ''
                                  }));
                                }}
                                className="w-full px-2 py-1 text-xs bg-gray-600 border border-gray-500 rounded text-white"
                              >
                                <option value="">-- Select Raw Material --</option>
                                {rawMaterials.length === 0 ? (
                                  <option disabled>No raw materials available</option>
                                ) : (
                                  rawMaterials.map((material) => (
                                    <option 
                                      key={material.material_id} 
                                      value={material.material_id}
                                    >
                                      {material.material_name || 'Unknown Material'}
                                    </option>
                                  ))
                                )}
                              </select>
                              {rawMaterials.length === 0 && (
                                <p className="text-xs text-yellow-400 mt-1">
                                  No raw materials found. Add materials to Raw Materials stock first.
                                </p>
                              )}
                            </div>

                            {/* Width and Meters inputs */}
                            <div className="flex items-center space-x-2">
                              <div className="flex-1">
                                <label className="text-xs text-gray-300 block mb-1">Width (mm):</label>
                                <input
                                  type="number"
                                  placeholder="Width"
                                  value={newSlittingWidth.width}
                                  onChange={(e) => setNewSlittingWidth(prev => ({ ...prev, width: e.target.value }))}
                                  className="w-full px-2 py-1 text-xs bg-gray-600 border border-gray-500 rounded text-white"
                                />
                              </div>
                              <div className="flex-1">
                                <label className="text-xs text-gray-300 block mb-1">Meters:</label>
                                <input
                                  type="number"
                                  placeholder="Meters"
                                  value={newSlittingWidth.meters}
                                  onChange={(e) => setNewSlittingWidth(prev => ({ ...prev, meters: e.target.value }))}
                                  className="w-full px-2 py-1 text-xs bg-gray-600 border border-gray-500 rounded text-white"
                                />
                              </div>
                              <div className="pt-5">
                                <button
                                  onClick={handleAddSlittingWidth}
                                  className="px-3 py-1 bg-green-700 text-white text-xs rounded hover:bg-green-800 whitespace-nowrap"
                                  disabled={!newSlittingWidth.material_id || !newSlittingWidth.width || !newSlittingWidth.meters}
                                >
                                  + Add
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                        
                        {/* Display pending widths */}
                        {pendingSlitWidths.length > 0 && (
                          <div className="mb-3">
                            <div className="text-xs text-gray-400 mb-2">Pending Submissions:</div>
                            <div className="space-y-1 max-h-40 overflow-y-auto bg-gray-800 p-2 rounded">
                              {pendingSlitWidths.map((width) => (
                                <div key={width.id} className="flex items-center justify-between bg-gray-700 px-2 py-1 rounded text-xs">
                                  <div className="flex-1">
                                    <div className="text-green-200 font-medium">{width.material_name}</div>
                                    <div className="text-gray-300">{width.width}mm × {width.meters}m</div>
                                  </div>
                                  <button
                                    onClick={() => handleRemoveSlittingWidth(width.id)}
                                    className="text-red-400 hover:text-red-300 ml-2"
                                    title="Remove width"
                                  >
                                    ✕
                                  </button>
                                </div>
                              ))}
                            </div>
                            
                            {/* Submit button */}
                            <button
                              onClick={handleSubmitSlitWidths}
                              className="mt-3 w-full px-4 py-2 bg-yellow-600 text-white text-sm font-medium rounded hover:bg-yellow-700"
                            >
                              Submit to Raw Materials On Hand ({pendingSlitWidths.length})
                            </button>
                          </div>
                        )}
                        
                        {pendingSlitWidths.length === 0 && (
                          <div className="text-xs text-gray-400 italic">
                            No pending slit widths. Add materials above to submit to Raw Materials.
                          </div>
                        )}
                      </div>
                    )}
              </div>
              
              {/* Second Column - Production Times */}
              <div>
                <h4 className="font-semibold text-white mb-2">Production Times (minutes)</h4>
                <table className="w-full text-sm border border-gray-600">
                  <tbody>
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">Setup Time</td>
                      <td className="p-2 text-right font-medium text-white">{calculations.setupTime}</td>
                    </tr>
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">Run Time (Estimated)</td>
                      <td className="p-2 text-right font-medium text-white">{calculations.runTime}</td>
                    </tr>
                    {/* Actual Run Time Row */}
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">
                        Actual Run Time
                        {isJobRunning && (
                          <span className="ml-2 px-2 py-1 bg-green-600 text-white text-xs rounded-full animate-pulse">
                            RUNNING
                          </span>
                        )}
                      </td>
                      <td className="p-2 text-right font-medium text-white">
                        {isEditingRunTime ? (
                          <div className="flex items-center justify-end space-x-2">
                            <input
                              type="number"
                              value={editedRunTime}
                              onChange={(e) => setEditedRunTime(e.target.value)}
                              className="w-20 px-2 py-1 text-sm bg-gray-600 border border-gray-500 rounded text-white text-center"
                              min="0"
                              autoFocus
                            />
                            <button
                              onClick={handleSaveRunTime}
                              className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                            >
                              ✓
                            </button>
                            <button
                              onClick={handleCancelEditRunTime}
                              className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <span
                            onDoubleClick={actualRunTime > 0 ? handleEditRunTime : undefined}
                            className={`${actualRunTime > 0 ? 'cursor-pointer hover:bg-gray-600 px-2 py-1 rounded' : ''} ${
                              isJobRunning ? 'text-green-400' : actualRunTime > 0 ? 'text-blue-400' : 'text-gray-500'
                            }`}
                            title={actualRunTime > 0 ? "Double-click to edit actual run time" : "Start job to track actual time"}
                          >
                            {isJobRunning 
                              ? `${Math.floor((currentTime - new Date(jobStartTime).getTime()) / (1000 * 60))} min (Live)`
                              : actualRunTime > 0 
                                ? `${Math.floor(actualRunTime / 60)}h ${actualRunTime % 60}m`
                                : '—'
                            }
                          </span>
                        )}
                      </td>
                    </tr>
                    <tr className="bg-green-600 font-bold text-white">
                      <td className="p-2">TOTAL PRODUCTION TIME</td>
                      <td className="p-2 text-right">{calculations.totalProductionTime}</td>
                    </tr>
                    <tr>
                      <td className="p-2 text-gray-400 text-xs" colSpan="2">
                        Estimated finish: {calculations.totalProductionTime ? `${calculations.totalProductionTime} minutes from start` : 'N/A'}
                        {actualRunTime > 0 && (
                          <div className="mt-1">
                            Tip: Double-click actual run time to adjust for stoppages
                          </div>
                        )}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          )}

          {/* Quality Control & Safety section temporarily removed - will be re-added at bottom */}

          {/* Packing & Delivery section temporarily removed - will be re-added at bottom */}

          {/* Other Products in Order */}
          {order?.other_products && order.other_products.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-3 border-b border-gray-600 pb-2">
                Other Products in this Order
              </h3>
              <div className="bg-gray-700 p-3 rounded border border-gray-600">
                <ul className="text-sm space-y-1">
                  {order?.other_products?.map((product, index) => (
                    <li key={index} className="flex justify-between text-gray-300">
                      <span>{product.code} - {product.description}</span>
                      <span>Qty: {product.quantity}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Operator Sign-off section temporarily removed - will be re-added at bottom */}

          {/* === SECTIONS RE-ADDED BELOW FOR PROPER CONTAINMENT === */}

          {/* Quality Control & Safety - Hidden for Core Winding Jobs and Slitting Jobs */}
          {productSpecs?.qc_tolerances && stage !== 'winding' && stage !== 'paper_slitting' && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-3 border-b border-gray-600 pb-2 flex items-center">
                <ShieldCheckIcon className="h-5 w-5 mr-2" />
                Quality Control & Safety
              </h3>
              <div>
                <h4 className="font-semibold text-white mb-2">QC Tolerances</h4>
                <table className="w-full text-sm border border-gray-600 max-w-md">
                  <tbody>
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">ID Tolerance</td>
                      <td className="p-2 text-right text-white">±{productSpecs.qc_tolerances.id_tolerance} mm</td>
                    </tr>
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">OD Tolerance</td>
                      <td className="p-2 text-right text-white">±{productSpecs.qc_tolerances.od_tolerance} mm</td>
                    </tr>
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">Wall Tolerance</td>
                      <td className="p-2 text-right text-white">±{productSpecs.qc_tolerances.wall_tolerance} mm</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Consumables Required - Show for Finishing Stage */}
          {stage === 'finishing' && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-3 border-b border-gray-600 pb-2 flex items-center">
                <DocumentTextIcon className="h-5 w-5 mr-2" />
                Consumables Required
              </h3>
              <div className="bg-gray-700 p-4 rounded border border-gray-600">
                <table className="w-full text-sm border border-gray-600">
                  <thead>
                    <tr className="bg-gray-600">
                      <th className="p-2 text-left text-white">Item</th>
                      <th className="p-2 text-right text-white">Quantity Required</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">Cartons Required</td>
                      <td className="p-2 text-right font-medium text-white">{calculations.cartonsRequired || 'N/A'}</td>
                    </tr>
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">Tape Rolls Required</td>
                      <td className="p-2 text-right font-medium text-white">{calculations.tapeRollsRequired || 'N/A'}</td>
                    </tr>
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">Pallet Wrap</td>
                      <td className="p-2 text-right font-medium text-white">As needed</td>
                    </tr>
                    <tr className="border-b border-gray-600">
                      <td className="p-2 bg-gray-700 text-gray-300">Labels (Carton Labels)</td>
                      <td className="p-2 text-right font-medium text-white">{calculations.cartonsRequired || 'N/A'}</td>
                    </tr>
                    {productSpecs?.consumables && productSpecs.consumables.length > 0 && (
                      productSpecs.consumables.map((consumable, index) => (
                        <tr key={index} className="border-b border-gray-600">
                          <td className="p-2 bg-gray-700 text-gray-300">{consumable.specification_name}</td>
                          <td className="p-2 text-right font-medium text-white">{consumable.measurement_unit}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
                
                {/* Print Carton Labels Button */}
                <div className="mt-4">
                  <button
                    onClick={handlePrintCartonLabels}
                    className="w-full px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 flex items-center justify-center space-x-2"
                  >
                    <PrinterIcon className="h-5 w-5" />
                    <span>Print Carton Labels ({calculations.cartonsRequired || 0} labels)</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Order Products List - Show for Finishing Stage */}
          {stage === 'finishing' && jobData?.order?.items && jobData.order.items.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-3 border-b border-gray-600 pb-2 flex items-center">
                <DocumentTextIcon className="h-5 w-5 mr-2" />
                Order Products Checklist
              </h3>
              <div className="bg-gray-700 p-4 rounded border border-gray-600">
                <p className="text-sm text-gray-300 mb-3">
                  Check off each product as it's completed and ready for packing:
                </p>
                <div className="space-y-2">
                  {jobData.order.items.map((item, index) => (
                    <div 
                      key={index}
                      className={`flex items-center p-3 rounded border transition-all ${
                        completedProducts[index] 
                          ? 'bg-green-900/30 border-green-500' 
                          : 'bg-gray-600 border-gray-500'
                      }`}
                    >
                      <input
                        type="checkbox"
                        id={`product-${index}`}
                        checked={completedProducts[index] || false}
                        onChange={() => handleToggleProductCompletion(index)}
                        className="w-5 h-5 text-green-600 bg-gray-700 border-gray-500 rounded focus:ring-green-500 focus:ring-2 cursor-pointer"
                      />
                      <label 
                        htmlFor={`product-${index}`}
                        className="ml-3 flex-1 cursor-pointer"
                      >
                        <div className="flex justify-between items-center">
                          <div>
                            <span className={`font-medium ${completedProducts[index] ? 'text-green-300' : 'text-white'}`}>
                              {item.product_name || item.product_code || 'Product'}
                            </span>
                            {item.allocated_stock && (
                              <span className="ml-2 text-xs text-blue-300">
                                (Stock Allocated: {item.allocated_stock.quantity})
                              </span>
                            )}
                          </div>
                          <div className="text-right">
                            <span className={`text-sm ${completedProducts[index] ? 'text-green-300' : 'text-gray-300'}`}>
                              Qty: {item.quantity}
                            </span>
                            {item.unit_price && (
                              <span className="ml-3 text-xs text-gray-400">
                                ${parseFloat(item.unit_price).toFixed(2)} ea
                              </span>
                            )}
                          </div>
                        </div>
                      </label>
                      {completedProducts[index] && (
                        <div className="ml-3">
                          <span className="text-green-400 text-xl">✓</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                
                {/* Completion Summary */}
                <div className="mt-4 pt-3 border-t border-gray-600">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-300">
                      Completion Progress:
                    </span>
                    <span className="text-sm font-bold text-white">
                      {Object.values(completedProducts).filter(Boolean).length} / {jobData.order.items.length} products completed
                    </span>
                  </div>
                  {Object.values(completedProducts).filter(Boolean).length === jobData.order.items.length && (
                    <div className="mt-2 p-2 bg-green-900/50 border border-green-500 rounded text-center">
                      <span className="text-green-300 font-medium text-sm">
                        ✓ All products completed and ready for packing!
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Packing & Delivery - Hidden for Core Winding Jobs and Slitting Jobs */}
          {stage !== 'winding' && stage !== 'paper_slitting' && stage !== 'finishing' && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-white mb-3 border-b border-gray-600 pb-2 flex items-center">
                <TruckIcon className="h-5 w-5 mr-2" />
                Packing & Delivery
              </h3>
              <div className="grid grid-cols-1 gap-4">
                <div>
                  <h4 className="font-semibold text-white mb-2">Packing Requirements</h4>
                  <table className="w-full text-sm border border-gray-600">
                    <tbody>
                      <tr className="border-b border-gray-600">
                        <td className="p-2 bg-gray-700 text-gray-300">Tubes per Carton</td>
                        <td className="p-2 text-right font-medium text-white">{calculations.tubesPerCarton}</td>
                      </tr>
                      <tr className="border-b border-gray-600">
                        <td className="p-2 bg-gray-700 text-gray-300">Cartons Required</td>
                        <td className="p-2 text-right font-medium text-white">{calculations.cartonsRequired}</td>
                      </tr>
                      <tr className="border-b border-gray-600">
                        <td className="p-2 bg-gray-700 text-gray-300">Cartons per Pallet</td>
                        <td className="p-2 text-right font-medium text-white">{calculations.cartonsPerPallet}</td>
                      </tr>
                      <tr className="bg-blue-600 font-bold text-white">
                        <td className="p-2">PALLETS REQUIRED</td>
                        <td className="p-2 text-right">{calculations.palletsRequired}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div>
                  <h4 className="font-semibold text-white mb-2">Consumables Usage</h4>
                  <table className="w-full text-sm border border-gray-600">
                    <tbody>
                      <tr className="border-b border-gray-600">
                        <td className="p-2 bg-gray-700 text-gray-300">Cartons Required</td>
                        <td className="p-2 text-right font-medium text-white">{calculations.cartonsRequired}</td>
                      </tr>
                      <tr className="border-b border-gray-600">
                        <td className="p-2 bg-gray-700 text-gray-300">Tape Rolls Required</td>
                        <td className="p-2 text-right font-medium text-white">{calculations.tapeRollsRequired}</td>
                      </tr>
                      {productSpecs?.consumables && productSpecs.consumables.length > 0 && (
                        productSpecs.consumables.map((consumable, index) => (
                          <tr key={index} className="border-b border-gray-600">
                            <td className="p-2 bg-gray-700 text-gray-300">{consumable.specification_name}</td>
                            <td className="p-2 text-right font-medium text-white">{consumable.measurement_unit}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Operator Sign-off - Show for Finishing Stage and other stages except winding and slitting */}
          {(stage === 'finishing' || (stage !== 'winding' && stage !== 'paper_slitting')) && (
            <div className="border-t-2 border-gray-600 pt-4 mt-8">
              <h3 className="text-lg font-semibold text-white mb-4">
                Operator Sign-off
                <span className="text-sm text-gray-400 ml-3 font-normal">Double-click to sign</span>
              </h3>
              <div className="grid grid-cols-3 gap-6">
                {/* Setup Sign-off */}
                <div className="text-center">
                  {editingSignOff.type === 'setup' ? (
                    <div className="mb-2 h-8 flex items-center justify-center">
                      <input
                        type="text"
                        value={editingSignOff.tempName}
                        onChange={(e) => setEditingSignOff(prev => ({ ...prev, tempName: e.target.value }))}
                        className="w-full px-2 py-1 text-sm bg-gray-600 border border-gray-500 rounded text-white text-center"
                        placeholder="Enter your name"
                        autoFocus
                        onKeyPress={(e) => e.key === 'Enter' && handleSignOffSave()}
                      />
                    </div>
                  ) : (
                    <div 
                      className={`mb-2 h-8 border-b-2 border-gray-500 cursor-pointer hover:bg-gray-700 transition-colors flex items-center justify-center ${
                        signOffs.setup.name ? 'bg-green-900' : ''
                      }`}
                      onDoubleClick={() => handleSignOffDoubleClick('setup')}
                      title="Double-click to sign"
                    >
                      {signOffs.setup.name ? (
                        <div className="flex flex-col">
                          <div className="font-medium text-white">{signOffs.setup.name}</div>
                          {signOffs.setup.date && (
                            <div className="text-xs text-gray-300">{signOffs.setup.date}</div>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-sm">Click to sign</span>
                      )}
                    </div>
                  )}
                  <div className="text-sm text-gray-400">Setup By / Date</div>
                  {editingSignOff.type === 'setup' && (
                    <div className="flex justify-center space-x-1 mt-2">
                      <button
                        onClick={handleSignOffSave}
                        className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                        disabled={!editingSignOff.tempName.trim()}
                      >
                        ✓ Sign
                      </button>
                      <button
                        onClick={handleSignOffCancel}
                        className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                      >
                        ✕ Cancel
                      </button>
                    </div>
                  )}
                  {signOffs.setup.name && editingSignOff.type !== 'setup' && (
                    <button
                      onClick={() => clearSignOff('setup')}
                      className="mt-1 text-xs text-red-400 hover:text-red-300"
                    >
                      Clear
                    </button>
                  )}
                </div>

                {/* Production Sign-off */}
                <div className="text-center">
                  {editingSignOff.type === 'production' ? (
                    <div className="mb-2 h-8 flex items-center justify-center">
                      <input
                        type="text"
                        value={editingSignOff.tempName}
                        onChange={(e) => setEditingSignOff(prev => ({ ...prev, tempName: e.target.value }))}
                        className="w-full px-2 py-1 text-sm bg-gray-600 border border-gray-500 rounded text-white text-center"
                        placeholder="Enter your name"
                        autoFocus
                        onKeyPress={(e) => e.key === 'Enter' && handleSignOffSave()}
                      />
                    </div>
                  ) : (
                    <div 
                      className={`mb-2 h-8 border-b-2 border-gray-500 cursor-pointer hover:bg-gray-700 transition-colors flex items-center justify-center ${
                        signOffs.production.name ? 'bg-green-900' : ''
                      }`}
                      onDoubleClick={() => handleSignOffDoubleClick('production')}
                      title="Double-click to sign"
                    >
                      {signOffs.production.name ? (
                        <div className="flex flex-col">
                          <div className="font-medium text-white">{signOffs.production.name}</div>
                          {signOffs.production.date && (
                            <div className="text-xs text-gray-300">{signOffs.production.date}</div>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-sm">Click to sign</span>
                      )}
                    </div>
                  )}
                  <div className="text-sm text-gray-400">Production By / Date</div>
                  {editingSignOff.type === 'production' && (
                    <div className="flex justify-center space-x-1 mt-2">
                      <button
                        onClick={handleSignOffSave}
                        className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                        disabled={!editingSignOff.tempName.trim()}
                      >
                        ✓ Sign
                      </button>
                      <button
                        onClick={handleSignOffCancel}
                        className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                      >
                        ✕ Cancel
                      </button>
                    </div>
                  )}
                  {signOffs.production.name && editingSignOff.type !== 'production' && (
                    <button
                      onClick={() => clearSignOff('production')}
                      className="mt-1 text-xs text-red-400 hover:text-red-300"
                    >
                      Clear
                    </button>
                  )}
                </div>

                {/* QC Sign-off */}
                <div className="text-center">
                  {editingSignOff.type === 'qc' ? (
                    <div className="mb-2 h-8 flex items-center justify-center">
                      <input
                        type="text"
                        value={editingSignOff.tempName}
                        onChange={(e) => setEditingSignOff(prev => ({ ...prev, tempName: e.target.value }))}
                        className="w-full px-2 py-1 text-sm bg-gray-600 border border-gray-500 rounded text-white text-center"
                        placeholder="Enter your name"
                        autoFocus
                        onKeyPress={(e) => e.key === 'Enter' && handleSignOffSave()}
                      />
                    </div>
                  ) : (
                    <div 
                      className={`mb-2 h-8 border-b-2 border-gray-500 cursor-pointer hover:bg-gray-700 transition-colors flex items-center justify-center ${
                        signOffs.qc.name ? 'bg-green-900' : ''
                      }`}
                      onDoubleClick={() => handleSignOffDoubleClick('qc')}
                      title="Double-click to sign"
                    >
                      {signOffs.qc.name ? (
                        <div className="flex flex-col">
                          <div className="font-medium text-white">{signOffs.qc.name}</div>
                          {signOffs.qc.date && (
                            <div className="text-xs text-gray-300">{signOffs.qc.date}</div>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400 text-sm">Click to sign</span>
                      )}
                    </div>
                  )}
                  <div className="text-sm text-gray-400">QC Check By / Date</div>
                  {editingSignOff.type === 'qc' && (
                    <div className="flex justify-center space-x-1 mt-2">
                      <button
                        onClick={handleSignOffSave}
                        className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                        disabled={!editingSignOff.tempName.trim()}
                      >
                        ✓ Sign
                      </button>
                      <button
                        onClick={handleSignOffCancel}
                        className="px-2 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                      >
                        ✕ Cancel
                      </button>
                    </div>
                  )}
                  {signOffs.qc.name && editingSignOff.type !== 'qc' && (
                    <button
                      onClick={() => clearSignOff('qc')}
                      className="mt-1 text-xs text-red-400 hover:text-red-300"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
        </div>
      </div>

      {/* Label Template Selection Modal */}
      {showLabelPrintModal && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white">Select Label Template</h3>
              <button
                onClick={() => setShowLabelPrintModal(false)}
                className="text-gray-400 hover:text-white"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            {labelTemplates.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-400 mb-4">No label templates found.</p>
                <p className="text-sm text-gray-500">Create a template in the Label Designer first.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {labelTemplates.map(template => (
                  <div
                    key={template.id}
                    onClick={() => handleSelectTemplate(template)}
                    className="bg-gray-700 border border-gray-600 rounded-lg p-4 cursor-pointer hover:border-yellow-600 transition-colors"
                  >
                    <h4 className="text-lg font-semibold text-white mb-2">{template.template_name}</h4>
                    <div className="text-sm text-gray-400 space-y-1">
                      <p>Size: {template.width_mm} × {template.height_mm} mm</p>
                      <p>Fields: {template.fields?.length || 0}</p>
                      {template.logo && <p className="text-blue-400">✓ Logo included</p>}
                      {template.include_qr_code && <p className="text-blue-400">✓ QR Code included</p>}
                    </div>
                    <button className="mt-3 w-full px-3 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 text-sm">
                      Select Template
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Printer Selection Modal */}
      {showPrinterSelection && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white">Select Printer</h3>
              <button
                onClick={() => setShowPrinterSelection(false)}
                className="text-gray-400 hover:text-white"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="mb-4 bg-gray-700 p-3 rounded">
              <p className="text-white text-sm">
                <strong>Quantity to print:</strong> {calculations.cartonsRequired || 0} labels
              </p>
            </div>

            <div className="space-y-2 mb-6 max-h-96 overflow-y-auto">
              {availablePrinters.map((printer, index) => (
                <div
                  key={index}
                  onClick={() => setSelectedPrinter(printer)}
                  className={`p-4 rounded border-2 cursor-pointer transition-all ${
                    selectedPrinter?.name === printer.name
                      ? 'border-yellow-600 bg-yellow-600/20'
                      : 'border-gray-600 bg-gray-700 hover:border-gray-500'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-white font-medium">{printer.name}</p>
                      {printer.is_default && (
                        <span className="text-xs text-green-400">Default Printer</span>
                      )}
                      {printer.is_browser && (
                        <span className="text-xs text-blue-400 block mt-1">
                          Uses your browser's print dialog
                        </span>
                      )}
                    </div>
                    {selectedPrinter?.name === printer.name && (
                      <div className="text-yellow-400">
                        <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowPrinterSelection(false);
                  setShowLabelPreview(true);
                }}
                className="misty-button misty-button-secondary"
              >
                Back to Preview
              </button>
              <button
                onClick={handleConfirmPrint}
                disabled={!selectedPrinter}
                className="misty-button misty-button-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <PrinterIcon className="h-5 w-5 mr-2" />
                Print {calculations.cartonsRequired || 0} Label(s)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Label Preview Modal */}
      {showLabelPreview && selectedLabelTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white">Label Preview</h3>
              <button
                onClick={() => setShowLabelPreview(false)}
                className="text-gray-400 hover:text-white"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="mb-4 bg-gray-700 p-3 rounded">
              <p className="text-white text-sm">
                <strong>Template:</strong> {selectedLabelTemplate.template_name}
              </p>
              <p className="text-gray-300 text-sm mt-1">
                <strong>Quantity to print:</strong> {calculations.cartonsRequired || 0} labels
              </p>
            </div>

            {/* Label Preview */}
            <div className="bg-white rounded-lg p-6 mb-4">
              <div
                className="relative bg-white border-2 border-gray-400 mx-auto print-label"
                style={{
                  width: `${selectedLabelTemplate.width_mm * 3.779527559}px`,
                  height: `${selectedLabelTemplate.height_mm * 3.779527559}px`,
                  maxWidth: '100%'
                }}
              >
                {/* Render Shapes */}
                {selectedLabelTemplate.shapes?.map((shape) => {
                  // For lines, use solid background instead of border
                  const isLine = shape.shape_type === 'line';
                  
                  return (
                    <div
                      key={shape.id}
                      className="absolute"
                      style={{
                        left: `${shape.x_position * 3.779527559}px`,
                        top: `${shape.y_position * 3.779527559}px`,
                        width: `${shape.width * 3.779527559}px`,
                        height: `${shape.height * 3.779527559}px`,
                        border: isLine ? 'none' : `${shape.border_width}px solid ${shape.border_color}`,
                        backgroundColor: isLine ? shape.border_color : (shape.fill_color || 'transparent'),
                        borderRadius: shape.shape_type === 'circle' ? '50%' : '0'
                      }}
                    />
                  );
                })}

                {/* Render Logo */}
                {selectedLabelTemplate.logo && (
                  <img
                    src={selectedLabelTemplate.logo.image_data}
                    alt="Company Logo"
                    className="absolute"
                    style={{
                      left: `${selectedLabelTemplate.logo.x_position * 3.779527559}px`,
                      top: `${selectedLabelTemplate.logo.y_position * 3.779527559}px`,
                      width: `${selectedLabelTemplate.logo.width * 3.779527559}px`,
                      height: `${selectedLabelTemplate.logo.height * 3.779527559}px`,
                      objectFit: 'contain'
                    }}
                  />
                )}

                {/* Render Fields with Real Data */}
                {selectedLabelTemplate.fields?.map((field) => {
                  const labelData = getLabelData();
                  const fieldValue = labelData[field.field_name] || 'N/A';
                  
                  return (
                    <div
                      key={field.id}
                      className="absolute text-black"
                      style={{
                        left: `${field.x_position * 3.779527559}px`,
                        top: `${field.y_position * 3.779527559}px`,
                        fontSize: `${field.font_size}pt`,
                        fontWeight: field.font_weight,
                        textAlign: field.text_align,
                        maxWidth: field.max_width ? `${field.max_width * 3.779527559}px` : 'none'
                      }}
                    >
                      <div className="text-xs text-gray-600">{field.label}:</div>
                      <div className="font-medium">{fieldValue}</div>
                    </div>
                  );
                })}

                {/* Render QR Code */}
                {selectedLabelTemplate.include_qr_code && (
                  <div
                    className="absolute flex items-center justify-center bg-white p-1"
                    style={{
                      left: `${selectedLabelTemplate.qr_code_x * 3.779527559}px`,
                      top: `${selectedLabelTemplate.qr_code_y * 3.779527559}px`,
                      width: `${selectedLabelTemplate.qr_code_size * 3.779527559}px`,
                      height: `${selectedLabelTemplate.qr_code_size * 3.779527559}px`
                    }}
                  >
                    <QRCodeSVG 
                      value={getLabelData().order_number}
                      size={selectedLabelTemplate.qr_code_size * 3.779527559 - 8}
                      level="M"
                      includeMargin={false}
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowLabelPreview(false);
                  setShowLabelPrintModal(true);
                }}
                className="misty-button misty-button-secondary"
              >
                Choose Different Template
              </button>
              <button
                onClick={handlePrintLabels}
                className="misty-button misty-button-primary flex items-center"
              >
                <PrinterIcon className="h-5 w-5 mr-2" />
                Continue to Print ({calculations.cartonsRequired || 0} labels)
              </button>
            </div>
          </div>
        </div>
      )}
      </>
    );
  } catch (error) {
    console.error('JobCard render error:', error);
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-8">
          <p className="text-white">Error loading job card: {error.message}</p>
          <button onClick={onClose} className="misty-button misty-button-secondary mt-4">Close</button>
        </div>
      </div>
    );
  }
};

export default JobCard;