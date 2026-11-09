// Bundles the dashboard card into the file the integration serves.
import { build } from 'esbuild';

await build({
  entryPoints: ['src/card.js'],
  bundle: true,
  format: 'esm',
  target: 'es2021',
  minify: true,
  outfile: '../custom_components/atomberg_purifier_local/www/atomberg-purifier-card.js',
});
