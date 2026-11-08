import React from 'react';

export interface CopierProps {
  style?: React.CSSProperties;
  className?: string;
  theme?: 'dark' | 'light' | 'auto';
  content?: {
    label?: string;
    value?: string;
    mark?: string;
  };
  light?: {
    body?: string;
    tray?: string;
    accent?: string;
    paper?: string;
    ink?: string;
    shadow?: string;
    strength?: number;
  };
  dark?: {
    body?: string;
    tray?: string;
    accent?: string;
    paper?: string;
    ink?: string;
    shadow?: string;
    strength?: number;
  };
  behavior?: {
    sound?: boolean;
    haptics?: boolean;
    keepCopies?: boolean;
    canvasState?: 'rest' | 'tray';
  };
  onCopy?: () => void;
}

declare const Copier: React.FC<CopierProps>;
export default Copier;
