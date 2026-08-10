import { ReactNode } from 'react';
import { cn } from '@/lib/utils';

type Props = {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  padding?: 'sm' | 'md' | 'lg';
};

const paddingMap = {
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export default function Card({ children, className, hover = false, padding = 'md' }: Props) {
  return (
    <div className={cn('glass rounded-2xl', paddingMap[padding], hover && 'glass-hover', className)}>
      {children}
    </div>
  );
}
