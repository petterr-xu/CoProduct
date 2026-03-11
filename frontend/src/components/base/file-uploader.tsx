'use client';

import { useState } from 'react';

import { apiClient, getApiErrorMessage } from '@/lib/api-client';
import { formatBytes } from '@/lib/utils';
import { FileParseStatus, UploadedFileRef } from '@/types';

type Props = {
  files: UploadedFileRef[];
  onChange: (files: UploadedFileRef[]) => void;
};

const MAX_FILES = 5;
const MAX_TOTAL_SIZE = 20 * 1024 * 1024;
const ALLOWED_EXTENSIONS = new Set(['txt', 'md', 'pdf', 'docx']);

const FILE_STATUS_LABEL_MAP: Record<FileParseStatus, string> = {
  PENDING: '待解析',
  PARSING: '解析中',
  DONE: '可用',
  FAILED: '解析失败'
};

const FILE_STATUS_COLOR_MAP: Record<FileParseStatus, string> = {
  PENDING: 'border-slate-200 bg-slate-100 text-slate-700',
  PARSING: 'border-blue-200 bg-blue-100 text-blue-700',
  DONE: 'border-green-200 bg-green-100 text-green-700',
  FAILED: 'border-red-200 bg-red-100 text-red-700'
};

export function FileUploader({ files, onChange }: Props) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  async function handleSelect(inputFiles: FileList | null) {
    if (!inputFiles || inputFiles.length === 0) return;
    setError('');

    const selected = Array.from(inputFiles);
    const unsupported = selected.find((file) => {
      const extension = file.name.split('.').pop()?.toLowerCase();
      return !extension || !ALLOWED_EXTENSIONS.has(extension);
    });
    if (unsupported) {
      setError('仅支持 txt、md、pdf、docx 附件');
      return;
    }

    const totalFiles = files.length + selected.length;
    if (totalFiles > MAX_FILES) {
      setError('最多上传 5 个附件');
      return;
    }

    const nextTotalSize = files.reduce((sum, f) => sum + f.fileSize, 0) + selected.reduce((sum, f) => sum + f.size, 0);
    if (nextTotalSize > MAX_TOTAL_SIZE) {
      setError('附件总大小不能超过 20MB');
      return;
    }

    setUploading(true);
    try {
      const uploaded: UploadedFileRef[] = [];
      for (const file of selected) {
        uploaded.push(await apiClient.uploadFile(file));
      }
      onChange([...files, ...uploaded]);
    } catch (e) {
      setError(getApiErrorMessage(e, '附件上传失败'));
    } finally {
      setUploading(false);
    }
  }

  function remove(fileId: string) {
    onChange(files.filter((item) => item.fileId !== fileId));
  }

  return (
    <div className='space-y-2'>
      <label className='inline-flex cursor-pointer rounded-md border border-black/20 bg-white px-3 py-2 text-sm font-medium'>
        {uploading ? '上传中...' : '选择附件'}
        <input type='file' className='hidden' multiple onChange={(e) => void handleSelect(e.target.files)} />
      </label>
      {error ? <p className='text-xs text-danger'>{error}</p> : null}
      <ul className='space-y-1'>
        {files.map((file) => (
          <li key={file.fileId} className='flex items-center justify-between rounded-md border border-black/10 bg-white px-3 py-2'>
            <div className='flex items-center gap-2'>
              <span className='text-sm'>
                {file.fileName} ({formatBytes(file.fileSize)})
              </span>
              <span
                className={`rounded-full border px-2 py-0.5 text-xs ${FILE_STATUS_COLOR_MAP[file.parseStatus]}`}
              >
                {FILE_STATUS_LABEL_MAP[file.parseStatus]}
              </span>
            </div>
            <button type='button' className='text-xs text-danger' onClick={() => remove(file.fileId)}>
              删除
            </button>
          </li>
        ))}
      </ul>
      {files.some((file) => file.parseStatus === 'FAILED') ? (
        <p className='text-xs text-danger'>存在解析失败的附件，建议删除后重传，或忽略失败项继续提交。</p>
      ) : null}
    </div>
  );
}
