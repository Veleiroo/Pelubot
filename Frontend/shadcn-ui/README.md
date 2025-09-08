# Shadcn-UI Template Usage Instructions

## technology stack

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS

All shadcn/ui components have been downloaded under `@/components/ui`.

## File Structure

- `index.html` - HTML entry point
- `vite.config.ts` - Vite configuration file
- `tailwind.config.js` - Tailwind CSS configuration file
- `package.json` - NPM dependencies and scripts
- `src/app.tsx` - Root component of the project
- `src/main.tsx` - Project entry point
- `src/index.css` - Existing CSS configuration
- `src/pages/Index.tsx` - Home page logic

## Components

- All shadcn/ui components are pre-downloaded and available at `@/components/ui`

## Styling

- Add global styles to `src/index.css` or create new CSS files as needed
- Use Tailwind classes for styling components

## Development

- Import components from `@/components/ui` in your React components
- Customize the UI by modifying the Tailwind configuration
- Configura la base URL del backend creando un `.env` en `Frontend/shadcn-ui/` con:

```
VITE_API_BASE_URL=http://127.0.0.1:8776
```

El archivo `src/lib/api.ts` usa `VITE_API_BASE_URL` (fallback a `http://127.0.0.1:8776`).
Si tu backend no permite llamadas sin API Key, añade también:

```
VITE_API_KEY=changeme
```

En desarrollo, alternativa: exporta `ALLOW_LOCAL_NO_AUTH=true` en el backend para no requerir API Key desde `localhost`.

## Note

- The `@/` path alias points to the `src/` directory
- In your typescript code, don't re-export types that you're already importing

# Commands

**Install Dependencies**

```shell
pnpm i
```

**Add Dependencies**

```shell
pnpm add some_new_dependency

**Start Dev**

```shell
pnpm run dev
```

**To build**

```shell
pnpm run build
```
