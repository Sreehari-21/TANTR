import { InputHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

type Props = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  error?: string;
};

const Input = forwardRef<HTMLInputElement, Props>(function Input(
  { label, error, className, id, ...props },
  ref
) {
  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-slate-300">
          {label}
        </label>
      )}
      <input ref={ref} id={inputId} className={cn('input-field', error && 'border-rose-500/50', className)} {...props} />
      {error && <p className="text-xs text-rose-400">{error}</p>}
    </div>
  );
});

export default Input;
