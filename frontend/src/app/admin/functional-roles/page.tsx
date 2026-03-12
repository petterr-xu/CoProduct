import { AdminOnly } from '@/components/auth/admin-only';
import { PageContainer } from '@/components/layout/page-container';
import { AdminNav } from '@/features/admin/admin-nav';
import { FunctionalRolesAdminView } from '@/features/admin/functional-roles-admin-view';

export default function AdminFunctionalRolesPage() {
  return (
    <PageContainer
      title='管理后台 · 职能角色'
      subtitle='维护组织内职能角色字典，并控制其启停状态。'
      actions={<AdminNav />}
    >
      <AdminOnly>
        <FunctionalRolesAdminView />
      </AdminOnly>
    </PageContainer>
  );
}
