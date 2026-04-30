import { Route, Routes } from "react-router-dom";

import { Layout } from "@/components/Layout";
import { Toaster } from "@/components/ui/toaster";
import { Dashboard } from "@/pages/Dashboard";
import { Targets } from "@/pages/Targets";
import { TargetDetail } from "@/pages/TargetDetail";
import { Modules } from "@/pages/Modules";

export default function App() {
  return (
    <>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="targets" element={<Targets />} />
          <Route path="targets/:id" element={<TargetDetail />} />
          <Route path="modules" element={<Modules />} />
        </Route>
      </Routes>
      <Toaster />
    </>
  );
}
