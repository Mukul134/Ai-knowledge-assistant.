"use client";

import React, { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase-client";
import { apiClient } from "@/lib/api-client";
import {
  MessageSquare,
  Plus,
  Trash2,
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  LogOut,
  Send,
  BookOpen,
  FolderOpen
} from "lucide-react";

interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

interface Message {
  id?: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  citations?: Array<{ file_name: string; page_number: number }>;
}

interface Document {
  id: string;
  file_name: string;
  file_size: number;
  page_count: number | null;
  status: "uploaded" | "processing" | "completed" | "failed";
  error_message: string | null;
  created_at: string;
}

export default function WorkspacePage() {
  const router = useRouter();

  // Authentication states
  const [userEmail, setUserEmail] = useState<string>("");
  const [loadingSession, setLoadingSession] = useState(true);

  // View state: "chat" or "docs"
  const [view, setView] = useState<"chat" | "docs">("chat");

  // Chat sessions state
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionTitle, setSessionTitle] = useState("Conversation Workspace");
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");

  // Messages state
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [streamingText, setStreamingText] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  // Document states
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Ref to handle auto-scrolling
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Hook to check authentication and load base profile
  useEffect(() => {
    const checkAuth = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push("/login");
        return;
      }
      setUserEmail(session.user.email || "");
      setLoadingSession(false);

      // Load sessions and documents
      loadSessions();
      loadDocuments();
    };

    checkAuth();
  }, [router]);

  // Auto-scroll to bottom on new messages or streaming chunks
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingText]);

  // Load chat session listings
  const loadSessions = async () => {
    try {
      const list = await apiClient.get("/api/chat/session");
      setSessions(list);
      // Auto-select first session if present
      if (list.length > 0 && !activeSessionId) {
        selectSession(list[0].id, list[0].title);
      }
    } catch (err) {
      console.error("Failed to load chat sessions:", err);
    }
  };

  // Load documents metadata listings
  const loadDocuments = async () => {
    try {
      const list = await apiClient.get("/api/documents");
      setDocuments(list);
    } catch (err) {
      console.error("Failed to load documents:", err);
    }
  };

  // Set up polling for documents status changes
  useEffect(() => {
    if (view !== "docs") return;

    const interval = setInterval(() => {
      // Refresh documents status list while in document view to check parsing progress
      loadDocuments();
    }, 4000);

    return () => clearInterval(interval);
  }, [view]);

  // Create a new session thread
  const handleCreateSession = async () => {
    try {
      const newSession = await apiClient.post("/api/chat/session", {
        title: "New Conversation"
      });
      setSessions((prev) => [newSession, ...prev]);
      selectSession(newSession.id, newSession.title);
      setView("chat");
    } catch (err) {
      console.error("Failed to create session:", err);
    }
  };

  // Select a session thread to view messages
  const selectSession = async (id: string, title: string) => {
    setActiveSessionId(id);
    setSessionTitle(title);
    setStreamingText("");
    try {
      const history = await apiClient.get(`/api/chat/session/${id}/messages`);
      setMessages(history);
    } catch (err) {
      console.error("Failed to load message history:", err);
    }
  };

  // Delete a session thread
  const handleDeleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.delete(`/api/chat/session/${id}`);
      setSessions((prev) => prev.filter((s) => s.id !== id));
      if (activeSessionId === id) {
        setActiveSessionId(null);
        setMessages([]);
        setSessionTitle("Conversation Workspace");
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  // Rename a session thread
  const handleRenameSession = async (id: string) => {
    if (!renameValue.trim()) return;
    try {
      const updated = await apiClient.put(`/api/chat/session/${id}`, {
        title: renameValue
      });
      setSessions((prev) => prev.map((s) => (s.id === id ? updated : s)));
      if (activeSessionId === id) {
        setSessionTitle(updated.title);
      }
      setRenamingId(null);
    } catch (err) {
      console.error("Failed to rename session:", err);
    }
  };

  // Send a message over SSE streaming connection
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || !activeSessionId || isGenerating) return;

    const userPrompt = inputMessage;
    setInputMessage("");
    setStreamingText("");
    setIsGenerating(true);

    // Optimistically update message logs with user prompt
    const userMessage: Message = { role: "user", content: userPrompt };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error("Authentication session expired.");

      const streamUrl = apiClient.getStreamUrl(`/api/chat/session/${activeSessionId}/stream`);

      const response = await fetch(streamUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ message: userPrompt })
      });

      if (!response.ok) {
        throw new Error(`Streaming request failed: ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error("Failed to read server event streams.");

      let fullAssistantText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const rawChunk = decoder.decode(value);
        const lines = rawChunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.slice(6).trim();
            if (!dataStr) continue;

            try {
              const event = JSON.parse(dataStr);
              
              if (event.type === "text") {
                fullAssistantText += event.content;
                setStreamingText(fullAssistantText);
              } else if (event.type === "error") {
                console.error("SSE Generation error event:", event.content);
                setStreamingText((prev) => prev + `\n[System Error: ${event.content}]`);
              }
            } catch (err) {
              console.warn("Failed to parse SSE payload chunk:", dataStr);
            }
          }
        }
      }

      // Re-fetch messages from the backend to obtain the official saved logs with citations
      const updatedHistory = await apiClient.get(`/api/chat/session/${activeSessionId}/messages`);
      setMessages(updatedHistory);
      setStreamingText("");

    } catch (err: any) {
      console.error("Failed to stream answer:", err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err.message || "Failed to generate answer"}` }
      ]);
    } finally {
      setIsGenerating(false);
    }
  };

  // Upload PDF file
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);

    try {
      await apiClient.uploadFile("/api/documents/upload", file);
      // Immediately refresh documents list
      await loadDocuments();
    } catch (err: any) {
      console.error("Upload failed:", err);
      setUploadError(err.message || "Failed to upload document");
    } finally {
      setUploading(false);
    }
  };

  // Delete PDF file
  const handleDeleteDocument = async (id: string) => {
    try {
      await apiClient.delete(`/api/documents/${id}`);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      console.error("Failed to delete document:", err);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    router.push("/login");
  };

  if (loadingSession) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zinc-950 text-zinc-400 font-mono text-sm">
        <div className="animate-pulse">Loading Workspace Identity...</div>
      </div>
    );
  }

  return (
    <main className="flex h-screen bg-zinc-950 text-zinc-100 font-sans overflow-hidden">
      
      {/* 1. LEFT SIDEBAR (Thread Management) */}
      <div className="w-80 bg-zinc-900 border-r border-zinc-800 flex flex-col flex-shrink-0">
        
        {/* Profile Header */}
        <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
          <div className="truncate">
            <h2 className="font-extrabold text-sm text-zinc-200">AI Knowledge Suite</h2>
            <p className="text-[10px] text-zinc-500 truncate">{userEmail}</p>
          </div>
          <button
            onClick={handleLogout}
            title="Sign Out"
            className="p-2 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-lg transition-all"
          >
            <LogOut size={16} />
          </button>
        </div>

        {/* Action Panel */}
        <div className="p-4 space-y-2 border-b border-zinc-800">
          <button
            onClick={handleCreateSession}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl py-2.5 text-xs shadow-lg flex items-center justify-center gap-2 transition-all"
          >
            <Plus size={14} /> New Conversation
          </button>
          
          <div className="grid grid-cols-2 gap-2 text-center text-xs">
            <button
              onClick={() => setView("chat")}
              className={`py-2 rounded-lg font-medium border transition-all ${
                view === "chat"
                  ? "bg-zinc-800 text-zinc-200 border-zinc-700"
                  : "bg-transparent text-zinc-500 border-transparent hover:text-zinc-300"
              }`}
            >
              <span className="flex items-center justify-center gap-1.5"><MessageSquare size={12} /> Chat</span>
            </button>
            <button
              onClick={() => setView("docs")}
              className={`py-2 rounded-lg font-medium border transition-all ${
                view === "docs"
                  ? "bg-zinc-800 text-zinc-200 border-zinc-700"
                  : "bg-transparent text-zinc-500 border-transparent hover:text-zinc-300"
              }`}
            >
              <span className="flex items-center justify-center gap-1.5"><FolderOpen size={12} /> Files ({documents.length})</span>
            </button>
          </div>
        </div>

        {/* Sessions Thread List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2 select-none">
          <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest px-2 mb-2">History</h3>
          {sessions.length === 0 ? (
            <div className="text-center text-xs text-zinc-600 py-8">No chats active yet</div>
          ) : (
            sessions.map((s) => (
              <div
                key={s.id}
                onClick={() => selectSession(s.id, s.title)}
                className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer border transition-all ${
                  activeSessionId === s.id
                    ? "bg-zinc-800/80 text-zinc-100 border-zinc-700/80"
                    : "bg-transparent text-zinc-400 border-transparent hover:bg-zinc-850 hover:text-zinc-200"
                }`}
              >
                <div className="flex items-center gap-2 truncate flex-1">
                  <MessageSquare size={14} className="flex-shrink-0 text-zinc-500" />
                  {renamingId === s.id ? (
                    <input
                      type="text"
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onBlur={() => handleRenameSession(s.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleRenameSession(s.id);
                        if (e.key === "Escape") setRenamingId(null);
                      }}
                      autoFocus
                      className="bg-zinc-950 border border-zinc-750 rounded text-xs px-1.5 py-0.5 text-zinc-100 focus:outline-none w-full"
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <span
                      onDoubleClick={(e) => {
                        e.stopPropagation();
                        setRenamingId(s.id);
                        setRenameValue(s.title);
                      }}
                      className="text-xs truncate font-medium"
                    >
                      {s.title}
                    </span>
                  )}
                </div>
                <button
                  onClick={(e) => handleDeleteSession(s.id, e)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-zinc-500 hover:text-rose-400 rounded transition-all hover:bg-zinc-800"
                  title="Delete Thread"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* 2. MAIN PANEL */}
      <div className="flex-1 flex flex-col min-w-0 bg-zinc-950">
        
        {/* Top Header */}
        <div className="h-14 border-b border-zinc-900 flex items-center justify-between px-8 bg-zinc-950/60 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="h-2.5 w-2.5 rounded-full bg-indigo-500" />
            <h1 className="font-extrabold text-sm truncate">{sessionTitle}</h1>
          </div>
          <span className="text-xs font-semibold text-zinc-500 bg-zinc-900 border border-zinc-800 px-3 py-1 rounded-full">
            {view === "chat" ? "Grounded AI Chat" : "Document Indexing Core"}
          </span>
        </div>

        {/* View Selection Route */}
        {view === "chat" ? (
          
          /* VIEW A: CHAT WORKSPACE */
          <div className="flex-1 flex flex-col min-h-0">
            {/* Message Viewport */}
            <div className="flex-1 overflow-y-auto p-8 space-y-6">
              {messages.length === 0 && !streamingText ? (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-3">
                  <div className="h-12 w-12 rounded-full bg-zinc-900 border border-zinc-850 flex items-center justify-center text-zinc-500">
                    <MessageSquare size={20} />
                  </div>
                  <h3 className="text-zinc-400 font-bold text-sm">Grounded Knowledge Loop</h3>
                  <p className="text-xs text-zinc-650 max-w-sm leading-relaxed">
                    Ask questions about your uploaded documents. The AI agent will search your knowledge base and provide cited answers.
                  </p>
                </div>
              ) : (
                <>
                  {messages.map((m, idx) => (
                    <div
                      key={idx}
                      className={`flex flex-col space-y-2 max-w-2xl ${
                        m.role === "user" ? "ml-auto items-end" : "mr-auto items-start"
                      }`}
                    >
                      <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-semibold font-mono">
                        {m.role === "user" ? "User Query" : "AI Agent"}
                      </span>
                      <div
                        className={`rounded-2xl px-5 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                          m.role === "user"
                            ? "bg-indigo-600 text-white rounded-br-none"
                            : "bg-zinc-900 text-zinc-200 border border-zinc-850 rounded-bl-none"
                        }`}
                      >
                        {m.content}
                      </div>

                      {/* Display Citations Cards */}
                      {m.role === "assistant" && m.citations && m.citations.length > 0 && (
                        <div className="flex flex-wrap gap-2 pt-1.5">
                          {m.citations.map((cite, cIdx) => (
                            <div
                              key={cIdx}
                              className="flex items-center gap-1.5 bg-zinc-900 border border-zinc-800 text-[10px] text-zinc-400 px-2.5 py-1 rounded-full font-medium shadow-sm hover:border-zinc-700 transition-all cursor-default"
                            >
                              <BookOpen size={10} className="text-indigo-400" />
                              <span>{cite.file_name} (Page {cite.page_number})</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Streaming Block */}
                  {streamingText && (
                    <div className="flex flex-col space-y-2 max-w-2xl mr-auto items-start">
                      <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-semibold font-mono flex items-center gap-1.5">
                        <Loader2 size={10} className="animate-spin text-indigo-400" /> AI Agent Reasoning...
                      </span>
                      <div className="rounded-2xl px-5 py-3 text-sm leading-relaxed bg-zinc-900 text-zinc-200 border border-zinc-850 rounded-bl-none whitespace-pre-wrap">
                        {streamingText}
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Input Box */}
            <div className="p-6 border-t border-zinc-900 bg-zinc-950">
              <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto flex items-center gap-3">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={
                    !activeSessionId
                      ? "Create or select a chat session first..."
                      : isGenerating
                      ? "Generating agent response..."
                      : "Ask about your documents (e.g. 'What does sales.pdf say about Q3?')..."
                  }
                  disabled={!activeSessionId || isGenerating}
                  className="flex-1 bg-zinc-900 border border-zinc-800 rounded-xl px-5 py-3 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={!activeSessionId || !inputMessage.trim() || isGenerating}
                  className="p-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-zinc-900 text-white disabled:text-zinc-650 rounded-xl shadow-lg transition-all flex items-center justify-center"
                >
                  <Send size={16} />
                </button>
              </form>
            </div>
          </div>
        ) : (
          
          /* VIEW B: DOCUMENT MANAGER */
          <div className="flex-1 overflow-y-auto p-8 space-y-8 max-w-4xl mx-auto w-full">
            
            {/* Upload Area */}
            <div className="space-y-3">
              <h2 className="text-lg font-bold text-zinc-300">File Ingestion Console</h2>
              <p className="text-xs text-zinc-500">
                Upload layout-extracted PDF documents. Chunks and embeddings are processed asynchronously.
              </p>
              
              <div className="relative border-2 border-dashed border-zinc-800 hover:border-indigo-500/50 rounded-2xl p-8 text-center bg-zinc-900/20 backdrop-blur-sm transition-all group">
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
                />
                <div className="flex flex-col items-center justify-center space-y-3">
                  <div className="h-10 w-10 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center text-zinc-400 group-hover:text-indigo-400 transition-all">
                    {uploading ? <Loader2 size={18} className="animate-spin text-indigo-500" /> : <UploadCloud size={18} />}
                  </div>
                  <div className="text-xs text-zinc-400">
                    {uploading ? (
                      <span className="font-semibold text-indigo-400">Uploading and registering PDF...</span>
                    ) : (
                      <span>
                        <span className="text-indigo-400 font-semibold underline">Click to upload</span> or drag and drop a PDF file
                      </span>
                    )}
                  </div>
                  <p className="text-[10px] text-zinc-600">PDF documents only, up to 10MB</p>
                </div>
              </div>

              {uploadError && (
                <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs p-3 rounded-lg flex items-center gap-2">
                  <AlertCircle size={14} className="flex-shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}
            </div>

            {/* Ingested Documents List */}
            <div className="space-y-4">
              <h2 className="text-md font-bold text-zinc-300">Document Registry ({documents.length})</h2>
              
              <div className="space-y-3">
                {documents.length === 0 ? (
                  <div className="text-center py-16 bg-zinc-900/10 border border-zinc-900 rounded-2xl text-xs text-zinc-600 font-medium">
                    No documents indexed yet. Upload a PDF above.
                  </div>
                ) : (
                  documents.map((doc) => {
                    const sizeMb = doc.file_size / (1024 * 1024);
                    return (
                      <div
                        key={doc.id}
                        className="bg-zinc-900/60 border border-zinc-900 hover:border-zinc-800 rounded-xl p-4 flex items-center justify-between gap-4 transition-all"
                      >
                        <div className="flex items-center gap-3 truncate">
                          <div className="h-9 w-9 bg-zinc-950 rounded-lg flex items-center justify-center text-zinc-500 flex-shrink-0 border border-zinc-850">
                            <FileText size={16} />
                          </div>
                          <div className="truncate space-y-0.5">
                            <h4 className="text-xs font-semibold text-zinc-200 truncate">{doc.file_name}</h4>
                            <p className="text-[10px] text-zinc-500">
                              Size: {sizeMb.toFixed(2)} MB | Pages: {doc.page_count ?? "Processing"}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-4 flex-shrink-0">
                          {/* Ingestion Status Tags */}
                          {doc.status === "completed" && (
                            <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-0.5 rounded-full">
                              <CheckCircle2 size={10} /> Completed
                            </span>
                          )}
                          {doc.status === "processing" && (
                            <span className="flex items-center gap-1 text-[10px] font-semibold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-0.5 rounded-full animate-pulse">
                              <Loader2 size={10} className="animate-spin" /> Ingesting
                            </span>
                          )}
                          {doc.status === "uploaded" && (
                            <span className="flex items-center gap-1 text-[10px] font-semibold text-zinc-400 bg-zinc-800 border border-zinc-700 px-2.5 py-0.5 rounded-full">
                              Queued
                            </span>
                          )}
                          {doc.status === "failed" && (
                            <span
                              title={doc.error_message || "Ingestion failed"}
                              className="flex items-center gap-1 text-[10px] font-semibold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2.5 py-0.5 rounded-full cursor-help"
                            >
                              <AlertCircle size={10} /> Failed
                            </span>
                          )}

                          {/* Delete File */}
                          <button
                            onClick={() => handleDeleteDocument(doc.id)}
                            className="p-2 text-zinc-500 hover:text-rose-400 hover:bg-zinc-950 border border-transparent hover:border-zinc-850 rounded-lg transition-all"
                            title="Delete Document"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

          </div>
        )}

      </div>
    </main>
  );
}
