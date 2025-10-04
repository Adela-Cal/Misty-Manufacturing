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
    loadJobCardData();
  }, [jobId, stage]);

  const loadJobCardData = async () => {
    try {
      setLoading(true);
      
      // Load job/order data
      const [jobResponse, orderResponse] = await Promise.all([
        apiHelpers.getJob(jobId),
        apiHelpers.getOrder(orderId)
      ]);

      const job = jobResponse.data;
      const order = orderResponse.data;
      
      // Load client product specifications
      if (order.client_id && order.product_id) {
        const productResponse = await apiHelpers.getClientProduct(order.client_id, order.product_id);
        setProductSpecs(productResponse.data);
      }

      setJobData({ ...job, order });
      
      // Auto-select first available machine for current stage
      const currentMachineConfig = MACHINE_LINES[stage];
      if (currentMachineConfig && currentMachineConfig.machines.length > 0) {
        setSelectedMachine(currentMachineConfig.machines[0]);
      }

      calculateProduction(job, order, productResponse?.data);
      
    } catch (error) {
      console.error('Failed to load job card data:', error);
      toast.error('Failed to load job card data');
    } finally {
      setLoading(false);
    }
  };

  const calculateProduction = (job, order, product) => {
    if (!product || !order) return;

    const orderQty = order.quantity || 0;
    const tubeLength = product.core_width ? parseFloat(product.core_width) : 1000; // mm -> meters
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

  if (!jobData) {
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-6xl max-h-[95vh] overflow-y-auto w-full">
        {/* Header - No Print */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 no-print">
          <h2 className="text-xl font-bold text-gray-900">{getCurrentStageTitle()}</h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={handlePrint}
              className="flex items-center px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              <PrinterIcon className="h-4 w-4 mr-2" />
              Print
            </button>
            <button
              onClick={onClose}
              className="flex items-center px-3 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
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
                <div><strong>Order ID:</strong> {order.order_number || orderId}</div>
                <div><strong>Customer:</strong> {order.client?.company_name || 'N/A'}</div>
                <div><strong>Quantity:</strong> {order.quantity?.toLocaleString()} units</div>
                <div><strong>Due Date:</strong> {order.due_date ? new Date(order.due_date).toLocaleDateString() : 'N/A'}</div>
                <div><strong>Priority:</strong> 
                  <span className={`ml-2 px-2 py-1 rounded text-xs ${order.priority === 'urgent' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'}`}>
                    {order.priority || 'Normal'}
                  </span>
                </div>
                <div><strong>Run Number:</strong> {jobData.run_number || '1'}</div>
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
          {order.other_products && order.other_products.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3 border-b border-gray-300 pb-2">
                Other Products in this Order
              </h3>
              <div className="bg-gray-50 p-3 rounded">
                <ul className="text-sm space-y-1">
                  {order.other_products.map((product, index) => (
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
};

export default JobCard;