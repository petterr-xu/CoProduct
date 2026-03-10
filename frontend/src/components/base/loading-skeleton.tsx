export function LoadingSkeleton() {
  return (
    <div className='space-y-3'>
      <div className='h-4 w-1/3 animate-pulse rounded bg-black/10' />
      <div className='h-4 w-full animate-pulse rounded bg-black/10' />
      <div className='h-4 w-2/3 animate-pulse rounded bg-black/10' />
    </div>
  );
}
