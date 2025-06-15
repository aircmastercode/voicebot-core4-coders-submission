
import React from 'react';
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Wifi, WifiOff, RotateCcw } from "lucide-react";

interface ConnectionStatusProps {
  isConnected: boolean;
  connectionAttempts: number;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({
  isConnected,
  connectionAttempts
}) => {
  return (
    <Card className="backdrop-blur-sm bg-white/5 border-white/10">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isConnected ? (
              <Wifi className="w-5 h-5 text-green-500 animate-pulse" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-500" />
            )}
            <div>
              <div className="font-medium">
                {isConnected ? 'Connected' : 'Disconnected'}
              </div>
              <div className="text-sm text-muted-foreground">
                WebSocket Status
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {connectionAttempts > 0 && !isConnected && (
              <div className="flex items-center gap-2 text-yellow-500">
                <RotateCcw className="w-4 h-4 animate-spin" />
                <span className="text-sm">Retry {connectionAttempts}/5</span>
              </div>
            )}
            <Badge 
              variant={isConnected ? "default" : "destructive"}
              className={`transition-all duration-300 ${
                isConnected 
                  ? 'bg-green-500/20 text-green-300 border-green-500/30' 
                  : 'bg-red-500/20 text-red-300 border-red-500/30'
              }`}
            >
              {isConnected ? 'Online' : 'Offline'}
            </Badge>
          </div>
        </div>
        
        {!isConnected && connectionAttempts > 0 && (
          <div className="mt-3">
            <div className="w-full bg-white/10 rounded-full h-1.5">
              <div 
                className="h-full bg-gradient-to-r from-yellow-500 to-orange-500 rounded-full transition-all duration-1000"
                style={{ width: `${(connectionAttempts / 5) * 100}%` }}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
