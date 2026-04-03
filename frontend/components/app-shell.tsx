'use client';

import { Header } from '@/components/header';
import { ChatContainer } from '@/components/chat/chat-container';
import { useEvidenceChat } from '@/hooks/use-evidence-chat';

export function AppShell() {
  const chat = useEvidenceChat();

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="mx-auto w-full max-w-6xl px-4 pb-8 pt-6 sm:px-6">
        <ChatContainer
          messages={chat.messages}
          isLoading={chat.isLoading}
          error={chat.error}
          onSubmit={chat.submitPrompt}
          onRetry={chat.retry}
          onUsePrompt={chat.submitPrompt}
        />
      </main>
      <footer className="pb-8 text-center text-xs text-slate-500">
        For research exploration only. Not medical advice.
      </footer>
    </div>
  );
}
