import { defineConfig } from 'vitest/config';
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import ts from 'typescript';

// Vite plugin: transforms Angular .ts files using TypeScript's own compiler so
// that (a) templateUrl/styleUrls are inlined and (b) emitDecoratorMetadata is
// honoured. This runs before the default esbuild transform; esbuild then sees
// plain JavaScript and leaves it untouched.
function angularTestPlugin() {
  return {
    name: 'angular-test-transform',
    enforce: 'pre' as const,
    transform(code: string, id: string) {
      if (!id.endsWith('.ts') || id.includes('node_modules')) return null;

      // Step 1: inline templateUrl
      let src = code.replace(
        /templateUrl\s*:\s*['"`]([^'"`]+)['"`]/g,
        (_m: string, url: string) => {
          try {
            const content = readFileSync(resolve(dirname(id), url), 'utf-8')
              .replace(/`/g, '\\`')
              .replace(/\$\{/g, '\\${');
            return `template: \`${content}\``;
          } catch {
            return _m;
          }
        },
      );

      // Step 2: drop styleUrls / styleUrl
      src = src
        .replace(/styleUrls?\s*:\s*\[[^\]]*\]/g, 'styles: []')
        .replace(/styleUrl\s*:\s*['"`][^'"`]+['"`]/g, 'styles: []');

      // Step 3: compile with TypeScript to emit decorator metadata
      const result = ts.transpileModule(src, {
        fileName: id,
        compilerOptions: {
          experimentalDecorators: true,
          emitDecoratorMetadata: true,
          module: ts.ModuleKind.ESNext,
          target: ts.ScriptTarget.ES2022,
          useDefineForClassFields: false,
          strict: false,
          isolatedModules: true,
          moduleResolution: ts.ModuleResolutionKind.Bundler,
          sourceMap: true,
          inlineSources: true,
        },
      });

      return { code: result.outputText, map: result.sourceMapText };
    },
  };
}

export default defineConfig({
  plugins: [angularTestPlugin()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
});
