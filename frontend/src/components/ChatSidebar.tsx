// frontend/src/components/ChatSidebar.tsx
import { useState, useRef, useEffect, useCallback } from 'react';
import { useStreaming } from '../hooks/useStreaming';
import ReactMarkdown from 'react-markdown';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface Props {
  sessionId: string;
  platform: string;
  datasetId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onWipeMemory: () => void;
}

export default function ChatSidebar({ sessionId, platform, datasetId, isOpen, onClose, onWipeMemory }: Props) {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState('');
  const [previousDataset, setPreviousDataset] = useState<string | null>(null);
  const [showContextUpdate, setShowContextUpdate] = useState(false);
  const { answer, streaming, sendMessage, resetStreaming } = useStreaming(sessionId, platform, datasetId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (datasetId && previousDataset && datasetId !== previousDataset) {
      setShowContextUpdate(true);
      setTimeout(() => setShowContextUpdate(false), 5000);
    }
    setPreviousDataset(datasetId);
  }, [datasetId, previousDataset]);

  useEffect(() => {
    if (answer) {
      setMessages(prev => {
        const last = prev[prev.length - 1];
        if (last && last.role === 'assistant') {
          return [...prev.slice(0, -1), { role: 'assistant', content: answer }];
        }
        return [...prev, { role: 'assistant', content: answer }];
      });
    }
  }, [answer]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = useCallback(() => {
    if (!input.trim() || !datasetId) return;
    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    sendMessage(userMsg);
  }, [input, datasetId, sendMessage]);

  const handleClearMemory = useCallback(() => {
    setMessages([]);
    resetStreaming();
    onWipeMemory();
  }, [onWipeMemory, resetStreaming]);

  if (!isOpen) return null;

  return (
    <div className="w-96 border-l border-gray-200/70 bg-white/95 backdrop-blur-md flex flex-col h-full shadow-2xl fixed right-0 top-0 z-40 animate-slide-up">
      <div className="p-5 border-b border-gray-100 flex justify-between items-center bg-gradient-to-r from-indigo-50 to-white">
        <h2 className="font-bold text-xl bg-gradient-to-r from-indigo-700 to-purple-700 bg-clip-text text-transparent">AI Assistant</h2>
        <div className="flex items-center gap-3">
          <button
            onClick={handleClearMemory}
            className="text-xs text-rose-500 hover:text-rose-700 underline transition"
            title="Wipe chat memory"
          >
            Clear Memory
          </button>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-transform hover:rotate-90">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {showContextUpdate && (
        <div className="bg-emerald-50 border-l-4 border-emerald-500 p-3 text-sm text-emerald-800 animate-pulse-glow">
          ✅ New analysis detected. Context updated.
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {messages.length === 0 && !streaming && (
          <div className="text-gray-400 text-sm text-center mt-8">
            {datasetId ? 'Ask a question about the analyzed videos.' : 'Submit video links to start analysis.'}
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={`${msg.role}-${idx}`} className={`${msg.role === 'user' ? 'text-right' : 'text-left'} animate-fade-in`}>
            <div className={`inline-block max-w-[85%] p-3 rounded-2xl shadow-sm ${
              msg.role === 'user' ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white' : 'bg-gray-100 text-gray-800'
            }`}>
              {msg.role === 'assistant' ? (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                <p className="text-sm">{msg.content}</p>
              )}
            </div>
          </div>
        ))}
        {streaming && !answer && <div className="text-gray-400 text-sm flex gap-1">Thinking<span className="animate-pulse">...</span></div>}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-5 border-t border-gray-100 flex gap-2 bg-white/50 backdrop-blur-sm">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={datasetId ? "Ask about these videos..." : "No videos analyzed yet"}
          className="flex-1 border border-gray-200 rounded-xl p-3 text-sm focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all shadow-sm"
          disabled={streaming || !datasetId}
        />
        <button
          onClick={handleSend}
          disabled={streaming || !datasetId}
          className="bg-gradient-to-r from-green-600 to-teal-600 text-white px-5 py-2 rounded-xl text-sm font-semibold shadow-md hover:shadow-lg transition-all disabled:opacity-50 transform hover:scale-105"
        >
          Send
        </button>
      </div>
    </div>
  );
}