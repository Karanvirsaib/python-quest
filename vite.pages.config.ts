import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import {resolve} from 'node:path';
export default defineConfig({
  root:resolve(process.cwd(),'pages'),
  base:process.env.PAGES_BASE_PATH || '/python-quest/',
  publicDir:resolve(process.cwd(),'public'),
  plugins:[react()],
  build:{outDir:resolve(process.cwd(),'dist-pages'),emptyOutDir:true},
});
