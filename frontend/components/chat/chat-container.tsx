import { AssistantMessage } from '@/components/chat/assistant-message';
import { ChatInput } from '@/components/chat/chat-input';
import { EmptyState } from '@/components/chat/empty-state';
import { ErrorState } from '@/components/chat/error-state';
import { LoadingMessage } from '@/components/chat/loading-message';
import { UserMessage } from '@/components/chat/user-message';
import { type ChatMessage } from '@/lib/types';

export function ChatContainer({
  messages,
  isLoading,
  error,
  onSubmit,
  onRetry,
  onUsePrompt,
}: {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  onSubmit: (prompt: string) => Promise<void>;
  onRetry: (prompt: string) => Promise<void>;
  onUsePrompt: (prompt: string) => Promise<void>;
}) {
  const isEmpty = messages.length === 0;

  return (
    <section className="mx-auto flex w-full max-w-4xl flex-col">
      <div className="min-h-[60vh] space-y-4 pb-6">
        {isEmpty ? (
          <EmptyState onPromptClick={onUsePrompt} />
        ) : (
          messages.map((message) => {
            if (message.role === 'user') return <UserMessage key={message.id} text={message.text} />;
            if (message.role === 'assistant_loading') return <LoadingMessage key={message.id} />;
            if (message.role === 'assistant_error') {
              return <ErrorState key={message.id} message={message.text} prompt={message.prompt} onRetry={onRetry} />;
            }
            return <AssistantMessage key={message.id} adjudication={message.adjudication} />;
          })
        )}
        {error ? <p className="text-xs text-rose-600">{error}</p> : null}
      </div>

      <div className="sticky bottom-4 mt-auto">
        <ChatInput onSubmit={onSubmit} disabled={isLoading} />
      </div>
    </section>
  );
}
