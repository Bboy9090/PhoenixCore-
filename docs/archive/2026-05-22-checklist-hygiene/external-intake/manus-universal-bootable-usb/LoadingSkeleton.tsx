import React from 'react';

interface SkeletonProps {
  className?: string;
  count?: number;
}

/**
 * Animated loading skeleton for better UX during data fetching
 */
export function SkeletonCard({ className = '' }: SkeletonProps) {
  return (
    <div className={`card animate-pulse ${className}`}>
      <div className="space-y-4">
        <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4"></div>
        <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
        <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded w-full"></div>
      </div>
    </div>
  );
}

/**
 * Skeleton for table rows
 */
export function SkeletonTableRow({ count = 5 }: SkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, idx) => (
        <tr key={idx} className="border-b border-slate-200 dark:border-slate-700">
          {Array.from({ length: 4 }).map((_, colIdx) => (
            <td key={colIdx} className="px-6 py-4">
              <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></div>
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

/**
 * Skeleton for hardware info cards
 */
export function SkeletonHardwareCard() {
  return (
    <div className="card animate-pulse">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-6 h-6 bg-slate-200 dark:bg-slate-700 rounded"></div>
        <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded w-1/3"></div>
      </div>
      <div className="space-y-2">
        <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-full"></div>
        <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-4/5"></div>
      </div>
    </div>
  );
}

/**
 * Skeleton for partition list
 */
export function SkeletonPartitionList({ count = 3 }: SkeletonProps) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, idx) => (
        <div key={idx} className="card animate-pulse">
          <div className="flex items-center justify-between mb-3">
            <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded w-1/3"></div>
            <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-1/4"></div>
          </div>
          <div className="space-y-2">
            <div className="h-2 bg-slate-200 dark:bg-slate-700 rounded w-full"></div>
            <div className="flex justify-between">
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/4"></div>
              <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/4"></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Skeleton for dashboard cards grid
 */
export function SkeletonDashboardGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {Array.from({ length: 4 }).map((_, idx) => (
        <SkeletonCard key={idx} />
      ))}
    </div>
  );
}

/**
 * Skeleton for charts
 */
export function SkeletonChart({ className = '' }: SkeletonProps) {
  return (
    <div className={`card animate-pulse ${className}`}>
      <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-4"></div>
      <div className="space-y-2">
        {Array.from({ length: 8 }).map((_, idx) => (
          <div key={idx} className="flex gap-2">
            <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded flex-1"></div>
            <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded w-1/4"></div>
          </div>
        ))}
      </div>
    </div>
  );
}
