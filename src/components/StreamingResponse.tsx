
import React, { forwardRef, useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Zap } from "lucide-react";

interface StreamingResponseProps {
  data: string;
  isStreaming: boolean;
}

export const StreamingResponse = forwardRef<HTMLDivElement, StreamingResponseProps>(
  ({ data, isStreaming }, ref) => {
    const [displayData, setDisplayData] = useState('');
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
      if (data.length > currentIndex) {
        // Stream data character by character for visual effect
        const timer = setTimeout(() => {
          setDisplayData(data.slice(0, currentIndex + 1));
          setCurrentIndex(prev => prev + 1);
        }, 10); // Very fast streaming

        return () => clearTimeout(timer);
      }
    }, [data, currentIndex]);

    useEffect(() => {
      if (data === '') {
        setDisplayData('');
        setCurrentIndex(0);
      }
    }, [data]);

    return (
      <Card className="backdrop-blur-sm bg-white/10 border-white/20 shadow-2xl hover:shadow-3xl transition-all duration-300">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Activity className={`w-5 h-5 ${isStreaming ? 'text-green-500 animate-pulse' : 'text-gray-500'}`} />
            Streaming Response
          </CardTitle>
          <div className="flex gap-2">
            {isStreaming && (
              <Badge variant="outline" className="bg-green-500/20 text-green-300 border-green-500/30 animate-pulse">
                <Zap className="w-3 h-3 mr-1" />
                Live
              </Badge>
            )}
            <Badge variant="outline" className="bg-blue-500/20 text-blue-300 border-blue-500/30">
              {displayData.length} chars
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div
            ref={ref}
            className="min-h-[200px] max-h-[400px] overflow-y-auto p-4 bg-black/20 rounded-lg border border-white/10 font-mono text-sm"
          >
            {displayData ? (
              <div className="whitespace-pre-wrap text-green-300">
                {displayData}
                {isStreaming && currentIndex < data.length && (
                  <span className="animate-pulse bg-green-400 text-black px-1">▌</span>
                )}
              </div>
            ) : (
              <div className="text-muted-foreground italic flex items-center justify-center h-full">
                Waiting for data stream...
                <div className="ml-2 flex space-x-1">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            )}
          </div>
          
          {isStreaming && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-muted-foreground mb-1">
                <span>Streaming Progress</span>
                <span>{Math.round((currentIndex / data.length) * 100)}%</span>
              </div>
              <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-100 ease-out"
                  style={{ width: `${(currentIndex / data.length) * 100}%` }}
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }
);

StreamingResponse.displayName = 'StreamingResponse';
