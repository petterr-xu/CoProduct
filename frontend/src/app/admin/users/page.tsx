import { AdminOnly } from '@/components/auth/admin-only';
import { PageContainer } from '@/components/layout/page-container';
import { AdminNav } from '@/features/admin/admin-nav';
import { UsersAdminView } from '@/features/admin/users-admin-view';

export default function AdminUsersPage() {
  return (
    <PageContainer
      title='管理后台 · 用户管理'
      subtitle='查看团队用户并执行创建、角色调整、状态变更。'
      actions={<AdminNav />}
    >
      <AdminOnly>
        <UsersAdminView />
      </AdminOnly>
    </PageContainer>
  );
}
