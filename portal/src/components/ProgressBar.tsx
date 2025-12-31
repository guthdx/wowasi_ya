interface ProgressBarProps {
  percentage: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export function ProgressBar({
  percentage,
  size = 'md',
  showLabel = true,
  className = '',
}: ProgressBarProps) {
  const heights = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
  };

  const getColor = (pct: number) => {
    if (pct >= 100) return 'bg-green-500';
    if (pct >= 75) return 'bg-slate';
    if (pct >= 50) return 'bg-slate-light';
    if (pct >= 25) return 'bg-terracotta-light';
    return 'bg-slate/50';
  };

  return (
    <div className={`w-full ${className}`}>
      <div className={`w-full bg-slate/20 rounded-full ${heights[size]} dark:bg-slate/30`}>
        <div
          className={`${heights[size]} rounded-full transition-all duration-300 ${getColor(percentage)}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-sm text-slate dark:text-slate-light mt-1 block">
          {percentage.toFixed(0)}% complete
        </span>
      )}
    </div>
  );
}
