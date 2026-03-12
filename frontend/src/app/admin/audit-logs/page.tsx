import { AdminOnly } from '@/components/auth/admin-only';
import { PageContainer } from '@/components/layout/page-container';
import { AuditLogsAdminView } from '@/features/admin/audit-logs-admin-view';
import { AdminNav } from '@/features/admin/admin-nav';

export default function AdminAuditLogsPage() {
  return (
    <PageContainer
      title='管理后台 · 审计日志'
      subtitle='按执行人和动作检索关键管理操作记录。'
      actions={<AdminNav />}
    >
      <AdminOnly>
        <AuditLogsAdminView />
      </AdminOnly>
    </PageContainer>
  );
}
