import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

import { cn } from '@/lib/utils';

const badgeVariants = cva('inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium', {
  variants: {
    variant: {
      neutral: 'bg-slate-100 text-slate-700',
      supporting: 'bg-emerald-50 text-emerald-700',
      opposing: 'bg-rose-50 text-rose-700',
      alternative: 'bg-indigo-50 text-indigo-700',
      high: 'bg-emerald-50 text-emerald-700',
      medium: 'bg-amber-50 text-amber-700',
      low: 'bg-rose-50 text-rose-700',
      unknown: 'bg-slate-100 text-slate-700',
    },
  },
  defaultVariants: {
    variant: 'neutral',
  },
});

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}
