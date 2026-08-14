import { useStore } from '../store/useStore';
import { formatDistanceToNow } from 'date-fns';
import { API_URL } from '../utils/config';

export const AlertModal = () => {
  const { selectedAlertModal, setSelectedAlertModal } = useStore();

  if (!selectedAlertModal) return null;

  const handleClose = () => setSelectedAlertModal(null);

  let imageUrl = selectedAlertModal.snapshot_url;
  if (imageUrl.startsWith('/snapshots/') || imageUrl.startsWith('/storage/')) {
    imageUrl = `${API_URL}${imageUrl}`;
  }

  return (
    <div 
      className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4 backdrop-blur-sm"
      onClick={handleClose}
    >
      <div 
        className="bg-bg-card border border-border p-4 rounded-xl max-w-4xl w-full flex flex-col items-center gap-4 relative shadow-2xl shadow-black/50"
        onClick={e => e.stopPropagation()}
      >
        <button 
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
          onClick={handleClose}
        >
          ✕
        </button>
        
        <img 
          src={imageUrl} 
          alt="Alert Snapshot" 
          className="max-h-[70vh] rounded-lg object-contain w-full"
        />
        
        <div className="w-full bg-bg-elevated p-4 rounded-lg flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
          <div>
            <h3 className="text-accent-red font-bold flex items-center gap-2">
              ⚠️ Unknown Person
            </h3>
            <p className="text-gray-400 text-sm">
              Camera: {selectedAlertModal.camera_source}
            </p>
          </div>
          <div className="text-right">
            <p className="text-gray-300 font-medium">
              Detected {formatDistanceToNow(new Date(selectedAlertModal.detected_at))} ago
            </p>
            <p className="text-xs text-gray-500 font-mono">
              Confidence: {(selectedAlertModal.confidence * 100).toFixed(1)}% | ID: {selectedAlertModal.id.substring(0,8)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
