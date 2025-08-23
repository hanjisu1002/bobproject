// components/RingProgress.tsx
import React from "react";
import { Circle, Svg } from "react-native-svg";

import { palette } from "../theme";

interface Props {
  size?: number;
  strokeWidth?: number;
  progress?: number; // 0 ~ 1
  color?: string;
}

export default function RingProgress({
  size = 100,
  strokeWidth = 10,
  progress = 0,
  color = palette.primary,
}: Props) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - progress);

  return (
    <Svg width={size} height={size}>
      {/* 배경 원 */}
      <Circle
        stroke="#E5E7EB"
        fill="none"
        cx={size / 2}
        cy={size / 2}
        r={radius}
        strokeWidth={strokeWidth}
      />
      {/* 진행 원 */}
      <Circle
        stroke={color}
        fill="none"
        cx={size / 2}
        cy={size / 2}
        r={radius}
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={strokeDashoffset}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
    </Svg>
  );
}