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
  activeVideoIds?: string[];
}

export default function ChatSidebar({ sessionId, platform, datasetId, isOpen, onClose, onWipeMemory, activeVideoIds = [] }: Props) {
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
    sendMessage(userMsg, activeVideoIds);
  }, [input, datasetId, sendMessage, activeVideoIds]);

  const handleClearMemory = useCallback(() => {
    setMessages([]);
    resetStreaming();
    onWipeMemory();
  }, [onWipeMemory, resetStreaming]);

  const examplePrompts = [
    "Which video has the highest hook score?",
    "Summarize the top performing video",
    "What's the average engagement rate?",
    "How can I improve my hooks?"
  ];

  if (!isOpen) return null;

  return (
    <div className="w-96 border-l border-white/20 bg-black/40 backdrop-blur-xl flex flex-col h-full shadow-2xl fixed right-0 top-0 z-40 animate-slide-up">
      <div className="p-5 border-b border-white/20 flex justify-between items-center bg-gradient-to-r from-white/10 to-transparent">
        <div>
          <h2 className="font-bold text-xl text-white flex items-center gap-2">
            🤖 AI Assistant
          </h2>
          {datasetId && (
            <span className="text-[10px] font-mono text-emerald-400 block mt-1 uppercase tracking-widest">
              ● Memory Bounds Active ({activeVideoIds.length} Nodes)
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleClearMemory}
            className="text-xs text-rose-300 hover:text-rose-100 underline transition"
            title="Wipe chat memory"
          >
            Clear Memory
          </button>
          <button onClick={onClose} className="text-white/60 hover:text-white transition-transform hover:rotate-90">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {showContextUpdate && (
        <div className="bg-emerald-500/20 border-l-4 border-emerald-400 p-3 text-sm text-emerald-100 animate-pulse-glow backdrop-blur-sm">
          ✅ New analysis detected. Context layered on top of current session memory.
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {messages.length === 0 && !streaming && (
          <div className="text-center mt-4 space-y-4">
            <div className="glass-card p-4 bg-white/10">
              <div className="text-3xl mb-2">💬</div>
              <p className="text-white/80 text-sm">
                {datasetId
                  ? "Ask anything about your videos. I can analyze engagement, hooks, semantic profiles, and trends."
                  : "Submit video links to start analysis."}
              </p>
              {datasetId && (
                <div className="mt-3 text-left">
                  <p className="text-xs font-semibold text-white/60 mb-2">✨ Try these prompts:</p>
                  <ul className="space-y-1">
                    {examplePrompts.map((prompt, idx) => (
                      <li
                        key={idx}
                        onClick={() => {
                          setInput(prompt);
                          setTimeout(() => handleSend(), 50);
                        }}
                        className="text-xs bg-white/10 hover:bg-white/20 rounded-full px-3 py-1.5 inline-block mr-1 mb-1 cursor-pointer transition text-white/90"
                      >
                        {prompt}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={`${msg.role}-${idx}`} className={`${msg.role === 'user' ? 'text-right' : 'text-left'} animate-fade-in`}>
            <div className={`inline-block max-w-[85%] p-3 rounded-2xl shadow-sm ${
              msg.role === 'user' 
                ? 'bg-gradient-to-r from-blue-600/80 to-indigo-600/80 backdrop-blur-sm text-white' 
                : 'bg-white/20 backdrop-blur-sm text-white'
            }`}>
              {msg.role === 'assistant' ? (
                <div className="prose prose-sm max-w-none prose-invert">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                <p className="text-sm">{msg.content}</p>
              )}
            </div>
          </div>
        ))}
        {streaming && !answer && <div className="text-white/60 text-sm flex gap-1">Thinking<span className="animate-pulse">...</span></div>}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-5 border-t border-white/20 flex gap-2 bg-black/20 backdrop-blur-sm">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder={datasetId ? "Ask about these videos..." : "No videos analyzed yet"}
          className="flex-1 border border-white/30 rounded-xl p-3 text-sm focus:ring-2 focus:ring-indigo-400 focus:border-transparent transition-all shadow-sm bg-white/10 text-white placeholder:text-white/50"
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