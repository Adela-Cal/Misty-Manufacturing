import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from './Layout';
import ClientForm from './ClientForm';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { 
  PlusIcon, 
  PencilIcon, 
  PhotoIcon, 
  TrashIcon,
  ArchiveBoxIcon,
  CubeIcon,
  ClipboardDocumentListIcon
} from '@heroicons/react/24/outline';

const ClientManagement = () => {
  const navigate = useNavigate();
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadClients();
  }, []);

  const loadClients = async () => {
    try {
      setLoading(true);
      const response = await apiHelpers.getClients();
      setClients(response.data);
    } catch (error) {
      console.error('Failed to load clients:', error);
      toast.error('Failed to load clients');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (client) => {
    setSelectedClient(client);
    setShowModal(true);
  };

  const handleCreate = () => {
    setSelectedClient(null);
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedClient(null);
  };

  const handleSuccess = () => {
    loadClients(); // Reload clients after successful create/update
  };

  const handleDelete = async (client) => {
    if (window.confirm(`Are you sure you want to delete ${client.company_name}?`)) {
      try {
        // Note: You'd need to implement a delete endpoint
        // await apiHelpers.deleteClient(client.id);
        toast.success('Client deleted successfully');
        loadClients();
      } catch (error) {
        console.error('Failed to delete client:', error);
        toast.error('Failed to delete client');
      }
    }
  };

  const filteredClients = clients.filter(client =>
    client.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    client.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (client.abn && client.abn.toLowerCase().includes(searchTerm.toLowerCase()))
  );

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

  return (
    <Layout>
      <div className="p-8" data-testid="client-management">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Client Management</h1>
            <p className="text-gray-400">Manage your customer relationships and information</p>
          </div>
          <button
            onClick={handleCreate}
            className="misty-button misty-button-primary flex items-center"
            data-testid="add-client-button"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Client
          </button>
        </div>

        {/* Search */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="Search clients by name, email, or ABN..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="misty-input w-full max-w-md"
          />
        </div>

        {/* Clients List */}
        {filteredClients.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredClients.map((client) => (
              <div key={client.id} className="misty-card p-6" data-testid={`client-card-${client.id}`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center flex-1">
                    {client.logo_path ? (
                      <img
                        src={client.logo_path}
                        alt={`${client.company_name} logo`}
                        className="h-12 w-12 rounded-lg object-cover mr-3 flex-shrink-0"
                      />
                    ) : (
                      <div className="h-12 w-12 bg-gray-600 rounded-lg flex items-center justify-center mr-3 flex-shrink-0">
                        <PhotoIcon className="h-6 w-6 text-gray-400" />
                      </div>
                    )}
                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-white truncate">{client.company_name}</h3>
                      <p className="text-sm text-gray-400 truncate">{client.abn || 'No ABN'}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-2">
                    <button
                      onClick={() => handleEdit(client)}
                      className="text-gray-400 hover:text-yellow-400 transition-colors p-1"
                      data-testid={`edit-client-${client.id}`}
                      title="Edit client"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    {/* Uncomment when delete functionality is implemented
                    <button
                      onClick={() => handleDelete(client)}
                      className="text-gray-400 hover:text-red-400 transition-colors p-1"
                      title="Delete client"
                    >
                      <TrashIcon className="h-4 w-4" />
                    </button>
                    */}
                  </div>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-start">
                    <span className="text-gray-400 w-16 flex-shrink-0">Address:</span>
                    <span className="text-gray-300">{client.address}, {client.city}, {client.state} {client.postal_code}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="text-gray-400 w-16 flex-shrink-0">Email:</span>
                    <a href={`mailto:${client.email}`} className="text-yellow-400 hover:text-yellow-300 transition-colors truncate">
                      {client.email}
                    </a>
                  </div>
                  <div className="flex items-center">
                    <span className="text-gray-400 w-16 flex-shrink-0">Phone:</span>
                    <a href={`tel:${client.phone}`} className="text-gray-300 hover:text-yellow-400 transition-colors">
                      {client.phone}
                    </a>
                  </div>
                  {client.website && (
                    <div className="flex items-center">
                      <span className="text-gray-400 w-16 flex-shrink-0">Website:</span>
                      <a 
                        href={client.website.startsWith('http') ? client.website : `https://${client.website}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-yellow-400 hover:text-yellow-300 transition-colors truncate"
                      >
                        {client.website.replace(/^https?:\/\//, '')}
                      </a>
                    </div>
                  )}
                  {client.contacts && client.contacts.length > 0 && (
                    <div className="flex items-start">
                      <span className="text-gray-400 w-16 flex-shrink-0">Contact:</span>
                      <div className="flex-1">
                        {client.contacts.slice(0, 2).map((contact, index) => (
                          <div key={index} className="text-gray-300">
                            {contact.name} {contact.position && `(${contact.position})`}
                            {contact.is_primary && <span className="text-yellow-400 text-xs ml-1">Primary</span>}
                          </div>
                        ))}
                        {client.contacts.length > 2 && (
                          <div className="text-gray-400 text-xs">+{client.contacts.length - 2} more</div>
                        )}
                      </div>
                    </div>
                  )}
                  {client.notes && (
                    <div className="flex items-start">
                      <span className="text-gray-400 w-16 flex-shrink-0">Notes:</span>
                      <span className="text-gray-300 text-xs line-clamp-2">{client.notes}</span>
                    </div>
                  )}
                </div>

                {/* Client Actions */}
                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400 font-medium">Client Actions</span>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => navigate(`/clients/${client.id}/archived-jobs`)}
                        className="text-gray-400 hover:text-blue-400 transition-colors p-1"
                        title="View Archived Jobs & Historic Job Cards"
                      >
                        <ArchiveBoxIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => navigate(`/clients/${client.id}/product-catalogue`)}
                        className="text-gray-400 hover:text-green-400 transition-colors p-1"
                        title="View Product Catalogue"
                      >
                        <CubeIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Bank Details Indicator */}
                {client.bank_details && client.bank_details.bank_name && (
                  <div className="mt-3 pt-3 border-t border-gray-700">
                    <div className="flex items-center">
                      <div className="h-2 w-2 bg-green-400 rounded-full mr-2"></div>
                      <span className="text-xs text-gray-400">Bank details on file</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <PhotoIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-300">
              {searchTerm ? 'No clients found' : 'No clients'}
            </h3>
            <p className="mt-1 text-sm text-gray-400">
              {searchTerm 
                ? 'Try adjusting your search criteria.' 
                : 'Get started by creating your first client.'
              }
            </p>
            {!searchTerm && (
              <div className="mt-6">
                <button
                  onClick={handleCreate}
                  className="misty-button misty-button-primary"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Add Client
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Client Form Modal */}
      {showModal && (
        <ClientForm
          client={selectedClient}
          onClose={handleCloseModal}
          onSuccess={handleSuccess}
        />
      )}
    </Layout>
  );
};

export default ClientManagement;