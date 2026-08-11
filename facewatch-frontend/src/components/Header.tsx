import { Bell } from 'lucide-react';
import { useStore } from '../store/useStore';
import { Camera } from 'lucide-react';

export const Header = () => {
  const { wsStatus, unreviewedCount } = useStore();

  return (
    <div className="h-16 bg-bg-card border-b border-border flex items-center justify-between px-6 sticky top-0 z-10 w-full">
      <div className="flex items-center sm:hidden">
        <Camera className="w-6 h-6 text-accent-blue" />
        <span className="font-bold text-white ml-3">FaceWatch</span>
      </div>
      <div className="hidden sm:block">
        {/* Title empty in desktop to let sidebar logo shine */}
      </div>

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            wsStatus === 'connected' ? 'bg-accent-green shadow-[0_0_8px_#10b981]' :
            wsStatus === 'reconnecting' ? 'bg-yellow-500 animate-pulse' :
            'bg-accent-red'
          }`} />
          <span className="text-sm text-gray-400 capitalize">{wsStatus}</span>
        </div>

        <div className="relative cursor-pointer hover:bg-bg-elevated p-2 rounded-full transition-colors">
          <Bell className="w-5 h-5 text-gray-300" />
          {unreviewedCount > 0 && (
            <div className="absolute top-1 right-1 w-4 h-4 bg-accent-red rounded-full flex items-center justify-center text-[10px] font-bold text-white border border-bg-card">
              {unreviewedCount > 99 ? '99+' : unreviewedCount}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
