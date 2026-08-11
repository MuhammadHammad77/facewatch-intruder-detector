import React, { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Face {
  id: string;
  name: string;
  photo_url: string;
  created_at: string;
}

export default function Faces() {
  const [name, setName] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { data: faces = [], isLoading } = useQuery<Face[]>({
    queryKey: ['faces'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/api/faces`);
      return res.data;
    }
  });

  const registerMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const res = await axios.post(`${API_URL}/api/faces/register`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return res.data;
    },
    onSuccess: (data) => {
      toast.success(data.message);
      setName('');
      setFile(null);
      setPreview(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      queryClient.invalidateQueries({ queryKey: ['faces'] });
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Failed to register face');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await axios.delete(`${API_URL}/api/faces/${id}`);
    },
    onSuccess: () => {
      toast.success('Face removed.');
      queryClient.invalidateQueries({ queryKey: ['faces'] });
    }
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      setPreview(URL.createObjectURL(f));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !file) {
      toast.error('Name and photo are required');
      return;
    }
    const formData = new FormData();
    formData.append('name', name);
    formData.append('photo', file);
    registerMutation.mutate(formData);
  };

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-8 pb-10">
      <div className="bg-bg-card border border-border p-6 rounded-xl shadow-lg">
        <h2 className="text-xl font-bold mb-6 text-white">Register New Person</h2>
        <form onSubmit={handleSubmit} className="flex flex-col md:flex-row gap-6">
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-2">Full Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Ahmed Khan"
              className="w-full bg-bg-elevated border border-border rounded-lg px-4 py-2.5 text-white outline-none focus:border-accent-blue transition-colors"
              required
            />
            
            <button 
              type="submit"
              disabled={registerMutation.isPending}
              className="mt-6 w-full bg-accent-blue hover:bg-blue-600 text-white font-semibold py-2.5 rounded-lg transition-colors disabled:opacity-50"
            >
              {registerMutation.isPending ? 'Encoding face...' : 'Register Face'}
            </button>
          </div>
          
          <div className="w-full md:w-48 shrink-0">
            <label className="block text-sm text-gray-400 mb-2">Photo</label>
            <div 
              className="border-2 border-dashed border-border rounded-xl aspect-square w-full flex items-center justify-center bg-bg-elevated/50 hover:bg-bg-elevated transition-colors cursor-pointer relative overflow-hidden"
              onClick={() => fileInputRef.current?.click()}
            >
              {preview ? (
                <img src={preview} alt="Preview" className="h-full w-full object-cover" />
              ) : (
                <div className="text-gray-500 text-sm flex flex-col items-center">
                  <span className="text-2xl mb-2">📸</span>
                  <span>Upload</span>
                </div>
              )}
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange}
                accept=".jpg,.jpeg,.png,.webp"
                className="hidden"
              />
            </div>
          </div>
        </form>
      </div>

      <div>
        <h2 className="text-xl font-bold mb-4 text-white flex items-center gap-3">
          Known Persons
          <span className="bg-bg-elevated text-xs px-2.5 py-1 rounded-full border border-border">
            {faces.length} Total
          </span>
        </h2>
        
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1,2,3].map(i => (
              <div key={i} className="h-24 bg-bg-card animate-pulse rounded-xl border border-border"></div>
            ))}
          </div>
        ) : faces.length === 0 ? (
          <div className="text-center py-12 bg-bg-card rounded-xl border border-border text-gray-500">
            No faces registered yet. Add your first person above.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {faces.map(face => (
              <div key={face.id} className="bg-bg-card border border-border p-4 rounded-xl flex items-center gap-4 hover:scale-[1.02] transition-transform shadow-sm">
                <img 
                  src={face.photo_url.startsWith('/') ? `${API_URL}${face.photo_url}` : face.photo_url} 
                  alt={face.name} 
                  className="w-14 h-14 rounded-full object-cover bg-bg-elevated"
                />
                <div className="flex-1 overflow-hidden">
                  <h3 className="font-bold text-white truncate">{face.name}</h3>
                  <p className="text-xs text-gray-500 font-mono truncate mt-0.5">ID: {face.id.substring(0,8)}</p>
                </div>
                <button 
                  onClick={() => {
                    if (confirm(`Remove ${face.name}? This cannot be undone.`)) {
                      deleteMutation.mutate(face.id);
                    }
                  }}
                  className="text-gray-500 hover:text-accent-red hover:bg-accent-red/10 p-2 rounded-lg transition-colors"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
