import { MessageBubble } from '@/components/chat/message-bubble';

export function LoadingMessage() {
  return (
    <MessageBubble className="max-w-2xl">
      <p className="text-sm font-medium text-slate-700">Reviewing evidence…</p>
      <div className="mt-4 space-y-2">
        <div className="h-2 w-2/3 animate-pulse rounded bg-slate-200" />
        <div className="h-2 w-5/6 animate-pulse rounded bg-slate-200" />
        <div className="h-2 w-1/2 animate-pulse rounded bg-slate-200" />
      </div>
      <div className="mt-4 space-y-1 text-xs text-slate-500">
        <p>Searching the literature</p>
        <p>Comparing supporting and opposing evidence</p>
        <p>Synthesizing a structured conclusion</p>
      </div>
    </MessageBubble>
  );
}
