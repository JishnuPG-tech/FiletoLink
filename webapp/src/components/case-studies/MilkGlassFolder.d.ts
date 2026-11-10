import React from "react";

export interface MilkGlassItem {
  type?: "image" | "document";
  title?: string;
  meta?: string;
  byline?: string;
  image?: {
    src: string;
    alt?: string;
    srcSet?: string;
  } | string;
  link?: string;
  file?: string;
}

export interface MilkGlassColors {
  tone?: "light" | "dark";
  shimmer1?: string;
  shimmer2?: string;
  shimmer3?: string;
  text?: string;
}

export interface MilkGlassLook {
  folder?: string;
  cards?: string;
  shadow?: string;
}

export interface MilkGlassMotion {
  hover?: boolean;
  entrance?: boolean;
  hint?: string;
}

export interface MilkGlassButton {
  label?: string;
  icon?: "arrow" | "download";
}

export interface MilkGlassFolderProps {
  title?: string;
  caption?: string;
  link?: string;
  source?: "items" | "cms";
  items?: MilkGlassItem[];
  button?: MilkGlassButton;
  colors?: MilkGlassColors;
  look?: MilkGlassLook;
  motion?: MilkGlassMotion;
  onOpen?: () => void;
  onClose?: () => void;
  style?: React.CSSProperties;
}

declare const MilkGlassFolder: React.FC<MilkGlassFolderProps>;
export default MilkGlassFolder;
