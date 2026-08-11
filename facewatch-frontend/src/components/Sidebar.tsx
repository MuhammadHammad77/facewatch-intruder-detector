import { Link, useLocation } from 'react-router-dom';
import { Monitor, Users, UploadCloud, Settings, Camera } from 'lucide-react';

export const Sidebar = () => {
  const location = useLocation();

  const links = [
    { to: '/monitor', icon: Monitor, label: 'Monitor' },
    { to: '/faces', icon: Users, label: 'Faces' },
    { to: '/upload', icon: UploadCloud, label: 'Upload' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <div className="w-16 hover:w-56 transition-all duration-200 h-screen bg-bg-card border-r border-border fixed left-0 top-0 flex flex-col z-20 group">
      <div className="h-16 flex items-center justify-center border-b border-border">
        <Camera className="w-6 h-6 text-accent-blue" />
        <span className="font-bold text-white ml-3 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          FaceWatch
        </span>
      </div>
      
      <div className="flex-1 py-4 flex flex-col gap-2">
        {links.map(({ to, icon: Icon, label }) => {
          const isActive = location.pathname.startsWith(to);
          return (
            <Link
              key={to}
              to={to}
              className={`flex items-center px-4 py-3 mx-2 rounded-lg transition-colors overflow-hidden ${
                isActive 
                  ? 'bg-accent-blue/10 text-accent-blue border-l-2 border-accent-blue' 
                  : 'text-gray-400 hover:bg-bg-elevated hover:text-white border-l-2 border-transparent'
              }`}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span className="ml-4 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                {label}
              </span>
            </Link>
          );
        })}
      </div>
      
      <div className="p-4 border-t border-border text-center overflow-hidden">
        <span className="text-xs text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
          FaceWatch v1.0
        </span>
      </div>
    </div>
  );
};
