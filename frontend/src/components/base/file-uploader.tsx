'use client';

import { useState } from 'react';

import { apiClient } from '@/lib/api-client';
import { formatBytes } from '@/lib/utils';
import { UploadedFileRef } from '@/types';

type Props = {
  files: UploadedFileRef[];
  onChange: (files: UploadedFileRef[]) => void;
};

const MAX_FILES = 5;
const MAX_TOTAL_SIZE = 20 * 1024 * 1024;

export function FileUploader({ files, onChange }: Props) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  async function handleSelect(inputFiles: FileList | null) {
    if (!inputFiles || inputFiles.length === 0) return;
    setError('');

    const selected = Array.from(inputFiles);
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
      setError(e instanceof Error ? e.message : '附件上传失败');
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
            <span className='text-sm'>
              {file.fileName} ({formatBytes(file.fileSize)})
            </span>
            <button type='button' className='text-xs text-danger' onClick={() => remove(file.fileId)}>
              删除
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
