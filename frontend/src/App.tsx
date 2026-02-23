import { Routes, Route } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Landing } from "@/pages/Landing";
import { IntakeWizard } from "@/pages/IntakeWizard";
import { Dashboard } from "@/pages/Dashboard";
import { OrderDetail } from "@/pages/Dashboard/OrderDetail";
import { HumanKernel } from "@/pages/HumanKernel";
import { OpsConsole } from "@/pages/OpsConsole";

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
        <Route path="start" element={<IntakeWizard />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="dashboard/:orderId" element={<OrderDetail />} />
        <Route path="kernel/:token" element={<HumanKernel />} />
        <Route path="ops" element={<OpsConsole />} />
        <Route
          path="docs"
          element={<Placeholder title="API Documentation" />}
        />
      </Route>
    </Routes>
  );
}
