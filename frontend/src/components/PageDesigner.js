import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { apiHelpers } from '../utils/api';
import {
  PlusIcon,
  TrashIcon,
  PencilIcon,
  EyeIcon,
  DocumentDuplicateIcon,
  PhotoIcon,
  RectangleGroupIcon,
  DocumentTextIcon,
  ArrowsPointingOutIcon
} from '@heroicons/react/24/outline';

const PageDesigner = () => {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showPreview, setShowPreview] = useState(false);
  
  // Canvas reference for drag and drop
  const canvasRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [draggedElement, setDraggedElement] = useState(null);
  const [isResizing, setIsResizing] = useState(false);
  const [selectedElementId, setSelectedElementId] = useState(null); // For properties panel
  
  // Template form state
  const [templateForm, setTemplateForm] = useState({
    template_name: '',
    document_type: 'acknowledgment', // acknowledgment, invoice, packing_slip
    elements: [], // All elements (fields, text, images, shapes)
    page_width: 595, // A4 width in points (210mm)
    page_height: 842 // A4 height in points (297mm)
  });

  // Available document types
  const documentTypes = [
    { value: 'acknowledgment', label: 'Acknowledgment' },
    { value: 'invoice', label: 'Invoice' },
    { value: 'packing_slip', label: 'Packing Slip' }
  ];

  // Available fields per document type
  const availableFields = {
    acknowledgment: [
      { value: 'order_number', label: 'Order Number' },
      { value: 'customer_name', label: 'Customer Name' },
      { value: 'customer_address', label: 'Customer Address' },
      { value: 'order_date', label: 'Order Date' },
      { value: 'due_date', label: 'Due Date' },
      { value: 'items_table', label: 'Items Table' },
      { value: 'total_amount', label: 'Total Amount' },
      { value: 'notes', label: 'Notes' }
    ],
    invoice: [
      { value: 'invoice_number', label: 'Invoice Number' },
      { value: 'customer_name', label: 'Customer Name' },
      { value: 'customer_address', label: 'Customer Address' },
      { value: 'invoice_date', label: 'Invoice Date' },
      { value: 'due_date', label: 'Due Date' },
      { value: 'items_table', label: 'Items Table' },
      { value: 'subtotal', label: 'Subtotal' },
      { value: 'tax', label: 'Tax (GST)' },
      { value: 'total_amount', label: 'Total Amount' },
      { value: 'payment_terms', label: 'Payment Terms' }
    ],
    packing_slip: [
      { value: 'order_number', label: 'Order Number' },
      { value: 'customer_name', label: 'Customer Name' },
      { value: 'shipping_address', label: 'Shipping Address' },
      { value: 'date', label: 'Date' },
      { value: 'items_table', label: 'Items Table' },
      { value: 'total_quantity', label: 'Total Quantity' },
      { value: 'notes', label: 'Notes' }
    ]
  };

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const response = await apiHelpers.getPageTemplates();
      setTemplates(response.data.data || []);
    } catch (error) {
      console.error('Error loading page templates:', error);
      toast.error('Failed to load page templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    setTemplateForm({
      template_name: 'New Page Template',
      document_type: 'acknowledgment',
      elements: [],
      page_width: 595,
      page_height: 842
    });
    setSelectedTemplate(null);
    setIsEditing(true);
  };

  const handleEditTemplate = (template) => {
    setTemplateForm(template);
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
        await apiHelpers.updatePageTemplate(selectedTemplate.id, templateForm);
        toast.success('Template updated successfully');
      } else {
        // Create new template
        await apiHelpers.createPageTemplate(templateForm);
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
      await apiHelpers.deletePageTemplate(templateId);
      toast.success('Template deleted successfully');
      loadTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      toast.error('Failed to delete template');
    }
  };

  const handleAddField = (fieldType) => {
    const timestamp = Date.now();
    const fieldLabel = availableFields[templateForm.document_type]?.find(f => f.value === fieldType)?.label || fieldType;
    
    // Create label element (static text above the field)
    const labelElement = {
      id: `${timestamp}-label`,
      type: 'text',
      content: `${fieldLabel}:`,
      x: 50,
      y: 50,
      width: 200,
      height: 20,
      fontSize: 11,
      fontWeight: 'bold',
      color: '#333333',
      isFieldLabel: true, // Mark this as a field label for identification
      linkedFieldId: `${timestamp}-field` // Link to the field below
    };

    // Create field element (data placeholder below the label)
    const fieldElement = {
      id: `${timestamp}-field`,
      type: 'field',
      field_type: fieldType,
      x: 50,
      y: 72, // Position below label (50 + 20 + 2px gap)
      width: 200,
      height: 30,
      fontSize: 12,
      fontWeight: 'normal',
      color: '#000000',
      linkedLabelId: `${timestamp}-label` // Link to the label above
    };

    setTemplateForm({
      ...templateForm,
      elements: [...templateForm.elements, labelElement, fieldElement]
    });
  };

  const handleAddText = () => {
    const newElement = {
      id: Date.now().toString(),
      type: 'text',
      content: 'Enter text here',
      x: 50,
      y: 50,
      width: 200,
      height: 30,
      fontSize: 12,
      fontWeight: 'normal',
      color: '#000000'
    };

    setTemplateForm({
      ...templateForm,
      elements: [...templateForm.elements, newElement]
    });
  };

  const handleAddShape = (shapeType) => {
    const newElement = {
      id: Date.now().toString(),
      type: 'shape',
      shape_type: shapeType, // rectangle, circle, line
      x: 50,
      y: 50,
      width: 100,
      height: 100,
      borderColor: '#000000',
      borderWidth: 1,
      fillColor: 'transparent'
    };

    setTemplateForm({
      ...templateForm,
      elements: [...templateForm.elements, newElement]
    });
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const reader = new FileReader();
      reader.onloadend = () => {
        const newElement = {
          id: Date.now().toString(),
          type: 'image',
          src: reader.result,
          x: 50,
          y: 50,
          width: 200,
          height: 150,
          maintainAspectRatio: true
        };

        setTemplateForm({
          ...templateForm,
          elements: [...templateForm.elements, newElement]
        });
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('Error uploading image:', error);
      toast.error('Failed to upload image');
    }
  };

  const handleDeleteElement = (elementId) => {
    setTemplateForm({
      ...templateForm,
      elements: templateForm.elements.filter(el => el.id !== elementId)
    });
  };

  const handleElementUpdate = (elementId, updates) => {
    setTemplateForm({
      ...templateForm,
      elements: templateForm.elements.map(el =>
        el.id === elementId ? { ...el, ...updates } : el
      )
    });
  };

  // Drag and drop handlers
  const handleMouseDown = (e, element) => {
    if (e.target.classList.contains('resize-handle')) {
      setIsResizing(true);
    } else {
      setIsDragging(true);
    }
    setDraggedElement(element);
  };

  const handleMouseMove = (e) => {
    if (!draggedElement) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    if (isResizing) {
      // Handle resizing
      const width = Math.max(20, x - draggedElement.x);
      const height = Math.max(20, y - draggedElement.y);
      
      if (draggedElement.maintainAspectRatio && e.shiftKey) {
        const aspectRatio = draggedElement.width / draggedElement.height;
        handleElementUpdate(draggedElement.id, {
          width: width,
          height: width / aspectRatio
        });
      } else {
        handleElementUpdate(draggedElement.id, { width, height });
      }
    } else if (isDragging) {
      // Handle dragging
      handleElementUpdate(draggedElement.id, { x, y });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setIsResizing(false);
    setDraggedElement(null);
  };

  const renderElement = (element) => {
    const style = {
      position: 'absolute',
      left: `${element.x}px`,
      top: `${element.y}px`,
      width: `${element.width}px`,
      height: `${element.height}px`,
      cursor: 'move',
      border: '1px dashed #666'
    };

    switch (element.type) {
      case 'field':
        return (
          <div
            key={element.id}
            style={{
              ...style,
              fontSize: `${element.fontSize}px`,
              fontWeight: element.fontWeight,
              color: element.color,
              padding: '4px',
              backgroundColor: '#f0f0f0'
            }}
            onMouseDown={(e) => handleMouseDown(e, element)}
          >
            {`{${element.field_type}}`}
            <div
              className="resize-handle"
              style={{
                position: 'absolute',
                right: 0,
                bottom: 0,
                width: '10px',
                height: '10px',
                backgroundColor: '#666',
                cursor: 'nwse-resize'
              }}
            />
          </div>
        );

      case 'text':
        return (
          <div
            key={element.id}
            style={{
              ...style,
              fontSize: `${element.fontSize}px`,
              fontWeight: element.fontWeight,
              color: element.color,
              padding: '4px'
            }}
            onMouseDown={(e) => handleMouseDown(e, element)}
          >
            {element.content}
            <div
              className="resize-handle"
              style={{
                position: 'absolute',
                right: 0,
                bottom: 0,
                width: '10px',
                height: '10px',
                backgroundColor: '#666',
                cursor: 'nwse-resize'
              }}
            />
          </div>
        );

      case 'image':
        return (
          <div
            key={element.id}
            style={style}
            onMouseDown={(e) => handleMouseDown(e, element)}
          >
            <img
              src={element.src}
              alt="Template element"
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            />
            <div
              className="resize-handle"
              style={{
                position: 'absolute',
                right: 0,
                bottom: 0,
                width: '10px',
                height: '10px',
                backgroundColor: '#666',
                cursor: 'nwse-resize'
              }}
            />
          </div>
        );

      case 'shape':
        const shapeStyle = {
          ...style,
          border: `${element.borderWidth}px solid ${element.borderColor}`,
          backgroundColor: element.fillColor
        };

        if (element.shape_type === 'circle') {
          shapeStyle.borderRadius = '50%';
        }

        return (
          <div
            key={element.id}
            style={shapeStyle}
            onMouseDown={(e) => handleMouseDown(e, element)}
          >
            <div
              className="resize-handle"
              style={{
                position: 'absolute',
                right: 0,
                bottom: 0,
                width: '10px',
                height: '10px',
                backgroundColor: '#666',
                cursor: 'nwse-resize'
              }}
            />
          </div>
        );

      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400"></div>
      </div>
    );
  }

  if (isEditing) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">
            {selectedTemplate ? 'Edit Template' : 'Create New Template'}
          </h2>
          <div className="flex space-x-3">
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

        {/* Template Settings */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Template Name
            </label>
            <input
              type="text"
              value={templateForm.template_name}
              onChange={(e) => setTemplateForm({ ...templateForm, template_name: e.target.value })}
              className="misty-input"
              placeholder="Enter template name"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Document Type
            </label>
            <select
              value={templateForm.document_type}
              onChange={(e) => setTemplateForm({ ...templateForm, document_type: e.target.value })}
              className="misty-select"
            >
              {documentTypes.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Toolbar */}
        <div className="bg-gray-700 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-medium text-gray-300 mb-3">Add Elements</h3>
          <div className="flex flex-wrap gap-2">
            {/* Add Field Dropdown */}
            <div className="relative inline-block">
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    handleAddField(e.target.value);
                    e.target.value = '';
                  }
                }}
                className="misty-select text-sm"
              >
                <option value="">+ Add Data Field</option>
                {availableFields[templateForm.document_type]?.map(field => (
                  <option key={field.value} value={field.value}>
                    {field.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={handleAddText}
              className="misty-button misty-button-secondary text-sm flex items-center"
            >
              <DocumentTextIcon className="h-4 w-4 mr-1" />
              Add Text
            </button>

            {/* Shape Buttons */}
            <button
              onClick={() => handleAddShape('rectangle')}
              className="misty-button misty-button-secondary text-sm flex items-center"
            >
              <RectangleGroupIcon className="h-4 w-4 mr-1" />
              Rectangle
            </button>

            <button
              onClick={() => handleAddShape('circle')}
              className="misty-button misty-button-secondary text-sm flex items-center"
            >
              <ArrowsPointingOutIcon className="h-4 w-4 mr-1" />
              Circle
            </button>

            <button
              onClick={() => handleAddShape('line')}
              className="misty-button misty-button-secondary text-sm flex items-center"
            >
              ━
              Line
            </button>

            <label className="misty-button misty-button-secondary text-sm flex items-center cursor-pointer">
              <PhotoIcon className="h-4 w-4 mr-1" />
              Upload Image
              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {/* Canvas Area */}
        <div className="bg-white rounded-lg p-8 relative">
          <div
            ref={canvasRef}
            style={{
              width: `${templateForm.page_width}px`,
              height: `${templateForm.page_height}px`,
              position: 'relative',
              border: '1px solid #ccc',
              backgroundColor: '#fff',
              margin: '0 auto'
            }}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            {templateForm.elements.map(element => renderElement(element))}
          </div>
        </div>

        {/* Elements List */}
        <div className="mt-6">
          <h3 className="text-lg font-medium text-white mb-3">Elements</h3>
          <div className="space-y-2">
            {templateForm.elements.map(element => (
              <div
                key={element.id}
                className="bg-gray-700 rounded p-3 flex items-center justify-between"
              >
                <span className="text-gray-300">
                  {element.type === 'field' ? `Field: ${element.field_type}` :
                   element.type === 'text' ? `Text: ${element.content}` :
                   element.type === 'image' ? 'Image' :
                   `Shape: ${element.shape_type}`}
                </span>
                <button
                  onClick={() => handleDeleteElement(element.id)}
                  className="text-red-400 hover:text-red-300"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Templates List View
  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white">Page Design Templates</h2>
        <button
          onClick={handleCreateNew}
          className="misty-button misty-button-primary flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Create New Template
        </button>
      </div>

      {templates.length === 0 ? (
        <div className="text-center py-12">
          <DocumentDuplicateIcon className="h-16 w-16 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg mb-4">No page templates yet</p>
          <button
            onClick={handleCreateNew}
            className="misty-button misty-button-primary"
          >
            Create Your First Template
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map(template => (
            <div
              key={template.id}
              className="bg-gray-700 rounded-lg p-4 hover:bg-gray-650 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-white">{template.template_name}</h3>
                  <p className="text-sm text-gray-400 capitalize">{template.document_type}</p>
                </div>
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={() => handleEditTemplate(template)}
                  className="flex-1 misty-button misty-button-secondary text-sm flex items-center justify-center"
                >
                  <PencilIcon className="h-4 w-4 mr-1" />
                  Edit
                </button>
                <button
                  onClick={() => handleDeleteTemplate(template.id)}
                  className="misty-button misty-button-secondary text-sm text-red-400 hover:text-red-300"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PageDesigner;
