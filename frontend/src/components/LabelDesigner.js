import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { QRCodeSVG } from 'qrcode.react';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import {
  PlusIcon,
  TrashIcon,
  PencilIcon,
  PrinterIcon,
  EyeIcon,
  DocumentDuplicateIcon,
  QrCodeIcon,
  XMarkIcon,
  ArrowsRightLeftIcon,
  HomeIcon
} from '@heroicons/react/24/outline';

const LabelDesigner = ({ embedded = false }) => {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Form state for template editing
  const [templateForm, setTemplateForm] = useState({
    template_name: '',
    width_mm: 100,
    height_mm: 150,
    fields: [],
    shapes: [],
    logo: null,
    include_qr_code: false,
    qr_code_x: 70,
    qr_code_y: 10,
    qr_code_size: 30
  });

  // Dragging state
  const [draggingElement, setDraggingElement] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  // Available fields that can be added to template
  const availableFields = [
    { value: 'customer', label: 'Customer Name' },
    { value: 'order_number', label: 'Order Number' },
    { value: 'due_date', label: 'Due Date' },
    { value: 'product_item', label: 'Product Item' },
    { value: 'product_details', label: 'Product Details' },
    { value: 'product_quantity', label: 'Product Quantity' },
    { value: 'carton_qty', label: 'Carton Qty' }
  ];

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const response = await apiHelpers.getLabelTemplates();
      setTemplates(response.data.data || []);
    } catch (error) {
      console.error('Error loading templates:', error);
      toast.error('Failed to load label templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    setTemplateForm({
      template_name: 'New Template',
      width_mm: 100,
      height_mm: 150,
      fields: [],
      shapes: [],
      logo: null,
      include_qr_code: false,
      qr_code_x: 70,
      qr_code_y: 10,
      qr_code_size: 30
    });
    setSelectedTemplate(null);
    setIsEditing(true);
  };

  const handleEditTemplate = (template) => {
    setTemplateForm({
      template_name: template.template_name,
      width_mm: template.width_mm,
      height_mm: template.height_mm,
      fields: template.fields || [],
      shapes: template.shapes || [],
      logo: template.logo || null,
      include_qr_code: template.include_qr_code || false,
      qr_code_x: template.qr_code_x || 70,
      qr_code_y: template.qr_code_y || 10,
      qr_code_size: template.qr_code_size || 30
    });
    setSelectedTemplate(template);
    setIsEditing(true);
  };

  const handleSaveTemplate = async () => {
    try {
      if (!templateForm.template_name.trim()) {
        toast.error('Please enter a template name');
        return;
      }

      if (selectedTemplate) {
        // Update existing template
        await apiHelpers.updateLabelTemplate(selectedTemplate.id, templateForm);
        toast.success('Template updated successfully');
      } else {
        // Create new template
        await apiHelpers.createLabelTemplate(templateForm);
        toast.success('Template created successfully');
      }

      setIsEditing(false);
      loadTemplates();
    } catch (error) {
      console.error('Error saving template:', error);
      toast.error('Failed to save template');
    }
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      await apiHelpers.deleteLabelTemplate(templateId);
      toast.success('Template deleted successfully');
      loadTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      toast.error('Failed to delete template');
    }
  };

  const handleAddField = () => {
    const newField = {
      id: `field-${Date.now()}`,
      field_name: availableFields[0].value,
      label: availableFields[0].label,
      x_position: 10,
      y_position: 10,
      font_size: 12,
      font_weight: 'normal',
      text_align: 'left',
      max_width: null
    };

    setTemplateForm(prev => ({
      ...prev,
      fields: [...prev.fields, newField]
    }));
  };

  const handleAddShape = (shapeType) => {
    const newShape = {
      id: `shape-${Date.now()}`,
      shape_type: shapeType,
      x_position: 10,
      y_position: 10,
      width: shapeType === 'line' ? 50 : 30,
      height: shapeType === 'line' ? 2 : 30,
      border_width: 1,
      border_color: '#000000',
      fill_color: null
    };

    setTemplateForm(prev => ({
      ...prev,
      shapes: [...prev.shapes, newShape]
    }));
  };

  const handleRemoveShape = (index) => {
    setTemplateForm(prev => ({
      ...prev,
      shapes: prev.shapes.filter((_, i) => i !== index)
    }));
  };

  const handleShapeChange = (index, field, value) => {
    setTemplateForm(prev => ({
      ...prev,
      shapes: prev.shapes.map((s, i) => 
        i === index ? { ...s, [field]: value } : s
      )
    }));
  };

  const handleLogoUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Check file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Only PNG and JPEG formats are supported');
      return;
    }

    // Check file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast.error('Image size must be less than 2MB');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        // Calculate dimensions to fit within label
        const maxWidth = templateForm.width_mm * 0.3; // 30% of label width
        const maxHeight = templateForm.height_mm * 0.3; // 30% of label height
        
        let width = maxWidth;
        let height = (img.height / img.width) * width;
        
        if (height > maxHeight) {
          height = maxHeight;
          width = (img.width / img.height) * height;
        }

        const logo = {
          id: `logo-${Date.now()}`,
          x_position: 5,
          y_position: 5,
          width: width,
          height: height,
          image_data: e.target.result,
          image_format: file.type.split('/')[1]
        };

        setTemplateForm(prev => ({
          ...prev,
          logo: logo
        }));

        toast.success('Logo uploaded successfully');
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveLogo = () => {
    setTemplateForm(prev => ({
      ...prev,
      logo: null
    }));
    toast.success('Logo removed');
  };

  const handleRemoveField = (index) => {
    setTemplateForm(prev => ({
      ...prev,
      fields: prev.fields.filter((_, i) => i !== index)
    }));
  };

  const handleFieldChange = (index, field, value) => {
    setTemplateForm(prev => ({
      ...prev,
      fields: prev.fields.map((f, i) => 
        i === index ? { ...f, [field]: value } : f
      )
    }));
  };

  const handleOrientationChange = (orientation) => {
    if (orientation === 'portrait') {
      // Portrait: height > width (100 x 150)
      setTemplateForm(prev => ({
        ...prev,
        width_mm: 100,
        height_mm: 150
      }));
    } else {
      // Landscape: width > height (150 x 100)
      setTemplateForm(prev => ({
        ...prev,
        width_mm: 150,
        height_mm: 100
      }));
    }
  };

  const getCurrentOrientation = () => {
    return templateForm.height_mm > templateForm.width_mm ? 'portrait' : 'landscape';
  };

  const handlePreview = (template) => {
    // Sample data for preview
    const sampleData = {
      customer: 'Label Makers Pty Ltd',
      order_number: 'ORD-2025-001',
      due_date: '15/01/2025',
      product_item: 'Paper Core 76mm ID x 3mmT',
      product_details: 'Spiral wound, 1000mm length',
      product_quantity: '500 units',
      carton_qty: '10 cartons'
    };

    setPreviewData({ template, data: sampleData });
    setShowPreview(true);
  };

  const handlePrint = async (template, copies = 1) => {
    try {
      // For now, open print dialog
      // In future, this can be connected to actual printer selection
      window.print();
      toast.success(`Printing ${copies} label(s)...`);
    } catch (error) {
      console.error('Error printing:', error);
      toast.error('Failed to print labels');
    }
  };

  // Drag and Drop handlers
  const handleDragStart = (e, elementType, elementId, currentX, currentY) => {
    const rect = e.target.getBoundingClientRect();
    const offsetX = e.clientX - rect.left;
    const offsetY = e.clientY - rect.top;
    
    setDraggingElement({ type: elementType, id: elementId });
    setDragOffset({ x: offsetX, y: offsetY });
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (!draggingElement) return;

    const canvas = e.currentTarget;
    const rect = canvas.getBoundingClientRect();
    
    // Calculate position in mm
    const x = ((e.clientX - rect.left - dragOffset.x) / 3.779527559);
    const y = ((e.clientY - rect.top - dragOffset.y) / 3.779527559);

    // Update position based on element type
    if (draggingElement.type === 'field') {
      setTemplateForm(prev => ({
        ...prev,
        fields: prev.fields.map(f => 
          f.id === draggingElement.id 
            ? { ...f, x_position: Math.max(0, x), y_position: Math.max(0, y) }
            : f
        )
      }));
    } else if (draggingElement.type === 'shape') {
      setTemplateForm(prev => ({
        ...prev,
        shapes: prev.shapes.map(s => 
          s.id === draggingElement.id 
            ? { ...s, x_position: Math.max(0, x), y_position: Math.max(0, y) }
            : s
        )
      }));
    } else if (draggingElement.type === 'logo' && templateForm.logo) {
      setTemplateForm(prev => ({
        ...prev,
        logo: { ...prev.logo, x_position: Math.max(0, x), y_position: Math.max(0, y) }
      }));
    } else if (draggingElement.type === 'qr_code') {
      setTemplateForm(prev => ({
        ...prev,
        qr_code_x: Math.max(0, x),
        qr_code_y: Math.max(0, y)
      }));
    }

    setDraggingElement(null);
  };

  return (
    <div className={embedded ? "" : "p-6"}>
      {!embedded && (
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Label Designer</h1>
            <p className="text-gray-400 mt-1">Create and manage carton label templates</p>
          </div>
          <div className="flex space-x-2">
            {isEditing && (
              <button
                onClick={() => setIsEditing(false)}
                className="misty-button misty-button-secondary flex items-center"
              >
                <XMarkIcon className="h-5 w-5 mr-2" />
                Return to Templates
              </button>
            )}
            {!isEditing && (
              <>
                <button
                  onClick={() => navigate('/')}
                  className="misty-button misty-button-secondary flex items-center"
                >
                  <HomeIcon className="h-5 w-5 mr-2" />
                  Return to Dashboard
                </button>
                <button
                  onClick={handleCreateNew}
                  className="misty-button misty-button-primary flex items-center"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Create New Template
                </button>
              </>
            )}
          </div>
        </div>
      )}
      
      {embedded && !isEditing && (
        <div className="mb-6 flex items-center justify-end">
          <button
            onClick={handleCreateNew}
            className="misty-button misty-button-primary flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Create New Template
          </button>
        </div>
      )}
      
      {embedded && isEditing && (
        <div className="mb-6 flex items-center justify-end">
          <button
            onClick={() => setIsEditing(false)}
            className="misty-button misty-button-secondary flex items-center"
          >
            <XMarkIcon className="h-5 w-5 mr-2" />
            Return to Templates
          </button>
        </div>
      )}

      {/* Template List */}
      {!isEditing && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading ? (
            <div className="col-span-3 text-center py-12">
              <p className="text-gray-400">Loading templates...</p>
            </div>
          ) : templates.length === 0 ? (
            <div className="col-span-3 text-center py-12">
              <p className="text-gray-400">No templates found. Create your first template!</p>
            </div>
          ) : (
            templates.map(template => (
              <div
                key={template.id}
                className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-yellow-600 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white">{template.template_name}</h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleEditTemplate(template)}
                      className="text-blue-400 hover:text-blue-300"
                      title="Edit"
                    >
                      <PencilIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleDeleteTemplate(template.id)}
                      className="text-red-400 hover:text-red-300"
                      title="Delete"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
                
                <div className="text-sm text-gray-400 space-y-1 mb-4">
                  <p>Size: {template.width_mm} × {template.height_mm} mm</p>
                  <p>Fields: {template.fields?.length || 0}</p>
                  {template.include_qr_code && (
                    <p className="text-blue-400 flex items-center">
                      <QrCodeIcon className="h-4 w-4 mr-1" />
                      Includes QR Code
                    </p>
                  )}
                </div>

                <div className="flex space-x-2">
                  <button
                    onClick={() => handlePreview(template)}
                    className="flex-1 px-3 py-2 bg-gray-700 text-white rounded hover:bg-gray-600 text-sm flex items-center justify-center"
                  >
                    <EyeIcon className="h-4 w-4 mr-1" />
                    Preview
                  </button>
                  <button
                    onClick={() => handlePrint(template, 1)}
                    className="flex-1 px-3 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 text-sm flex items-center justify-center"
                  >
                    <PrinterIcon className="h-4 w-4 mr-1" />
                    Print
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Template Editor */}
      {isEditing && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <div className="mb-6 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white">
              {selectedTemplate ? 'Edit Template' : 'Create New Template'}
            </h2>
            <div className="flex space-x-2">
              <button
                onClick={() => setIsEditing(false)}
                className="misty-button misty-button-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveTemplate}
                className="misty-button misty-button-primary"
              >
                Save Template
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column - Form */}
            <div className="space-y-6">
              {/* Template Name */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Template Name
                </label>
                <input
                  type="text"
                  value={templateForm.template_name}
                  onChange={(e) => setTemplateForm(prev => ({ ...prev, template_name: e.target.value }))}
                  className="misty-input w-full"
                  placeholder="Enter template name"
                />
              </div>

              {/* Orientation Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Label Orientation
                </label>
                <div className="flex space-x-4">
                  <button
                    type="button"
                    onClick={() => handleOrientationChange('portrait')}
                    className={`flex-1 px-4 py-3 rounded border-2 transition-all ${
                      getCurrentOrientation() === 'portrait'
                        ? 'border-yellow-600 bg-yellow-600/20 text-white'
                        : 'border-gray-600 bg-gray-700 text-gray-300 hover:border-gray-500'
                    }`}
                  >
                    <div className="flex flex-col items-center">
                      <div className="w-12 h-16 border-2 border-current mb-2 rounded"></div>
                      <span className="text-sm font-medium">Portrait</span>
                      <span className="text-xs text-gray-400">100 × 150 mm</span>
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleOrientationChange('landscape')}
                    className={`flex-1 px-4 py-3 rounded border-2 transition-all ${
                      getCurrentOrientation() === 'landscape'
                        ? 'border-yellow-600 bg-yellow-600/20 text-white'
                        : 'border-gray-600 bg-gray-700 text-gray-300 hover:border-gray-500'
                    }`}
                  >
                    <div className="flex flex-col items-center">
                      <div className="w-16 h-12 border-2 border-current mb-2 rounded"></div>
                      <span className="text-sm font-medium">Landscape</span>
                      <span className="text-xs text-gray-400">150 × 100 mm</span>
                    </div>
                  </button>
                </div>
              </div>

              {/* Dimensions */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Width (mm)
                  </label>
                  <input
                    type="number"
                    value={templateForm.width_mm}
                    onChange={(e) => setTemplateForm(prev => ({ ...prev, width_mm: parseFloat(e.target.value) }))}
                    className="misty-input w-full"
                    min="10"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Height (mm)
                  </label>
                  <input
                    type="number"
                    value={templateForm.height_mm}
                    onChange={(e) => setTemplateForm(prev => ({ ...prev, height_mm: parseFloat(e.target.value) }))}
                    className="misty-input w-full"
                    min="10"
                  />
                </div>
              </div>

              {/* Logo Import */}
              <div className="border border-gray-700 rounded p-4">
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-medium text-gray-300">
                    Company Logo
                  </label>
                  {templateForm.logo && (
                    <button
                      onClick={handleRemoveLogo}
                      className="text-xs px-2 py-1 bg-red-600 text-white rounded hover:bg-red-700"
                    >
                      Remove Logo
                    </button>
                  )}
                </div>
                
                {!templateForm.logo ? (
                  <div>
                    <p className="text-xs text-gray-400 mb-2">
                      <strong>Accepted formats:</strong> PNG, JPEG, JPG<br />
                      <strong>Maximum size:</strong> 2MB<br />
                      <strong>Recommended:</strong> Transparent PNG for best results
                    </p>
                    <label className="block">
                      <input
                        type="file"
                        accept="image/png,image/jpeg,image/jpg"
                        onChange={handleLogoUpload}
                        className="hidden"
                      />
                      <div className="cursor-pointer px-4 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 text-center text-sm">
                        Choose Logo File
                      </div>
                    </label>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="text-xs text-gray-300 bg-gray-700 p-2 rounded">
                      <p>✓ Logo uploaded</p>
                      <p className="text-gray-400 italic mt-1">Drag logo on preview to reposition</p>
                    </div>
                    
                    {/* Logo Size Controls */}
                    <div>
                      <label className="block text-xs font-medium text-gray-300 mb-1">
                        Logo Size (mm)
                      </label>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-xs text-gray-400 mb-1">Width</label>
                          <input
                            type="number"
                            value={templateForm.logo.width.toFixed(1)}
                            onChange={(e) => {
                              const newWidth = parseFloat(e.target.value) || 5;
                              setTemplateForm(prev => ({
                                ...prev,
                                logo: {
                                  id: prev.logo.id,
                                  x_position: prev.logo.x_position,
                                  y_position: prev.logo.y_position,
                                  width: newWidth,
                                  height: prev.logo.height,
                                  image_data: prev.logo.image_data,
                                  image_format: prev.logo.image_format
                                }
                              }));
                            }}
                            className="misty-input w-full text-xs py-1"
                            step="0.5"
                            min="5"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-400 mb-1">Height</label>
                          <input
                            type="number"
                            value={templateForm.logo.height.toFixed(1)}
                            onChange={(e) => {
                              const newHeight = parseFloat(e.target.value) || 5;
                              setTemplateForm(prev => ({
                                ...prev,
                                logo: {
                                  id: prev.logo.id,
                                  x_position: prev.logo.x_position,
                                  y_position: prev.logo.y_position,
                                  width: prev.logo.width,
                                  height: newHeight,
                                  image_data: prev.logo.image_data,
                                  image_format: prev.logo.image_format
                                }
                              }));
                            }}
                            className="misty-input w-full text-xs py-1"
                            step="0.5"
                            min="5"
                          />
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          // Reset to proportional scaling
                          const img = new Image();
                          img.onload = () => {
                            const aspectRatio = img.width / img.height;
                            const maxWidth = templateForm.width_mm * 0.3;
                            let width = maxWidth;
                            let height = width / aspectRatio;
                            
                            setTemplateForm(prev => ({
                              ...prev,
                              logo: {
                                id: prev.logo.id,
                                x_position: prev.logo.x_position,
                                y_position: prev.logo.y_position,
                                width: width,
                                height: height,
                                image_data: prev.logo.image_data,
                                image_format: prev.logo.image_format
                              }
                            }));
                            toast.success('Logo size reset to proportional');
                          };
                          img.src = templateForm.logo.image_data;
                        }}
                        className="mt-2 text-xs px-2 py-1 bg-gray-600 text-white rounded hover:bg-gray-500 w-full"
                      >
                        Reset Proportions
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Shapes */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-medium text-gray-300">
                    Shapes
                  </label>
                  <div className="flex space-x-1">
                    <button
                      onClick={() => handleAddShape('rectangle')}
                      className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                      title="Add Rectangle"
                    >
                      □
                    </button>
                    <button
                      onClick={() => handleAddShape('circle')}
                      className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                      title="Add Circle"
                    >
                      ○
                    </button>
                    <button
                      onClick={() => handleAddShape('line')}
                      className="text-xs px-2 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                      title="Add Line"
                    >
                      ―
                    </button>
                  </div>
                </div>

                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {templateForm.shapes.map((shape, index) => (
                    <div key={shape.id} className="border border-gray-700 rounded p-2">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-white capitalize">{shape.shape_type}</span>
                        <button
                          onClick={() => handleRemoveShape(index)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <TrashIcon className="h-3 w-3" />
                        </button>
                      </div>

                      <div className="grid grid-cols-2 gap-1 text-xs">
                        <div>
                          <label className="block text-xs text-gray-400">Width (mm)</label>
                          <input
                            type="number"
                            value={shape.width}
                            onChange={(e) => handleShapeChange(index, 'width', parseFloat(e.target.value))}
                            className="misty-input w-full text-xs py-1"
                            step="0.5"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-400">Height (mm)</label>
                          <input
                            type="number"
                            value={shape.height}
                            onChange={(e) => handleShapeChange(index, 'height', parseFloat(e.target.value))}
                            className="misty-input w-full text-xs py-1"
                            step="0.5"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-400">Border</label>
                          <input
                            type="number"
                            value={shape.border_width}
                            onChange={(e) => handleShapeChange(index, 'border_width', parseInt(e.target.value))}
                            className="misty-input w-full text-xs py-1"
                            min="0"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-400">Border Color</label>
                          <input
                            type="color"
                            value={shape.border_color}
                            onChange={(e) => handleShapeChange(index, 'border_color', e.target.value)}
                            className="w-full h-7 rounded cursor-pointer"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {templateForm.shapes.length === 0 && (
                    <p className="text-center text-gray-500 py-3 text-xs">
                      No shapes added. Click icons above to add shapes.
                    </p>
                  )}
                </div>
              </div>

              {/* QR Code Settings */}
              <div className="border border-gray-700 rounded p-4">
                <div className="flex items-center mb-3">
                  <input
                    type="checkbox"
                    id="include_qr"
                    checked={templateForm.include_qr_code}
                    onChange={(e) => setTemplateForm(prev => ({ ...prev, include_qr_code: e.target.checked }))}
                    className="w-4 h-4 text-yellow-600 bg-gray-700 border-gray-600 rounded focus:ring-yellow-500"
                  />
                  <label htmlFor="include_qr" className="ml-2 text-sm font-medium text-gray-300">
                    Include QR Code
                  </label>
                </div>

                {templateForm.include_qr_code && (
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">X Position</label>
                      <input
                        type="number"
                        value={templateForm.qr_code_x}
                        onChange={(e) => setTemplateForm(prev => ({ ...prev, qr_code_x: parseFloat(e.target.value) }))}
                        className="misty-input w-full text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Y Position</label>
                      <input
                        type="number"
                        value={templateForm.qr_code_y}
                        onChange={(e) => setTemplateForm(prev => ({ ...prev, qr_code_y: parseFloat(e.target.value) }))}
                        className="misty-input w-full text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Size</label>
                      <input
                        type="number"
                        value={templateForm.qr_code_size}
                        onChange={(e) => setTemplateForm(prev => ({ ...prev, qr_code_size: parseFloat(e.target.value) }))}
                        className="misty-input w-full text-sm"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Fields */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className="block text-sm font-medium text-gray-300">
                    Label Fields
                  </label>
                  <button
                    onClick={handleAddField}
                    className="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center"
                  >
                    <PlusIcon className="h-4 w-4 mr-1" />
                    Add Field
                  </button>
                </div>

                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {templateForm.fields.map((field, index) => (
                    <div key={index} className="border border-gray-700 rounded p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-white">Field {index + 1}</span>
                        <button
                          onClick={() => handleRemoveField(index)}
                          className="text-red-400 hover:text-red-300"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div className="col-span-2">
                          <label className="block text-xs text-gray-400 mb-1">Field Type</label>
                          <select
                            value={field.field_name}
                            onChange={(e) => {
                              const selectedField = availableFields.find(f => f.value === e.target.value);
                              handleFieldChange(index, 'field_name', e.target.value);
                              handleFieldChange(index, 'label', selectedField.label);
                            }}
                            className="misty-select w-full"
                          >
                            {availableFields.map(af => (
                              <option key={af.value} value={af.value}>{af.label}</option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="block text-xs text-gray-400 mb-1">X (mm)</label>
                          <input
                            type="number"
                            value={field.x_position}
                            onChange={(e) => handleFieldChange(index, 'x_position', parseFloat(e.target.value))}
                            className="misty-input w-full"
                            step="0.1"
                          />
                        </div>

                        <div>
                          <label className="block text-xs text-gray-400 mb-1">Y (mm)</label>
                          <input
                            type="number"
                            value={field.y_position}
                            onChange={(e) => handleFieldChange(index, 'y_position', parseFloat(e.target.value))}
                            className="misty-input w-full"
                            step="0.1"
                          />
                        </div>

                        <div>
                          <label className="block text-xs text-gray-400 mb-1">Font Size</label>
                          <input
                            type="number"
                            value={field.font_size}
                            onChange={(e) => handleFieldChange(index, 'font_size', parseInt(e.target.value))}
                            className="misty-input w-full"
                            min="8"
                            max="72"
                          />
                        </div>

                        <div>
                          <label className="block text-xs text-gray-400 mb-1">Weight</label>
                          <select
                            value={field.font_weight}
                            onChange={(e) => handleFieldChange(index, 'font_weight', e.target.value)}
                            className="misty-select w-full"
                          >
                            <option value="normal">Normal</option>
                            <option value="bold">Bold</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  ))}

                  {templateForm.fields.length === 0 && (
                    <p className="text-center text-gray-500 py-4 text-sm">
                      No fields added yet. Click "Add Field" to start designing your label.
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column - Live Preview */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Live Preview
              </label>
              <div className="bg-white rounded-lg p-4 border-2 border-gray-600">
                <div
                  className="relative bg-white border-2 border-dashed border-gray-400 mx-auto overflow-hidden"
                  style={{
                    width: `${templateForm.width_mm * 3.779527559}px`,
                    height: `${templateForm.height_mm * 3.779527559}px`,
                    maxWidth: '100%',
                    aspectRatio: `${templateForm.width_mm} / ${templateForm.height_mm}`
                  }}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                >
                  {/* Render Shapes */}
                  {templateForm.shapes.map((shape) => {
                    // For lines, use solid background instead of border
                    const isLine = shape.shape_type === 'line';
                    
                    return (
                      <div
                        key={shape.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, 'shape', shape.id, shape.x_position, shape.y_position)}
                        className="absolute cursor-move hover:opacity-80"
                        style={{
                          left: `${shape.x_position * 3.779527559}px`,
                          top: `${shape.y_position * 3.779527559}px`,
                          width: `${shape.width * 3.779527559}px`,
                          height: `${shape.height * 3.779527559}px`,
                          border: isLine ? 'none' : `${shape.border_width}px solid ${shape.border_color}`,
                          backgroundColor: isLine ? shape.border_color : (shape.fill_color || 'transparent'),
                          borderRadius: shape.shape_type === 'circle' ? '50%' : '0'
                        }}
                        title="Drag to reposition"
                      />
                    );
                  })}

                  {/* Render Logo */}
                  {templateForm.logo && (
                    <img
                      draggable
                      onDragStart={(e) => handleDragStart(e, 'logo', templateForm.logo.id, templateForm.logo.x_position, templateForm.logo.y_position)}
                      src={templateForm.logo.image_data}
                      alt="Company Logo"
                      className="absolute cursor-move hover:opacity-80"
                      style={{
                        left: `${templateForm.logo.x_position * 3.779527559}px`,
                        top: `${templateForm.logo.y_position * 3.779527559}px`,
                        width: `${templateForm.logo.width * 3.779527559}px`,
                        height: `${templateForm.logo.height * 3.779527559}px`,
                        objectFit: 'contain'
                      }}
                      title="Drag to reposition"
                    />
                  )}

                  {/* Render Fields */}
                  {templateForm.fields.map((field) => (
                    <div
                      key={field.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, 'field', field.id, field.x_position, field.y_position)}
                      className="absolute text-black cursor-move hover:bg-blue-50"
                      style={{
                        left: `${field.x_position * 3.779527559}px`,
                        top: `${field.y_position * 3.779527559}px`,
                        fontSize: `${field.font_size}pt`,
                        fontWeight: field.font_weight,
                        textAlign: field.text_align,
                        maxWidth: field.max_width ? `${field.max_width * 3.779527559}px` : 'none'
                      }}
                      title="Drag to reposition"
                    >
                      <div className="text-xs text-gray-400">{field.label}:</div>
                      <div className="font-medium">Sample Data</div>
                    </div>
                  ))}

                  {/* Render QR Code */}
                  {templateForm.include_qr_code && (
                    <div
                      draggable
                      onDragStart={(e) => handleDragStart(e, 'qr_code', 'qr', templateForm.qr_code_x, templateForm.qr_code_y)}
                      className="absolute bg-white flex items-center justify-center cursor-move hover:opacity-80 p-1"
                      style={{
                        left: `${templateForm.qr_code_x * 3.779527559}px`,
                        top: `${templateForm.qr_code_y * 3.779527559}px`,
                        width: `${templateForm.qr_code_size * 3.779527559}px`,
                        height: `${templateForm.qr_code_size * 3.779527559}px`
                      }}
                      title="Drag to reposition"
                    >
                      <QRCodeSVG 
                        value="SAMPLE-ORDER-123"
                        size={templateForm.qr_code_size * 3.779527559 - 8}
                        level="M"
                        includeMargin={false}
                      />
                    </div>
                  )}

                  {/* Grid Lines for Reference */}
                  <div className="absolute inset-0 pointer-events-none">
                    {[...Array(Math.floor(templateForm.height_mm / 10))].map((_, i) => (
                      <div
                        key={`h-${i}`}
                        className="absolute w-full border-t border-gray-300"
                        style={{ top: `${(i + 1) * 10 * 3.779527559}px` }}
                      />
                    ))}
                    {[...Array(Math.floor(templateForm.width_mm / 10))].map((_, i) => (
                      <div
                        key={`v-${i}`}
                        className="absolute h-full border-l border-gray-300"
                        style={{ left: `${(i + 1) * 10 * 3.779527559}px` }}
                      />
                    ))}
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2 text-center">
                  <strong>Tip:</strong> Drag elements on the canvas to reposition them | Grid lines = 10mm intervals
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal - Will be implemented for printing */}
      {showPreview && previewData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-white">Label Preview</h3>
              <button
                onClick={() => setShowPreview(false)}
                className="text-gray-400 hover:text-white"
              >
                <TrashIcon className="h-6 w-6" />
              </button>
            </div>

            {/* Preview content will be added here */}
            <div className="bg-white p-6 rounded">
              <p className="text-gray-800">Preview with actual data will be shown here</p>
            </div>

            <div className="mt-4 flex justify-end space-x-2">
              <button
                onClick={() => setShowPreview(false)}
                className="misty-button misty-button-secondary"
              >
                Close
              </button>
              <button
                onClick={() => {
                  handlePrint(previewData.template, 1);
                  setShowPreview(false);
                }}
                className="misty-button misty-button-primary"
              >
                <PrinterIcon className="h-5 w-5 mr-2" />
                Print
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LabelDesigner;
