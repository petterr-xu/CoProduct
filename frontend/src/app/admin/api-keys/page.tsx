import { AdminOnly } from '@/components/auth/admin-only';
import { PageContainer } from '@/components/layout/page-container';
import { ApiKeysAdminView } from '@/features/admin/api-keys-admin-view';
import { AdminNav } from '@/features/admin/admin-nav';

export default function AdminApiKeysPage() {
  return (
    <PageContainer
      title='管理后台 · API Key 管理'
      subtitle='签发、查询并吊销团队成员 API Key。'
      actions={<AdminNav />}
    >
      <AdminOnly>
        <ApiKeysAdminView />
      </AdminOnly>
    </PageContainer>
  );
}
