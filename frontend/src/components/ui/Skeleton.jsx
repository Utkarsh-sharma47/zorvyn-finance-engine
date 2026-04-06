export function Skeleton({ className = '' }) {
  return <div className={`animate-pulse rounded-lg bg-gray-800 ${className}`} />;
}

export function KpiSkeleton() {
  return (
    <div className="panel p-6">
      <Skeleton className="mb-3 h-3 w-24" />
      <Skeleton className="h-8 w-40" />
    </div>
  );
}
