type Props = {
  title?: string;
  message: string;
};

export function ErrorAlert({ title = '请求失败', message }: Props) {
  return (
    <div className='rounded-card border border-danger/20 bg-red-50 p-3 text-sm text-danger'>
      <p className='font-semibold'>{title}</p>
      <p className='mt-1'>{message}</p>
    </div>
  );
}
