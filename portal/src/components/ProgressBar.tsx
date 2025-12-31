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
    if (pct >= 75) return 'bg-blue-500';
    if (pct >= 50) return 'bg-yellow-500';
    if (pct >= 25) return 'bg-orange-500';
    return 'bg-gray-400';
  };

  return (
    <div className={`w-full ${className}`}>
      <div className={`w-full bg-gray-200 rounded-full ${heights[size]} dark:bg-gray-700`}>
        <div
          className={`${heights[size]} rounded-full transition-all duration-300 ${getColor(percentage)}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-sm text-gray-600 dark:text-gray-400 mt-1 block">
          {percentage.toFixed(0)}% complete
        </span>
      )}
    </div>
  );
}
