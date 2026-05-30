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

  // Detect dataset change and show a notification
  useEffect(() => {
    if (datasetId && previousDataset && datasetId !== previousDataset) {
      setShowContextUpdate(true);
      setTimeout(() => setShowContextUpdate(false), 5000);
    }
    setPreviousDataset(datasetId);
  }, [datasetId, previousDataset]);

  // Update assistant message when streaming answer changes
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
    <div className="w-96 border-l border-gray-200 bg-white flex flex-col h-full shadow-lg fixed right-0 top-0 z-40">
      <div className="p-4 border-b flex justify-between items-center">
        <h2 className="font-semibold">AI Assistant</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={handleClearMemory}
            className="text-xs text-red-500 hover:text-red-700 underline"
            title="Wipe chat memory"
          >
            Clear Memory
          </button>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {showContextUpdate && (
        <div className="bg-green-50 border-b border-green-200 p-2 text-sm text-green-700">
          ✅ New analysis detected. Context updated.
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !streaming && (
          <div className="text-gray-400 text-sm text-center mt-4">
            {datasetId ? 'Ask a question about the analyzed videos.' : 'Submit video links to start analysis.'}
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={`${msg.role}-${idx}`} className={`${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
            <div className={`inline-block max-w-[85%] p-3 rounded-lg ${
              msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-800'
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
        {streaming && !answer && <div className="text-gray-400 text-sm">Thinking...</div>}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={datasetId ? "Ask about these videos..." : "No videos analyzed yet"}
          className="flex-1 border rounded p-2 text-sm"
          disabled={streaming || !datasetId}
        />
        <button
          onClick={handleSend}
          disabled={streaming || !datasetId}
          className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}