import React, { useState, useEffect } from 'react';
import Layout from './Layout';
import { apiHelpers } from '../utils/api';
import { toast } from 'sonner';
import { PlusIcon, PencilIcon, PhotoIcon } from '@heroicons/react/24/outline';

const ClientManagement = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedClient, setSelectedClient] = useState(null);

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

        {/* Clients List */}
        {clients.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {clients.map((client) => (
              <div key={client.id} className="misty-card p-6" data-testid={`client-card-${client.id}`}>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    {client.logo_path ? (
                      <img
                        src={client.logo_path}
                        alt={`${client.company_name} logo`}
                        className="h-12 w-12 rounded-lg object-cover mr-3"
                      />
                    ) : (
                      <div className="h-12 w-12 bg-gray-600 rounded-lg flex items-center justify-center mr-3">
                        <PhotoIcon className="h-6 w-6 text-gray-400" />
                      </div>
                    )}
                    <div>
                      <h3 className="font-semibold text-white">{client.company_name}</h3>
                      <p className="text-sm text-gray-400">{client.abn || 'No ABN'}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleEdit(client)}
                    className="text-gray-400 hover:text-yellow-400 transition-colors"
                    data-testid={`edit-client-${client.id}`}
                  >
                    <PencilIcon className="h-5 w-5" />
                  </button>
                </div>
                
                <div className="space-y-2 text-sm">
                  <p className="text-gray-300">
                    <span className="text-gray-400">Address:</span> {client.address}, {client.city}
                  </p>
                  <p className="text-gray-300">
                    <span className="text-gray-400">Email:</span> {client.email}
                  </p>
                  <p className="text-gray-300">
                    <span className="text-gray-400">Phone:</span> {client.phone}
                  </p>
                  {client.contacts && client.contacts.length > 0 && (
                    <p className="text-gray-300">
                      <span className="text-gray-400">Contact:</span> {client.contacts[0].name}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <PhotoIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-300">No clients</h3>
            <p className="mt-1 text-sm text-gray-400">Get started by creating a new client.</p>
            <div className="mt-6">
              <button
                onClick={handleCreate}
                className="misty-button misty-button-primary"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Add Client
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal Placeholder */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content max-w-2xl">
            <div className="p-6">
              <h2 className="text-xl font-bold text-white mb-4">
                {selectedClient ? 'Edit Client' : 'Add New Client'}
              </h2>
              <p className="text-gray-400 mb-4">Client form will be implemented here</p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setShowModal(false)}
                  className="misty-button misty-button-secondary"
                >
                  Cancel
                </button>
                <button className="misty-button misty-button-primary">
                  {selectedClient ? 'Update' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  );
};

export default ClientManagement;