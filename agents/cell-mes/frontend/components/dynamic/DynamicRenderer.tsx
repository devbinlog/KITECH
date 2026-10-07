'use client';

/**
 * Dynamic Renderer
 * Renders UI components dynamically based on a UI schema from the NL Router
 */

import { ComponentRegistry } from './index';
import { UISchema } from '@/types/nlm';

interface DynamicRendererProps {
  schema: UISchema;
}

function getLayoutClass(layout: string): string {
  switch (layout) {
    case 'dashboard':
      return 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4';
    case 'grid':
      return 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4';
    case 'single':
      return 'flex flex-col gap-4';
    case 'split':
      return 'grid grid-cols-1 md:grid-cols-2 gap-4';
    case 'list':
      return 'flex flex-col gap-2';
    default:
      return 'flex flex-col gap-4';
  }
}

export function DynamicRenderer({ schema }: DynamicRendererProps) {
  if (!schema || !schema.components || schema.components.length === 0) {
    return null;
  }

  return (
    <div className="dynamic-layout">
      {schema.title && (
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          {schema.title}
        </h3>
      )}
      <div className={getLayoutClass(schema.layout)}>
        {schema.components.map((comp, idx) => {
          const Component = ComponentRegistry[comp.type];

          if (!Component) {
            console.warn(`Unknown component type: ${comp.type}`);
            return (
              <div
                key={idx}
                className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm"
              >
                Unknown component: {comp.type}
              </div>
            );
          }

          return <Component key={idx} {...comp.props} />;
        })}
      </div>
    </div>
  );
}

export default DynamicRenderer;
