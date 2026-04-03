import { MessageBubble } from '@/components/chat/message-bubble';

export function UserMessage({ text }: { text: string }) {
  return (
    <div className="flex justify-end">
      <MessageBubble className="max-w-[90%] bg-slate-900 text-slate-50 sm:max-w-[75%]">
        <p className="whitespace-pre-wrap text-sm leading-relaxed">{text}</p>
      </MessageBubble>
    </div>
  );
}
