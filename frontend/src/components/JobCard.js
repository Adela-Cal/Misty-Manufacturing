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
    name: 'Winding Line', 
    machines: ['Winder X1', 'Winder Y2', 'Winder Z3'],
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

  useEffect(() => {
    if (jobId && stage) {
      loadJobCardData();
    } else {
      console.error('JobCard: Missing required props', { jobId, stage, orderId });
      setLoading(false);
    }
  }, [jobId, stage]);

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
      
      // Create safe mock data with all required properties
      const safeJobId = jobId || 'default-job-id';
      const safeOrderId = orderId || jobId || 'default-order-id';
      
      const mockJob = {
        id: safeJobId,
        run_number: 1,
        status: 'in_progress',
        created_date: new Date().toISOString()
      };

      const mockOrder = {
        id: safeOrderId,
        order_number: `ORD-${safeOrderId}`,
        client: {
          id: 1,
          company_name: 'Sample Client Co.'
        },
        quantity: 1000,
        due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        priority: 'normal',
        product_id: 'sample-product-1',
        other_products: []
      };

      const mockProductSpecs = {
        id: 'sample-product-1',
        product_code: 'PC-100-50',
        product_description: 'Paper Core 100mm ID, 50mm length',
        core_id: '100',
        core_width: '1000', // length in mm
        core_thickness: '3.0',
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
        special_tooling_notes: 'Standard mandrel required',
        packing_instructions: 'Handle with care',
        consumables: []
      };

      setJobData({ ...mockJob, order: mockOrder });
      setProductSpecs(mockProductSpecs);
      
      // Auto-select first available machine for current stage
      const currentMachineConfig = MACHINE_LINES[stage];
      if (currentMachineConfig && currentMachineConfig.machines.length > 0) {
        setSelectedMachine(currentMachineConfig.machines[0]);
      }

      calculateProduction(mockJob, mockOrder, mockProductSpecs);
      
    } catch (error) {
      console.error('Failed to load job card data:', error);
      toast.error('Failed to load job card data');
    } finally {
      setLoading(false);
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

  const getCurrentStageTitle = () => {
    const stageNames = {
      paper_slitting: 'Paper Slitting Job Card',
      winding: 'Winding Job Card', 
      finishing: 'Cutting/Indexing Job Card',
      delivery: 'Packing/Delivery Job Card'
    };
    return stageNames[stage] || 'Job Card';
  };

  const getMachineConfig = () => MACHINE_LINES[stage] || {};

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
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-gray-800 rounded-lg max-w-6xl max-h-[95vh] overflow-y-auto w-full border border-gray-700">
        {/* Header - No Print */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700 no-print">
          <h2 className="text-xl font-bold text-white">{getCurrentStageTitle()}</h2>
          <div className="flex items-center space-x-2">
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
          <div className="text-center mb-6 border-b-2 border-gray-800 pb-4">
            <h1 className="text-2xl font-bold text-gray-900">{getCurrentStageTitle()}</h1>
            <p className="text-gray-600">Generated: {new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}</p>
          </div>

          {/* Order Information */}
          <div className="grid grid-cols-2 gap-6 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                <DocumentTextIcon className="h-5 w-5 mr-2" />
                Order Information
              </h3>
              <div className="space-y-2 text-sm">
                <div><strong>Order ID:</strong> {order?.order_number || `ORD-${orderId || jobId}` || 'N/A'}</div>
                <div><strong>Customer:</strong> {order?.client?.company_name || 'Sample Client Co.'}</div>
                <div><strong>Quantity:</strong> {(order?.quantity || 1000)?.toLocaleString()} units</div>
                <div><strong>Due Date:</strong> {order?.due_date ? new Date(order.due_date).toLocaleDateString() : new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toLocaleDateString()}</div>
                <div><strong>Priority:</strong> 
                  <span className={`ml-2 px-2 py-1 rounded text-xs ${order?.priority === 'urgent' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                    {order?.priority || 'Normal'}
                  </span>
                </div>
                <div><strong>Run Number:</strong> {jobData?.run_number || '1'}</div>
              </div>
            </div>

            {/* Machine Line Selection */}
            <div className="bg-purple-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                <CogIcon className="h-5 w-5 mr-2" />
                Machine Line: {machineConfig.name}
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Selected Machine:</label>
                  <select 
                    value={selectedMachine}
                    onChange={(e) => setSelectedMachine(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  >
                    {machineConfig.machines?.map(machine => (
                      <option key={machine} value={machine}>{machine}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Setup Notes:</label>
                  <textarea
                    value={setupNotes}
                    onChange={(e) => setSetupNotes(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-md h-16 resize-none"
                    placeholder="Special tooling, mandrel requirements..."
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Product Specifications */}
          {productSpecs && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 border-b border-gray-300 pb-2">
                Product Specifications
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm text-gray-600">Product Code</div>
                  <div className="font-medium">{productSpecs.product_code}</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm text-gray-600">Core ID (mm)</div>
                  <div className="font-medium">{productSpecs.core_id || 'N/A'}</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm text-gray-600">Tube Length (mm)</div>
                  <div className="font-medium">{productSpecs.core_width || 'N/A'}</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm text-gray-600">Wall Thickness (mm)</div>
                  <div className="font-medium">{productSpecs.core_thickness || 'N/A'}</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm text-gray-600">Special Tooling</div>
                  <div className="font-medium text-xs">{productSpecs.special_tooling_notes || 'None'}</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm text-gray-600">Packing Notes</div>
                  <div className="font-medium text-xs">{productSpecs.packing_instructions || 'Standard'}</div>
                </div>
              </div>
            </div>
          )}

          {/* Production Calculations */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 border-b border-gray-300 pb-2 flex items-center">
              <CalculatorIcon className="h-5 w-5 mr-2" />
              Production Calculations
            </h3>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-gray-800 mb-2">Material Requirements (metres)</h4>
                <table className="w-full text-sm border border-gray-300">
                  <tbody>
                    <tr className="border-b">
                      <td className="p-2 bg-gray-50">Good Material Length</td>
                      <td className="p-2 text-right font-medium">{calculations.goodMaterialLength?.toLocaleString()}</td>
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 bg-gray-50">Makeready Allowance ({calculations.makereadyPercentage}%)</td>
                      <td className="p-2 text-right font-medium">{calculations.makereadyLength?.toLocaleString()}</td>
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 bg-gray-50">Waste Allowance ({calculations.wastePercentage}%)</td>
                      <td className="p-2 text-right font-medium">{calculations.wasteLength?.toLocaleString()}</td>
                    </tr>
                    <tr className="bg-yellow-100 font-bold">
                      <td className="p-2">TOTAL LENGTH REQUIRED</td>
                      <td className="p-2 text-right">{calculations.totalLengthRequired?.toLocaleString()}</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div>
                <h4 className="font-semibold text-gray-800 mb-2">Production Times (minutes)</h4>
                <table className="w-full text-sm border border-gray-300">
                  <tbody>
                    <tr className="border-b">
                      <td className="p-2 bg-gray-50">Setup Time</td>
                      <td className="p-2 text-right font-medium">{calculations.setupTime}</td>
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 bg-gray-50">Run Time</td>
                      <td className="p-2 text-right font-medium">{calculations.runTime}</td>
                    </tr>
                    <tr className="bg-green-100 font-bold">
                      <td className="p-2">TOTAL PRODUCTION TIME</td>
                      <td className="p-2 text-right">{calculations.totalProductionTime}</td>
                    </tr>
                    <tr>
                      <td className="p-2 text-gray-600 text-xs" colSpan="2">
                        Estimated finish: {new Date(Date.now() + calculations.totalProductionTime * 60000).toLocaleTimeString()}
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
              <h3 className="text-lg font-semibold text-gray-900 mb-3 border-b border-gray-300 pb-2 flex items-center">
                <ShieldCheckIcon className="h-5 w-5 mr-2" />
                Quality Control & Safety
              </h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">QC Tolerances</h4>
                  <table className="w-full text-sm border border-gray-300">
                    <tbody>
                      <tr className="border-b">
                        <td className="p-2 bg-gray-50">ID Tolerance</td>
                        <td className="p-2 text-right">±{productSpecs.qc_tolerances.id_tolerance} mm</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2 bg-gray-50">OD Tolerance</td>
                        <td className="p-2 text-right">±{productSpecs.qc_tolerances.od_tolerance} mm</td>
                      </tr>
                      <tr className="border-b">
                        <td className="p-2 bg-gray-50">Wall Tolerance</td>
                        <td className="p-2 text-right">±{productSpecs.qc_tolerances.wall_tolerance} mm</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">Inspection Schedule</h4>
                  <div className="bg-yellow-50 p-3 rounded border">
                    <div className="text-sm">
                      <div><strong>Check Interval:</strong> Every {productSpecs.inspection_interval_minutes} minutes</div>
                      <div className="mt-2"><strong>Next Check Due:</strong> {new Date(Date.now() + productSpecs.inspection_interval_minutes * 60000).toLocaleTimeString()}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Packing & Delivery */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 border-b border-gray-300 pb-2 flex items-center">
              <TruckIcon className="h-5 w-5 mr-2" />
              Packing & Delivery
            </h3>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-gray-800 mb-2">Packing Requirements</h4>
                <table className="w-full text-sm border border-gray-300">
                  <tbody>
                    <tr className="border-b">
                      <td className="p-2 bg-gray-50">Tubes per Carton</td>
                      <td className="p-2 text-right font-medium">{calculations.tubesPerCarton}</td>
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 bg-gray-50">Cartons Required</td>
                      <td className="p-2 text-right font-medium">{calculations.cartonsRequired}</td>
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 bg-gray-50">Cartons per Pallet</td>
                      <td className="p-2 text-right font-medium">{calculations.cartonsPerPallet}</td>
                    </tr>
                    <tr className="bg-blue-100 font-bold">
                      <td className="p-2">PALLETS REQUIRED</td>
                      <td className="p-2 text-right">{calculations.palletsRequired}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 mb-2">Consumables Usage</h4>
                <table className="w-full text-sm border border-gray-300">
                  <tbody>
                    <tr className="border-b">
                      <td className="p-2 bg-gray-50">Cartons Required</td>
                      <td className="p-2 text-right font-medium">{calculations.cartonsRequired}</td>
                    </tr>
                    <tr className="border-b">
                      <td className="p-2 bg-gray-50">Tape Rolls Required</td>
                      <td className="p-2 text-right font-medium">{calculations.tapeRollsRequired}</td>
                    </tr>
                    {productSpecs?.consumables && productSpecs.consumables.length > 0 && (
                      productSpecs.consumables.map((consumable, index) => (
                        <tr key={index} className="border-b">
                          <td className="p-2 bg-gray-50">{consumable.specification_name}</td>
                          <td className="p-2 text-right font-medium">{consumable.measurement_unit}</td>
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
              <h3 className="text-lg font-semibold text-gray-900 mb-3 border-b border-gray-300 pb-2">
                Other Products in this Order
              </h3>
              <div className="bg-gray-50 p-3 rounded">
                <ul className="text-sm space-y-1">
                  {order?.other_products?.map((product, index) => (
                    <li key={index} className="flex justify-between">
                      <span>{product.code} - {product.description}</span>
                      <span>Qty: {product.quantity}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {/* Operator Sign-off */}
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

      {/* Print Styles */}
      <style jsx>{`
        @media print {
          .no-print { display: none !important; }
          .print-content { 
            font-size: 12px !important;
            margin: 0 !important;
            padding: 20px !important;
          }
          body { print-color-adjust: exact; }
          .bg-blue-50, .bg-purple-50, .bg-gray-50, .bg-yellow-50, .bg-yellow-100, .bg-green-100, .bg-blue-100 { 
            background-color: #f8f9fa !important; 
          }
        }
      `}</style>
      </div>
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