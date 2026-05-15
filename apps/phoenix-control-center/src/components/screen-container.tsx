import React from 'react';

interface ScreenContainerProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Web-compatible ScreenContainer for ARCWYRE Control Center.
 * Replaces the React Native version to support the Tauri/Web build.
 */
export const ScreenContainer: React.FC<ScreenContainerProps> = ({ children, className = "" }) => {
  return (
    <div className={`flex-1 min-h-full w-full bg-arc-bg ${className}`}>
      {children}
    </div>
  );
};
