import { AdminOnly } from '@/components/auth/admin-only';
import { PageContainer } from '@/components/layout/page-container';
import { AdminNav } from '@/features/admin/admin-nav';
import { UsersAdminView } from '@/features/admin/users-admin-view';

export default function AdminUsersPage() {
  return (
    <PageContainer
      title='管理后台 · 成员管理'
      subtitle='管理组织成员的权限角色、成员状态和职能角色。'
      actions={<AdminNav />}
    >
      <AdminOnly>
        <UsersAdminView />
      </AdminOnly>
    </PageContainer>
  );
}
