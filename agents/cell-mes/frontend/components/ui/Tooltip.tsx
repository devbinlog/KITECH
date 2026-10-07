'use client';

import { useState, useRef, useEffect, ReactNode } from 'react';
import { createPortal } from 'react-dom';

interface TooltipProps {
  children: ReactNode;
  content: ReactNode;
  delay?: number;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export function Tooltip({ children, content, delay = 200, position = 'top' }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  // display:'contents' wrapper has no layout box so onMouseEnter never fires.
  // Attach native listeners directly to the first child element instead.
  useEffect(() => {
    const wrapper = triggerRef.current;
    if (!wrapper) return;
    const child = wrapper.firstElementChild as HTMLElement | null;
    if (!child) return;

    const onEnter = () => showTooltipFn();
    const onLeave = () => hideTooltip();
    child.addEventListener('mouseenter', onEnter);
    child.addEventListener('mouseleave', onLeave);
    return () => {
      child.removeEventListener('mouseenter', onEnter);
      child.removeEventListener('mouseleave', onLeave);
    };
  });

  const showTooltipFn = () => {
    timeoutRef.current = setTimeout(() => {
      if (triggerRef.current) {
        // display:'contents' elements have no layout box, so getBoundingClientRect
        // returns (0,0,0,0). Fall back to the first child element's rect.
        let rect = triggerRef.current.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0 && triggerRef.current.firstElementChild) {
          rect = triggerRef.current.firstElementChild.getBoundingClientRect();
        }
        let x = rect.left + rect.width / 2;
        let y = rect.top;

        switch (position) {
          case 'bottom':
            y = rect.bottom + 8;
            break;
          case 'left':
            x = rect.left - 8;
            y = rect.top + rect.height / 2;
            break;
          case 'right':
            x = rect.right + 8;
            y = rect.top + rect.height / 2;
            break;
          default: // top
            y = rect.top - 8;
        }

        setCoords({ x, y });
        setIsVisible(true);
      }
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setIsVisible(false);
  };

  const tooltipStyle: React.CSSProperties = {
    position: 'fixed',
    left: coords.x,
    top: coords.y,
    transform: position === 'top' ? 'translate(-50%, -100%)' :
               position === 'bottom' ? 'translate(-50%, 0)' :
               position === 'left' ? 'translate(-100%, -50%)' :
               'translate(0, -50%)',
    zIndex: 9999,
    pointerEvents: 'none',
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={showTooltipFn}
        onMouseLeave={hideTooltip}
        style={{ display: 'contents' }}
      >
        {children}
      </div>
      {mounted && isVisible && createPortal(
        <div style={tooltipStyle}>
          <div className="bg-gray-900 text-white text-xs rounded-lg py-2 px-3 shadow-lg max-w-xs">
            {content}
          </div>
        </div>,
        document.body
      )}
    </>
  );
}

export default Tooltip;
