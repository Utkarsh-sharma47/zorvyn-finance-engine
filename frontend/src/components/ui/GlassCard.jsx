/** Flat card surface — no gradients (design system). */
export function GlassCard({ children, className = '', strong = false }) {
  return (
    <div className={`${strong ? 'panel-elevated' : 'panel'} ${className}`}>
      {children}
    </div>
  );
}
