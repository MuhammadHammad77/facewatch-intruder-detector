import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useStore } from '../store/useStore';
import { formatDistanceToNow } from 'date-fns';
import { API_URL, BACKEND_URL } from '../utils/config';

export default function Monitor() {
  const { liveAlerts, selectedCameraSource, setSelectedSource, unreviewedCount, setSelectedAlertModal } = useStore();
  const [customSource, setCustomSource] = useState('');
  const queryClient = useQueryClient();

  useEffect(() => {
    // Fetch initial alert history
    if (liveAlerts.length === 0) {
      axios.get(`${API_URL}/api/alerts`)
        .then(res => {
          useStore.getState().setLiveAlerts(res.data);
          const unreviewed = res.data.filter((a: any) => !a.is_reviewed).length;
          useStore.getState().setUnreviewedCount(unreviewed);
        })
        .catch(err => console.error("Failed to fetch alert history", err));
    }
  }, []);

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customSource) {
      setSelectedSource(customSource);
    }
  };

  const reviewMutation = useMutation({
    mutationFn: async (id: string) => {
      await axios.put(`${API_URL}/api/alerts/${id}/review`);
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      useStore.getState().decrementUnreviewed();
      useStore.getState().setLiveAlerts(
        useStore.getState().liveAlerts.map(a => a.id === id ? { ...a, is_reviewed: true } : a)
      );
    }
  });

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-8rem)]">
      {/* Left Panel - Camera Feed */}
      <div className="w-full lg:w-3/5 flex flex-col gap-4">
        <div className="bg-bg-card p-4 rounded-xl border border-border shadow-lg flex flex-col gap-4 h-full">
          <div className="flex justify-between items-center">
            <h2 className="font-bold text-white flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-accent-green animate-pulse"></div>
              Live Feed
            </h2>
            <div className="flex gap-2">
              <select 
                value={selectedCameraSource === '0' || selectedCameraSource === '1' ? selectedCameraSource : 'custom'} 
                onChange={(e) => e.target.value !== 'custom' && setSelectedSource(e.target.value)}
                className="bg-bg-elevated text-sm rounded-lg px-3 py-2 border border-border outline-none"
              >
                <option value="0">0 — Webcam</option>
                <option value="1">1 — Ext Camera</option>
                <option value="custom">Custom RTSP...</option>
              </select>
            </div>
          </div>
          
          {selectedCameraSource !== '0' && selectedCameraSource !== '1' && (
            <form onSubmit={handleCustomSubmit} className="flex gap-2">
              <input 
                type="text" 
                placeholder="rtsp://..."
                value={customSource}
                onChange={e => setCustomSource(e.target.value)}
                className="flex-1 bg-bg-elevated border border-border rounded-lg px-3 py-2 text-sm"
              />
              <button type="submit" className="bg-accent-blue px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-600 transition-colors">
                Connect
              </button>
            </form>
          )}

          <div className="flex-1 bg-black rounded-lg overflow-hidden border border-border relative flex items-center justify-center min-h-[300px]">
            <img 
              key={selectedCameraSource}
              src={`${BACKEND_URL}/api/stream/feed/${encodeURIComponent(selectedCameraSource)}`}
              alt="Live Feed"
              className="w-full h-full object-contain"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                const parent = e.currentTarget.parentElement;
                if(parent) {
                  parent.innerHTML = '<div class="text-accent-red text-sm font-bold flex items-center justify-center h-full w-full">Stream unavailable. Check camera connection.</div>';
                }
              }}
            />
            <div className="absolute top-4 left-4 bg-black/60 px-2 py-1 rounded text-xs font-mono">
              Source: {selectedCameraSource}
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Alerts */}
      <div className="w-full lg:w-2/5 flex flex-col gap-4 h-full">
        <div className="bg-bg-card p-4 rounded-xl border border-border shadow-lg flex flex-col h-full overflow-hidden">
          <div className="flex justify-between items-center mb-4">
            <h2 className="font-bold text-white flex items-center gap-2">
              ⚠️ Alerts
              {unreviewedCount > 0 && (
                <span className="bg-accent-red text-white text-xs px-2 py-0.5 rounded-full">
                  {unreviewedCount} New
                </span>
              )}
            </h2>
            <button className="text-xs text-accent-blue hover:underline">
              History
            </button>
          </div>

          <div className="flex-1 overflow-y-auto flex flex-col gap-3 pr-2" style={{ scrollbarWidth: 'thin' }}>
            {liveAlerts.length === 0 ? (
              <div className="text-gray-500 text-center py-10 text-sm">
                No recent alerts. Monitoring...
              </div>
            ) : (
              liveAlerts.map(alert => (
                <div 
                  key={alert.id} 
                  className={`bg-bg-elevated p-3 rounded-lg border ${!alert.is_reviewed ? 'border-accent-red/50 shadow-sm shadow-accent-red/10' : 'border-border'} flex gap-4 transition-all hover:bg-bg-elevated/80`}
                >
                  <img 
                    src={alert.snapshot_url.startsWith('/') ? `${API_URL}${alert.snapshot_url}` : alert.snapshot_url} 
                    alt="Alert" 
                    className="w-20 h-20 rounded-md object-cover cursor-pointer hover:opacity-80 transition-opacity bg-black"
                    onClick={() => setSelectedAlertModal(alert)}
                  />
                  <div className="flex-1 flex flex-col justify-between py-1">
                    <div>
                      <div className="flex justify-between items-start">
                        <span className="text-accent-red font-semibold text-sm">Unknown Person</span>
                        <span className="text-xs text-gray-500 whitespace-nowrap ml-2">{formatDistanceToNow(new Date(alert.detected_at))} ago</span>
                      </div>
                      <div className="text-xs text-gray-400 mt-1">Cam: {alert.camera_source}</div>
                    </div>
                    {!alert.is_reviewed && (
                      <button 
                        onClick={() => reviewMutation.mutate(alert.id)}
                        className="text-xs text-accent-blue self-start mt-2 hover:bg-accent-blue/10 px-2 py-1 rounded transition-colors"
                      >
                        Mark Reviewed
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
