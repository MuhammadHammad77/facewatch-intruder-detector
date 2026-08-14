import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { playAlertSound } from '../utils/audio';
import { API_URL } from '../utils/config';

export default function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState<any>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_URL}/api/stream/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResults(res.data);
      
      if (res.data.unknown_detections > 0) {
        toast.error(`Analysis complete: ${res.data.unknown_detections} unknown persons detected!`);
        // Play alert sound
        playAlertSound('upload');
      } else {
        toast.success("Analysis complete. No unknown persons detected.");
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-6">
      <div className="bg-bg-card p-8 rounded-xl border border-border shadow-lg">
        <h2 className="text-xl font-bold mb-2 text-white">Analyze Recorded Video</h2>
        <p className="text-gray-400 text-sm mb-6">Upload an MP4, AVI, or MKV file to scan for unknown persons.</p>
        
        <div className="border-2 border-dashed border-border rounded-xl h-64 flex flex-col items-center justify-center bg-bg-elevated/50 hover:bg-bg-elevated transition-colors cursor-pointer relative overflow-hidden mb-6">
          <input 
            type="file" 
            onChange={handleFileChange}
            accept="video/mp4,video/x-m4v,video/*"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          <div className="text-4xl mb-4">🎥</div>
          {file ? (
            <div className="text-accent-blue font-semibold text-center px-4">
              {file.name}
              <div className="text-gray-500 text-xs mt-1">{(file.size / (1024*1024)).toFixed(2)} MB</div>
            </div>
          ) : (
            <div className="text-gray-400 text-center px-4">
              Drag & drop a video file here, or click to select<br/>
              <span className="text-xs text-gray-500 mt-2 block">Max 100MB</span>
            </div>
          )}
        </div>

        <button 
          onClick={handleUpload}
          disabled={!file || isUploading}
          className="w-full flex justify-center items-center bg-accent-blue hover:bg-blue-600 disabled:bg-bg-elevated disabled:text-gray-500 text-white font-bold py-3 rounded-lg transition-colors"
        >
          {isUploading ? (
            <>
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Analyzing Video...
            </>
          ) : 'Start Analysis'}
        </button>
      </div>

      {results && (
        <div className="bg-bg-card p-6 rounded-xl border border-border shadow-lg animate-in slide-in-from-bottom-4">
          <h3 className="font-bold text-white mb-4">Analysis Results</h3>
          <div className="flex gap-4 mb-6">
            <div className="bg-bg-elevated p-4 rounded-lg flex-1 border border-border">
              <div className="text-gray-400 text-xs uppercase tracking-wider mb-1">Frames Analyzed</div>
              <div className="text-2xl font-bold text-white">{results.processed_frames || 0}</div>
            </div>
            <div className="bg-bg-elevated p-4 rounded-lg flex-1 border border-border">
              <div className="text-gray-400 text-xs uppercase tracking-wider mb-1">Unknown Detections</div>
              <div className="text-2xl font-bold text-accent-red">{results.unknown_detections || 0}</div>
            </div>
          </div>
          
          {results.unknown_detections > 0 && results.detections && results.detections.length > 0 && (
            <div className="mb-6">
              <h4 className="text-sm font-bold text-white mb-3">Detected Snapshots</h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 max-h-96 overflow-y-auto pr-2" style={{ scrollbarWidth: 'thin' }}>
                {results.detections.map((det: any, idx: number) => (
                  <div key={idx} className="bg-bg-elevated rounded-lg overflow-hidden border border-border">
                    <img 
                      src={det.snapshot_url.startsWith('/') ? `${API_URL}${det.snapshot_url}` : det.snapshot_url}
                      alt={`Detection at frame ${det.frame}`}
                      className="w-full h-32 object-cover"
                    />
                    <div className="p-2 text-xs text-gray-400">
                      <div>Time: {det.timestamp_sec}s</div>
                      <div>Unknowns: {det.unknown_count}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="text-gray-400 text-sm">
            {results.message || "Video processed successfully."}
          </div>
        </div>
      )}
    </div>
  );
}
