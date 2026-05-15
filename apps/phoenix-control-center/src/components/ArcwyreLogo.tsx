import React from 'react';

interface ArcwyreLogoProps {
  size?: number;
  className?: string;
}

export const ArcwyreLogo: React.FC<ArcwyreLogoProps> = ({ size = 64, className = "" }) => {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 100 100" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Outer Power Ring */}
      <circle 
        cx="50" 
        cy="50" 
        r="45" 
        stroke="var(--arc-cyan)" 
        strokeWidth="2" 
        strokeDasharray="200"
        strokeDashoffset="40"
        opacity="0.3"
      />
      
      {/* Inner Ring */}
      <circle 
        cx="50" 
        cy="50" 
        r="35" 
        stroke="var(--arc-border)" 
        strokeWidth="1" 
      />

      {/* The Electric Arc */}
      <path 
        d="M30 70 L45 50 L55 50 L70 30" 
        stroke="url(#arcGradient)" 
        strokeWidth="4" 
        strokeLinecap="round"
        filter="url(#glow)"
      />
      
      {/* Ignition Point (Ember Gold) */}
      <circle cx="50" cy="50" r="3" fill="var(--arc-gold)" />
      
      {/* Gradients and Filters */}
      <defs>
        <linearGradient id="arcGradient" x1="30" y1="70" x2="70" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="var(--arc-cyan)" />
          <stop offset="100%" stopColor="var(--arc-blue)" />
        </linearGradient>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
          <blur stdDeviation="2" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>
    </svg>
  );
};
