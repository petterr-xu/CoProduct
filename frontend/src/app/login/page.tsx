import { LoginForm } from '@/features/auth/login-form';

export default function LoginPage() {
  return (
    <main className='mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-6xl items-center justify-center px-4 py-10'>
      <section className='w-full max-w-md rounded-card border border-black/10 bg-panel p-6 shadow-panel'>
        <h1 className='text-xl font-semibold'>登录 CoProduct</h1>
        <p className='mt-2 text-sm text-muted'>请输入管理员签发的 API Key 访问预审系统。</p>
        <div className='mt-5'>
          <LoginForm />
        </div>
      </section>
    </main>
  );
}

