import React, { useState, useEffect } from 'react';
import { apiHelpers } from '../utils/api';
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

const JobCard = ({ jobId, stage, orderId, onClose }) => {
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

  // Master Core Lengths states (for core winding jobs)
  const [masterCores, setMasterCores] = useState([]);
  const [isEditingMasterCore, setIsEditingMasterCore] = useState(false);
  const [newMasterCore, setNewMasterCore] = useState({ length: '', quantity: '', addToStock: false });
  
  // Machine-specific additional production states
  const [additionalProduction, setAdditionalProduction] = useState({
    slittingWidths: [], // For slitting machine: additional widths and meters
    extraMaterial: 0    // General excess material
  });
  const [isEditingAdditionalProduction, setIsEditingAdditionalProduction] = useState(false);
  const [newSlittingWidth, setNewSlittingWidth] = useState({ width: '', meters: '' });

  useEffect(() => {
    if (jobId && stage && orderId) {
      loadJobCardData();
      loadJobTiming();
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
          masterCores
        };
        localStorage.setItem(timingKey, JSON.stringify(timingData));
      }, 500); // Debounce by 500ms
      
      return () => clearTimeout(timeoutId);
    }
  }, [isJobRunning, jobStartTime, actualRunTime, selectedMachine, setupNotes, signOffs, finishedQuantity, additionalProduction, jobId, stage]);

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
              special_tooling_notes: specificationData?.manufacturing_notes || 'Standard processing',
              packing_instructions: 'Handle with care',
              consumables: []
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
          if (timingData.masterCores) setMasterCores(timingData.masterCores);
        } catch (error) {
          console.error('Error loading job timing data:', error);
        }
      }
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

  const handleStartJob = () => {
    const startTime = new Date();
    setJobStartTime(startTime);
    setIsJobRunning(true);
    toast.success(`Job started at ${startTime.toLocaleTimeString()}`);
  };

  const handleCompleteRun = () => {
    if (jobStartTime) {
      const endTime = new Date();
      const durationMs = endTime.getTime() - new Date(jobStartTime).getTime();
      const durationMinutes = Math.round(durationMs / (1000 * 60));
      
      setActualRunTime(durationMinutes);
      setIsJobRunning(false);
      toast.success(`Job completed! Actual run time: ${Math.floor(durationMinutes / 60)}h ${durationMinutes % 60}m`);
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
    if (newSlittingWidth.width && newSlittingWidth.meters) {
      setAdditionalProduction(prev => ({
        ...prev,
        slittingWidths: [...prev.slittingWidths, { 
          width: parseFloat(newSlittingWidth.width),
          meters: parseFloat(newSlittingWidth.meters),
          id: Date.now() // Simple ID for removal
        }]
      }));
      setNewSlittingWidth({ width: '', meters: '' });
    }
  };

  const handleRemoveSlittingWidth = (id) => {
    setAdditionalProduction(prev => ({
      ...prev,
      slittingWidths: prev.slittingWidths.filter(width => width.id !== id)
    }));
  };

  // Master Core management functions
  const handleAddMasterCore = () => {
    if (newMasterCore.length && newMasterCore.quantity) {
      const coreEntry = {
        id: Date.now(),
        length: parseFloat(newMasterCore.length),
        quantity: parseInt(newMasterCore.quantity),
        addToStock: newMasterCore.addToStock,
        addedToStock: false // Track if already added to stock
      };
      
      setMasterCores(prev => [...prev, coreEntry]);
      setNewMasterCore({ length: '', quantity: '', addToStock: false });
      
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
        product_description: `${productSpecs.product_code} - Master Cores (${coreEntry.length}m length)`,
        quantity_on_hand: excessCores,
        unit_of_measure: 'cores',
        source_order_id: jobData.order.id,
        source_job_id: jobId,
        is_shared_product: false,
        shared_with_clients: [],
        created_from_excess: true,
        material_specifications: {
          core_length: coreEntry.length,
          core_diameter: productSpecs.core_diameter,
          material_layers: productSpecs.material_layers
        },
        minimum_stock_level: 0
      };

      // Add to stock via API
      const response = await apiHelpers.post('/stock/raw-substrates', stockData);
      
      if (response.success) {
        toast.success(`${excessCores} excess cores added to Raw Substrates stock`);
        return true;
      } else {
        throw new Error(response.message || 'Failed to add to stock');
      }
    } catch (error) {
      console.error('Failed to add cores to stock:', error);
      toast.error('Failed to add cores to stock');
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
        return 'Master Core Lengths';
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

    // Get core specifications
    const coreLength = parseFloat(productSpecs.core_width) / 1000 || 1.2; // Convert mm to meters, default 1.2m
    const orderQuantity = jobData?.order?.quantity || 1;
    
    // Get winding angle from core winding specification
    let windingAngle = 65; // Default angle in degrees
    if (coreWindingSpec && coreWindingSpec.recommendedAngle) {
      const angleMatch = coreWindingSpec.recommendedAngle.match(/(\d+)/);
      if (angleMatch) {
        windingAngle = parseInt(angleMatch[1]);
      }
    }

    // Calculate length factor: 1/cos(angle in radians)
    const angleInRadians = (windingAngle * Math.PI) / 180;
    const lengthFactor = 1 / Math.cos(angleInRadians);

    const materialRequirements = productSpecs.material_layers.map((layer, index) => {
      // Calculate laps per layer (using quantity as laps, default to 1)
      const lapsPerCore = layer.quantity || 1;
      
      // Material length per core = (core length × length factor) × laps
      const metersPerCore = (coreLength * lengthFactor) * lapsPerCore;
      
      // Total material needed for entire order
      const totalMeters = metersPerCore * orderQuantity;

      return {
        ...layer,
        metersPerCore: metersPerCore,
        totalMeters: totalMeters,
        lapsPerCore: lapsPerCore,
        lengthFactor: lengthFactor.toFixed(3)
      };
    });

    return materialRequirements;
  };

  // Get core winding specification for calculations
  const getCoreWindingSpecForCalculation = () => {
    if (!productSpecs?.core_winding_spec_id) return null;
    
    // This should match the core winding specs from Machinery Specifications
    const coreWindingSpecs = [
      { id: 'cw_15_20', recommendedAngle: '72°', lengthFactor: '3.236' },
      { id: 'cw_21_30', recommendedAngle: '70°', lengthFactor: '2.924' },
      { id: 'cw_31_50', recommendedAngle: '68°', lengthFactor: '2.670' },
      { id: 'cw_51_70', recommendedAngle: '66°', lengthFactor: '2.459' },
      { id: 'cw_71_120', recommendedAngle: '65°', lengthFactor: '2.366' },
      { id: 'cw_121_200', recommendedAngle: '64°', lengthFactor: '2.281' },
      { id: 'cw_201_plus', recommendedAngle: '62°', lengthFactor: '2.130' }
    ];
    
    return coreWindingSpecs.find(spec => spec.id === productSpecs.core_winding_spec_id);
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
        <div className="bg-gray-800 rounded-lg max-w-6xl max-h-[95vh] overflow-y-auto w-full border border-gray-700">
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
          <div className="grid grid-cols-2 gap-6 mb-6">
            <div className="bg-gray-700 p-4 rounded-lg border border-gray-600">
              <h3 className="text-lg font-semibold text-white mb-3 flex items-center">
                <DocumentTextIcon className="h-5 w-5 mr-2" />
                Order Information
              </h3>
              <div className="space-y-2 text-sm">
                <div className="text-gray-300"><strong className="text-white">Order ID:</strong> {jobData?.order?.order_number || `ORD-${orderId || jobId}` || 'N/A'}</div>
                <div className="text-gray-300"><strong className="text-white">Customer:</strong> {jobData?.order?.client_name || 'Unknown Client'}</div>
                <div className="text-gray-300"><strong className="text-white">Quantity:</strong> {(jobData?.order?.quantity || 1000)?.toLocaleString()} units</div>
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
                          Formula: Core Length {(parseFloat(productSpecs.core_width) / 1000 || 1.2).toFixed(2)}m × Angle Factor {materialRequirements[0]?.lengthFactor || '2.366'} × Laps × {jobData?.order?.quantity || 1} cores
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

          {/* Production Calculations */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-3 border-b border-gray-600 pb-2 flex items-center">
              <CalculatorIcon className="h-5 w-5 mr-2" />
              Production Calculations
            </h3>
            <div className="grid grid-cols-2 gap-6">
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
                      <div className="mb-3">
                        <span className="text-white font-medium block mb-2">Master Core Entries:</span>
                        
                        {/* Add new core entry form */}
                        <div className="bg-green-700 p-3 rounded mb-3">
                          <div className="grid grid-cols-4 gap-2 items-end">
                            <div>
                              <label className="text-xs text-green-100 block mb-1">Length (m)</label>
                              <input
                                type="number"
                                step="0.1"
                                placeholder="1.2"
                                value={newMasterCore.length}
                                onChange={(e) => setNewMasterCore(prev => ({ ...prev, length: e.target.value }))}
                                className="w-full px-2 py-1 text-sm bg-gray-600 border border-gray-500 rounded text-white"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-green-100 block mb-1">Quantity</label>
                              <input
                                type="number"
                                placeholder="100"
                                value={newMasterCore.quantity}
                                onChange={(e) => setNewMasterCore(prev => ({ ...prev, quantity: e.target.value }))}
                                className="w-full px-2 py-1 text-sm bg-gray-600 border border-gray-500 rounded text-white"
                              />
                            </div>
                            <div>
                              <label className="text-xs text-green-100 block mb-1">Add Excess to Stock</label>
                              <div className="flex items-center h-7">
                                <input
                                  type="checkbox"
                                  checked={newMasterCore.addToStock}
                                  onChange={(e) => setNewMasterCore(prev => ({ ...prev, addToStock: e.target.checked }))}
                                  className="w-4 h-4 text-green-500 bg-gray-600 border-gray-500 rounded focus:ring-green-500"
                                />
                              </div>
                            </div>
                            <div>
                              <button
                                onClick={handleAddMasterCore}
                                disabled={!newMasterCore.length || !newMasterCore.quantity}
                                className="w-full px-3 py-1 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700 disabled:opacity-50"
                              >
                                + Add
                              </button>
                            </div>
                          </div>
                        </div>
                        
                        {/* Display master core entries */}
                        {masterCores.length > 0 && (
                          <div className="space-y-2">
                            <div className="text-xs text-green-100 grid grid-cols-6 gap-2 font-semibold border-b border-green-500 pb-1">
                              <span>Length (m)</span>
                              <span>Quantity</span>
                              <span>Total Meters</span>
                              <span>Excess Cores</span>
                              <span>Add to Stock</span>
                              <span>Actions</span>
                            </div>
                            {masterCores.map((core) => {
                              const totalMeters = (core.length * core.quantity).toFixed(1);
                              const requiredQuantity = jobData?.order?.quantity || 0;
                              const excessCores = Math.max(0, core.quantity - requiredQuantity);
                              
                              return (
                                <div key={core.id} className="text-sm text-white grid grid-cols-6 gap-2 items-center bg-green-700 p-2 rounded">
                                  <span>{core.length}m</span>
                                  <span>{core.quantity}</span>
                                  <span className="text-yellow-200">{totalMeters}m</span>
                                  <span className={excessCores > 0 ? 'text-yellow-300 font-medium' : 'text-gray-300'}>
                                    {excessCores > 0 ? `+${excessCores}` : '0'}
                                  </span>
                                  <div className="flex items-center">
                                    <input
                                      type="checkbox"
                                      checked={core.addToStock}
                                      onChange={() => handleToggleAddToStock(core.id)}
                                      disabled={excessCores <= 0}
                                      className="w-4 h-4 text-yellow-500 bg-gray-600 border-gray-500 rounded focus:ring-yellow-500 disabled:opacity-50"
                                    />
                                    {core.addedToStock && <span className="ml-1 text-xs text-yellow-300">✓</span>}
                                  </div>
                                  <button
                                    onClick={() => handleRemoveMasterCore(core.id)}
                                    className="text-red-300 hover:text-red-200 text-xs"
                                  >
                                    Remove
                                  </button>
                                </div>
                              );
                            })}
                          </div>
                        )}
                        
                        {masterCores.length === 0 && (
                          <div className="text-center text-green-200 text-sm py-2">
                            No master cores entered yet
                          </div>
                        )}
                      </div>
                      
                      {/* Summary */}
                      {masterCores.length > 0 && jobData?.order?.quantity && (
                        <div className="mt-3 pt-3 border-t border-green-500">
                          <div className="grid grid-cols-3 gap-4 text-sm">
                            <div className="text-green-100">
                              <span className="block">Total Cores:</span>
                              <span className="font-bold text-white">{masterCores.reduce((sum, core) => sum + core.quantity, 0)}</span>
                            </div>
                            <div className="text-green-100">
                              <span className="block">Required:</span>
                              <span className="font-bold text-white">{jobData.order.quantity.toLocaleString()}</span>
                            </div>
                            <div className="text-green-100">
                              <span className="block">Total Excess:</span>
                              <span className="font-bold text-yellow-300">
                                {masterCores.reduce((sum, core) => {
                                  const excess = Math.max(0, core.quantity - (jobData.order.quantity || 0));
                                  return sum + excess;
                                }, 0)}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
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
                        <div className="text-sm text-green-200 font-medium mb-2">Additional Widths Produced:</div>
                        
                        {/* Add new width form */}
                        <div className="flex items-center space-x-2 mb-3">
                          <input
                            type="number"
                            placeholder="Width (mm)"
                            value={newSlittingWidth.width}
                            onChange={(e) => setNewSlittingWidth(prev => ({ ...prev, width: e.target.value }))}
                            className="w-24 px-2 py-1 text-xs bg-gray-600 border border-gray-500 rounded text-white"
                          />
                          <input
                            type="number"
                            placeholder="Meters"
                            value={newSlittingWidth.meters}
                            onChange={(e) => setNewSlittingWidth(prev => ({ ...prev, meters: e.target.value }))}
                            className="w-20 px-2 py-1 text-xs bg-gray-600 border border-gray-500 rounded text-white"
                          />
                          <button
                            onClick={handleAddSlittingWidth}
                            className="px-3 py-1 bg-green-700 text-white text-xs rounded hover:bg-green-800"
                            disabled={!newSlittingWidth.width || !newSlittingWidth.meters}
                          >
                            + Add
                          </button>
                        </div>
                        
                        {/* Display added widths */}
                        {additionalProduction.slittingWidths.length > 0 && (
                          <div className="space-y-1 max-h-32 overflow-y-auto">
                            {additionalProduction.slittingWidths.map((width) => (
                              <div key={width.id} className="flex items-center justify-between bg-gray-800 px-2 py-1 rounded text-xs">
                                <span className="text-green-200">
                                  {width.width}mm × {width.meters}m
                                </span>
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
                        )}
                        
                        {additionalProduction.slittingWidths.length === 0 && (
                          <div className="text-xs text-green-300 italic">
                            No additional widths recorded yet
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>

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

          {/* Quality Control & Safety */}
          {productSpecs?.qc_tolerances && (
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
                {/* Inspection Schedule removed as requested - was causing screen glitching due to Date.now() re-renders */}
              </div>
            </div>
          )}

          {/* Packing & Delivery */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-3 border-b border-gray-600 pb-2 flex items-center">
              <TruckIcon className="h-5 w-5 mr-2" />
              Packing & Delivery
            </h3>
            <div className="grid grid-cols-2 gap-6">
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

          {/* Operator Sign-off */}
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
                    {signOffs.setup.name && (
                      <div className="text-sm text-white font-medium">
                        {signOffs.setup.name}
                        {signOffs.setup.date && (
                          <div className="text-xs text-gray-300">{signOffs.setup.date}</div>
                        )}
                      </div>
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
                    {signOffs.production.name && (
                      <div className="text-sm text-white font-medium">
                        {signOffs.production.name}
                        {signOffs.production.date && (
                          <div className="text-xs text-gray-300">{signOffs.production.date}</div>
                        )}
                      </div>
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
                    {signOffs.qc.name && (
                      <div className="text-sm text-white font-medium">
                        {signOffs.qc.name}
                        {signOffs.qc.date && (
                          <div className="text-xs text-gray-300">{signOffs.qc.date}</div>
                        )}
                      </div>
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
        </div>
      </div>

      {/* Print Styles */}
      <style jsx>{`
        @media print {
          .no-print { display: none !important; }
          .print-content { 
            font-size: 12px !important;
            margin: 0 !important;
            padding: 20px !important;
            background: white !important;
            color: black !important;
          }
          .print-content * {
            background: white !important;
            color: black !important;
            border-color: #333 !important;
          }
          .print-content h1, .print-content h2, .print-content h3, .print-content h4 {
            color: black !important;
          }
          .print-content table {
            border: 1px solid #333 !important;
          }
          .print-content td, .print-content th {
            border: 1px solid #333 !important;
            background: white !important;
            color: black !important;
          }
          .print-content .bg-yellow-600 {
            background: #fef3c7 !important;
            color: black !important;
          }
          .print-content .bg-green-600 {
            background: #dcfce7 !important;
            color: black !important;
          }
          .print-content .bg-blue-600 {
            background: #dbeafe !important;
            color: black !important;
          }
          body { print-color-adjust: exact; }
        }
      `}</style>
      </div>
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