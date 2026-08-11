import { create } from 'zustand';

export interface Alert {
  id: string;
  snapshot_url: string;
  camera_source: string;
  confidence: number;
  is_reviewed: boolean;
  detected_at: string;
}

interface FaceWatchStore {
  unreviewedCount: number;
  wsStatus: 'connected' | 'disconnected' | 'reconnecting';
  liveAlerts: Alert[];
  selectedCameraSource: string;
  selectedAlertModal: Alert | null;
  
  incrementUnreviewed: () => void;
  decrementUnreviewed: () => void;
  setWsStatus: (status: 'connected' | 'disconnected' | 'reconnecting') => void;
  addLiveAlert: (alert: Alert) => void;
  setSelectedSource: (source: string) => void;
  setLiveAlerts: (alerts: Alert[]) => void;
  setUnreviewedCount: (count: number) => void;
  setSelectedAlertModal: (alert: Alert | null) => void;
}

export const useStore = create<FaceWatchStore>((set) => ({
  unreviewedCount: 0,
  wsStatus: 'disconnected',
  liveAlerts: [],
  selectedCameraSource: '0',
  selectedAlertModal: null,
  
  incrementUnreviewed: () => set((state) => ({ unreviewedCount: state.unreviewedCount + 1 })),
  decrementUnreviewed: () => set((state) => ({ unreviewedCount: Math.max(0, state.unreviewedCount - 1) })),
  setWsStatus: (status) => set({ wsStatus: status }),
  addLiveAlert: (alert) => set((state) => ({ 
    liveAlerts: [alert, ...state.liveAlerts].slice(0, 20) 
  })),
  setSelectedSource: (source) => set({ selectedCameraSource: source }),
  setLiveAlerts: (alerts) => set({ liveAlerts: alerts }),
  setUnreviewedCount: (count) => set({ unreviewedCount: count }),
  setSelectedAlertModal: (alert) => set({ selectedAlertModal: alert }),
}));
