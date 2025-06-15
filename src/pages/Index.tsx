
import React, { useState, useEffect, useRef } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Send, Mic, Square, Play, Pause } from "lucide-react";
import { StreamingResponse } from "@/components/StreamingResponse";
import { ConnectionStatus } from "@/components/ConnectionStatus";
import { AnimatedBackground } from "@/components/AnimatedBackground";

const Index = () => {
  const [message, setMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingData, setStreamingData] = useState('');
  const [connectionAttempts, setConnectionAttempts] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const streamingRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      // Replace with your actual WebSocket URL
      const ws = new WebSocket('ws://localhost:8080');
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setConnectionAttempts(0);
      };

      ws.onmessage = (event) => {
        const data = event.data;
        console.log('Received data:', data);
        
        // Stream the data immediately with no delay
        setStreamingData(prev => prev + data);
        setIsStreaming(true);
        
        // Auto-scroll to bottom
        if (streamingRef.current) {
          streamingRef.current.scrollTop = streamingRef.current.scrollHeight;
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setIsStreaming(false);
        
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (connectionAttempts < 5) {
            setConnectionAttempts(prev => prev + 1);
            connectWebSocket();
          }
        }, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect:', error);
      setIsConnected(false);
    }
  };

  const sendMessage = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && message.trim()) {
      wsRef.current.send(message);
      setMessage('');
      setStreamingData(''); // Clear previous data
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearStream = () => {
    setStreamingData('');
    setIsStreaming(false);
  };

  return (
    <div className="min-h-screen relative overflow-hidden">
      <AnimatedBackground />
      
      <div className="relative z-10 container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Header */}
          <div className="text-center space-y-4 animate-fade-in">
            <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 bg-clip-text text-transparent">
              Real-Time Streaming Platform
            </h1>
            <p className="text-lg text-muted-foreground">
              Experience lightning-fast WebSocket streaming with beautiful animations
            </p>
          </div>

          {/* Connection Status */}
          <ConnectionStatus 
            isConnected={isConnected} 
            connectionAttempts={connectionAttempts}
          />

          {/* Input Section */}
          <Card className="backdrop-blur-sm bg-white/10 border-white/20 shadow-2xl hover:shadow-3xl transition-all duration-300">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Send className="w-5 h-5 text-blue-500" />
                Send Message
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message here..."
                  className="flex-1 transition-all duration-200 focus:scale-[1.02] focus:shadow-lg"
                  disabled={!isConnected}
                />
                <Button
                  onClick={sendMessage}
                  disabled={!isConnected || !message.trim()}
                  className="hover:scale-105 transition-transform duration-200"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
              
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="hover:scale-105 transition-transform">
                  <Mic className="w-4 h-4 mr-2" />
                  Voice Input
                </Button>
                <Button variant="outline" size="sm" onClick={clearStream} className="hover:scale-105 transition-transform">
                  <Square className="w-4 h-4 mr-2" />
                  Clear
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Streaming Response */}
          <StreamingResponse
            data={streamingData}
            isStreaming={isStreaming}
            ref={streamingRef}
          />

          {/* Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="backdrop-blur-sm bg-white/5 border-white/10 hover:bg-white/10 transition-all duration-300">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-green-500">{streamingData.length}</div>
                <div className="text-sm text-muted-foreground">Characters Received</div>
              </CardContent>
            </Card>
            <Card className="backdrop-blur-sm bg-white/5 border-white/10 hover:bg-white/10 transition-all duration-300">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-blue-500">{connectionAttempts}</div>
                <div className="text-sm text-muted-foreground">Connection Attempts</div>
              </CardContent>
            </Card>
            <Card className="backdrop-blur-sm bg-white/5 border-white/10 hover:bg-white/10 transition-all duration-300">
              <CardContent className="p-4 text-center">
                <div className="text-2xl font-bold text-purple-500">
                  {isStreaming ? 'Active' : 'Idle'}
                </div>
                <div className="text-sm text-muted-foreground">Stream Status</div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
