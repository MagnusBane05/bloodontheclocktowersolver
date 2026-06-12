import { CSSProperties, ReactNode } from "react";

export interface CircleLayoutProps {
  count: number;
  size?: number | string;
  className?: string;
  style?: CSSProperties;
  innerRingClassName?: string;
  renderPlayer: (index: number, style: CSSProperties, angle: number) => ReactNode;
  centerContent?: ReactNode;
}

export function CircleLayout({
  count, size = 280, className = '', style, innerRingClassName = 'absolute inset-0 rounded-full border border-white/30', renderPlayer, centerContent,
}: CircleLayoutProps): JSX.Element {
  const ringRadiusPercent = 37.5;

  return (
    <div className={className} style={{ width: size, height: size, position: 'relative', ...style }}>
      <div className={innerRingClassName} />
      {Array.from({ length: count }, (_, index) => {
        const angle = ((-90 + (360 * index) / count) * Math.PI) / 180;
        const x = 50 + Math.cos(angle) * ringRadiusPercent;
        const y = 50 + Math.sin(angle) * ringRadiusPercent;
        return renderPlayer(
          index,
          {
            position: 'absolute',
            left: `${x}%`,
            top: `${y}%`,
            transform: 'translate(-50%, -50%)',
          },
          angle
        );
      })}
      {centerContent}
    </div>
  );
}
