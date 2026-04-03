'use client';

import { SendHorizonal } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

export function ChatInput({ onSubmit, disabled }: { onSubmit: (prompt: string) => Promise<void> | void; disabled?: boolean }) {
  const [value, setValue] = useState('');

  const submit = async () => {
    const next = value.trim();
    if (!next || disabled) return;
    setValue('');
    await onSubmit(next);
  };

  return (
    <div className="rounded-xl2 border border-slate-200 bg-white p-3 shadow-soft">
      <Textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        disabled={disabled}
        placeholder="Ask a biomedical claim or question…"
        onKeyDown={async (event) => {
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            await submit();
          }
        }}
      />
      <div className="mt-3 flex items-center justify-between">
        <p className="text-xs text-slate-500">Enter to submit · Shift+Enter for newline</p>
        <Button onClick={submit} disabled={disabled || !value.trim()}>
          <SendHorizonal className="mr-1.5 h-4 w-4" />
          Submit
        </Button>
      </div>
    </div>
  );
}
