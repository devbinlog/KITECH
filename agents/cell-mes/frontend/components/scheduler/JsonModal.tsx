"use client";

import { Download } from "lucide-react";

interface JsonModalProps {
  isOpen: boolean;
  title: string;
  data: any;
  onClose: () => void;
}

export function JsonModal({ isOpen, title, data, onClose }: JsonModalProps) {
  if (!isOpen || !data) return null;

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">{title}</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              className="btn btn-secondary text-sm flex items-center gap-1"
            >
              <Download size={14} />
              다운로드
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded"
            >
              ✕
            </button>
          </div>
        </div>
        <div className="p-4 overflow-auto flex-1">
          <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-sm overflow-auto">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}
