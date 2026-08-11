import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'sonner';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { AlertModal } from './components/AlertModal';
import { useAlertWebSocket } from './hooks/useAlertWebSocket';

// Pages
import Monitor from './pages/Monitor';
import Faces from './pages/Faces';
import Upload from './pages/Upload';
import Settings from './pages/Settings';

const queryClient = new QueryClient();

function AppLayout() {
  useAlertWebSocket();

  return (
    <div className="flex bg-bg-primary min-h-screen text-gray-200">
      <Sidebar />
      <div className="flex-1 sm:ml-16 flex flex-col min-h-screen w-full transition-all">
        <Header />
        <main className="flex-1 overflow-x-hidden p-6 relative">
          <Routes>
            <Route path="/" element={<Navigate to="/monitor" replace />} />
            <Route path="/monitor" element={<Monitor />} />
            <Route path="/faces" element={<Faces />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
      <AlertModal />
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppLayout />
        <Toaster theme="dark" position="top-right" />
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
