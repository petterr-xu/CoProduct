'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter, useSearchParams } from 'next/navigation';
import type { Route } from 'next';
import { useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { ErrorAlert } from '@/components/base/error-alert';
import { authClient } from '@/lib/auth-client';
import { ApiClientError } from '@/lib/http-client';
import { buildFallbackAuthContext, useAuthStore } from '@/stores/auth-store';

const schema = z.object({
  apiKey: z.string().min(20, 'API Key 长度至少 20 位').max(128, 'API Key 过长')
});

type LoginSchema = z.infer<typeof schema>;

function mapLoginError(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.code === 'AUTH_ERROR') return 'API Key 无效或已失效。';
    if (error.code === 'USER_DISABLED') return '账号已被禁用，请联系管理员。';
    if (error.httpStatus === 0) return '网络异常，请检查前后端服务是否可访问。';
    return error.message || '登录失败，请稍后重试。';
  }
  if (error instanceof Error) return error.message || '登录失败，请稍后重试。';
  return '登录失败，请稍后重试。';
}

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setSession = useAuthStore((state) => state.setSession);
  const setAuthContext = useAuthStore((state) => state.setAuthContext);
  const redirectTarget = useMemo(() => searchParams?.get('redirect') || '/', [searchParams]);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError
  } = useForm<LoginSchema>({
    resolver: zodResolver(schema),
    defaultValues: { apiKey: '' }
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      const login = await authClient.keyLogin({
        apiKey: values.apiKey.trim(),
        deviceInfo: navigator.userAgent
      });
      setSession({ accessToken: login.accessToken, user: login.user });
      const context = await authClient.getContext(login.accessToken).catch(() => buildFallbackAuthContext(login.user));
      setAuthContext(context);
      router.replace(redirectTarget as Route);
    } catch (error) {
      setError('root', { message: mapLoginError(error) });
    }
  });

  return (
    <form className='space-y-4' onSubmit={onSubmit}>
      {errors.root?.message ? <ErrorAlert title='登录失败' message={errors.root.message} /> : null}
      <div className='space-y-1'>
        <label htmlFor='api-key' className='text-sm font-medium'>
          API Key
        </label>
        <input
          id='api-key'
          type='password'
          autoComplete='off'
          className='w-full rounded-md border border-black/20 bg-white px-3 py-2 text-sm outline-none focus:border-black/50'
          placeholder='请输入 API Key'
          {...register('apiKey')}
        />
        <p className='text-xs text-danger'>{errors.apiKey?.message}</p>
      </div>
      <button
        type='submit'
        disabled={isSubmitting}
        className='rounded-md border border-black bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-60'
      >
        {isSubmitting ? '登录中...' : '登录'}
      </button>
    </form>
  );
}
