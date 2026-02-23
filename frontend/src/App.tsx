import { Routes, Route } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Landing } from "@/pages/Landing";

// Lightweight placeholder pages for routes that haven't been built yet.
function Placeholder({ title }: { title: string }) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="text-center">
        <h1 className="heading-display text-3xl text-stone-100">{title}</h1>
        <p className="mt-2 text-sm text-stone-500">Coming soon.</p>
      </div>
    </div>
  );
}

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Landing />} />
        <Route
          path="start"
          element={<Placeholder title="Intake Wizard" />}
        />
        <Route
          path="dashboard"
          element={<Placeholder title="Dashboard" />}
        />
        <Route
          path="dashboard/:orderId"
          element={<Placeholder title="Order Detail" />}
        />
        <Route
          path="kernel/:token"
          element={<Placeholder title="Human Kernel" />}
        />
        <Route
          path="ops"
          element={<Placeholder title="Ops Console" />}
        />
        <Route
          path="docs"
          element={<Placeholder title="API Documentation" />}
        />
      </Route>
    </Routes>
  );
}
