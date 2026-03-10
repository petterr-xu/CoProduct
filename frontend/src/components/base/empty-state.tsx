type Props = {
  title: string;
  description: string;
};

export function EmptyState({ title, description }: Props) {
  return (
    <div className='rounded-card border border-dashed border-black/20 bg-white/50 p-6 text-center'>
      <p className='text-base font-semibold'>{title}</p>
      <p className='mt-2 text-sm text-muted'>{description}</p>
    </div>
  );
}
