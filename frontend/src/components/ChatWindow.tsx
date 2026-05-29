import { useState, useRef, useEffect } from 'react';
import { useStreaming } from '../hooks/useStreaming';
import SourceCitation from './SourceCitation';
import type { VideoMetadata } from '../types';

interface Props {
  sessionId: string;
  metadataA?: VideoMetadata;
  metadataB?: VideoMetadata;
}

export default function ChatWindow({ sessionId, metadataA, metadataB }: Props) {
  const [messages, setMessages] = useState<{ role: string; content: string; sources?: any[] }[]>([]);
  const [input, setInput] = useState('');
  const { answer, sources, streaming, sendMessage } = useStreaming(sessionId);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (answer || sources.length) {
      // Update or add assistant message
      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last && last.role === 'assistant') {
          return [...prev.slice(0, -1), { role: 'assistant', content: answer, sources }];
        }
        return [...prev, { role: 'assistant', content: answer, sources }];
      });
    }
  }, [answer, sources]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg = input.trim();
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    sendMessage(userMsg);
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow flex flex-col h-96">
      <h2 className="text-xl font-semibold mb-4">AI Chat</h2>
      <div className="flex-1 overflow-y-auto mb-4 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`p-3 rounded-lg ${msg.role === 'user' ? 'bg-blue-100 ml-8' : 'bg-gray-100 mr-8'}`}>
            <p className="text-sm">{msg.content}</p>
            {msg.role === 'assistant' && msg.sources && <SourceCitation sources={msg.sources} />}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a question..."
          className="flex-1 border p-2 rounded"
          disabled={streaming}
        />
        <button
          onClick={handleSend}
          disabled={streaming}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
}