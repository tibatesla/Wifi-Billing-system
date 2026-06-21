# Frontend - Wi-Fi Billing System

This frontend is a starter React + TypeScript + Vite application for the Wi-Fi Billing System project.

The current UI is minimal and designed as a scaffold for building the admin portal, tenant dashboard, and payment flow.

## Project Structure

- `src/main.tsx` — React entrypoint that mounts the `App` component.
- `src/App.tsx` — Root application component and starter UI.
- `src/App.css` — Base styling for the starter page.
- `src/index.css` — Global CSS styles.
- `src/assets/` — Static images used by the starter page.

## Dependencies

- `react`
- `react-dom`
- `vite`
- `typescript`
- `@vitejs/plugin-react`

## Local Development

Install dependencies and start the development server:

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown in the terminal to preview the app.

## Build

Build the production bundle with:

```bash
npm run build
```

## Next Frontend Steps

This frontend currently contains a placeholder page. Recommended next steps:

1. Add API client utilities to call the backend `/api/v1` endpoints.
2. Build auth flow using `/api/v1/auth/login`.
3. Add routing for admin, tenant, and customer dashboards.
4. Integrate payment initiation using `/api/v1/mpesa/stk-push`.
5. Create forms for tenant/router/customer management.

## Notes

- The backend API is located under `backend/app/`.
- The frontend is not yet connected to backend logic.
- The current project is intended as a bootstrap for the Wi-Fi Billing SaaS platform.
