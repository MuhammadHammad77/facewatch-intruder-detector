import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { toast } from 'sonner';
import { API_URL } from '../utils/config';

export default function Settings() {
  const queryClient = useQueryClient();

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/api/health`);
      return res.data;
    },
    refetchInterval: 10000
  });

  const refreshMutation = useMutation({
    mutationFn: async () => {
      const res = await axios.post(`${API_URL}/api/faces/refresh-cache`);
      return res.data;
    },
    onSuccess: (data) => {
      toast.success(data.message);
      queryClient.invalidateQueries({ queryKey: ['health'] });
    }
  });

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-6">
      <h2 className="text-2xl font-bold text-white mb-2">System Settings</h2>

      <div className="bg-bg-card p-6 rounded-xl border border-border shadow-lg flex justify-between items-center">
        <div>
          <h3 className="font-bold text-white">API Status</h3>
          <p className="text-sm text-gray-400 mt-1">Backend connection and health</p>
        </div>
        <div className="flex items-center gap-2">
          {health ? (
            <>
              <div className="w-2 h-2 rounded-full bg-accent-green shadow-[0_0_8px_#10b981]"></div>
              <span className="text-accent-green font-mono text-sm">Operational</span>
            </>
          ) : (
            <>
              <div className="w-2 h-2 rounded-full bg-accent-red"></div>
              <span className="text-accent-red font-mono text-sm">Unreachable</span>
            </>
          )}
        </div>
      </div>

      <div className="bg-bg-card p-6 rounded-xl border border-border shadow-lg">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-bold text-white">Face Encoding Cache</h3>
            <p className="text-sm text-gray-400 mt-1">
              Memory cache loads encodings for fast live-stream matching.<br/>
              Known faces in memory: <span className="font-mono text-white">{health?.known_faces_loaded ?? '?'}</span>
            </p>
          </div>
          <button 
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
            className="bg-bg-elevated hover:bg-border text-white px-4 py-2 rounded-lg text-sm transition-colors border border-border"
          >
            {refreshMutation.isPending ? 'Refreshing...' : 'Force Refresh'}
          </button>
        </div>
      </div>

      <div className="bg-bg-card p-6 rounded-xl border border-border shadow-lg opacity-70">
        <h3 className="font-bold text-white mb-2">Alert Cooldown</h3>
        <p className="text-sm text-gray-400">
          Alerts fire max once every 10 seconds per camera to prevent spam.
          This value is controlled by the backend <code>ALERT_COOLDOWN_SECONDS</code> environment variable.
        </p>
      </div>
    </div>
  );
}
