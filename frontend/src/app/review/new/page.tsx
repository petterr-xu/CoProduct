import { PageContainer } from '@/components/layout/page-container';
import { CreateReviewForm } from '@/features/create-review/create-review-form';

export default function NewReviewPage() {
  return (
    <PageContainer title='新建预审' subtitle='提交需求描述并生成结构化预审结果'>
      <div className='grid gap-4 lg:grid-cols-[1.6fr_1fr]'>
        <section className='rounded-card border border-black/10 bg-panel p-4 shadow-panel'>
          <CreateReviewForm />
        </section>

        <aside className='space-y-4'>
          <section className='rounded-card border border-black/10 bg-panel p-4 shadow-panel'>
            <h3 className='text-sm font-semibold'>输入建议</h3>
            <ul className='mt-2 list-disc space-y-1 pl-4 text-sm text-muted'>
              <li>写清楚目标用户和业务目标</li>
              <li>尽量补充权限边界和数据范围</li>
              <li>说明时效与性能预期</li>
            </ul>
          </section>

          <section className='rounded-card border border-black/10 bg-panel p-4 shadow-panel'>
            <h3 className='text-sm font-semibold'>示例</h3>
            <p className='mt-2 text-sm text-muted'>
              运营希望按活动批量导出报名用户信息，不同角色字段权限不同，主管可导出手机号。
            </p>
          </section>
        </aside>
      </div>
    </PageContainer>
  );
}
