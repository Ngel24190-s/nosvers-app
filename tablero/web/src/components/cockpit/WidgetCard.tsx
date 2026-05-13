import { motion, type Variants } from 'framer-motion';
import { type ReactNode } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import clsx from 'clsx';

const card = cva('cockpit-glass relative flex h-full flex-col', {
  variants: {
    critical: {
      true: 'cockpit-glass--critical animate-glow-pulse',
      false: '',
    },
  },
  defaultVariants: { critical: false },
});

const variants: Variants = {
  hidden: { opacity: 0, y: 14 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, delay: i * 0.05, ease: [0.22, 1, 0.36, 1] },
  }),
};

interface WidgetCardProps extends VariantProps<typeof card> {
  title: string;
  icon?: ReactNode;
  accent?: 'green' | 'orange' | 'violet' | 'red' | 'cyan' | 'amber';
  index?: number;
  headerExtra?: ReactNode;
  children: ReactNode;
  className?: string;
}

const accentText: Record<NonNullable<WidgetCardProps['accent']>, string> = {
  green: 'text-accent-green',
  orange: 'text-accent-orange',
  violet: 'text-accent-violet',
  red: 'text-accent-red',
  cyan: 'text-accent-cyan',
  amber: 'text-accent-amber',
};

export function WidgetCard({
  title,
  icon,
  accent = 'green',
  index = 0,
  headerExtra,
  critical,
  children,
  className,
}: WidgetCardProps) {
  return (
    <motion.div
      className={clsx(card({ critical }), className)}
      variants={variants}
      initial="hidden"
      animate="visible"
      custom={index}
    >
      <div className="flex items-center justify-between px-4 pt-3 pb-2 border-b border-cockpit-border">
        <div className="flex items-center gap-2">
          {icon && (
            <span className={clsx('flex items-center justify-center', accentText[accent])}>
              {icon}
            </span>
          )}
          <h3 className="cockpit-mono text-[11px] font-semibold uppercase tracking-[0.18em] text-cockpit-textDim">
            {title}
          </h3>
        </div>
        {headerExtra}
      </div>
      <div className="flex-1 px-4 py-3 overflow-hidden">{children}</div>
    </motion.div>
  );
}
