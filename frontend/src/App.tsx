import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Doctor from "./pages/Doctor";
import Wireless from "./pages/Wireless";
import Metasploit from "./pages/Metasploit";
import Awareness from "./pages/Awareness";
import History from "./pages/History";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="doctor" element={<Doctor />} />
        <Route path="wireless" element={<Wireless />} />
        <Route path="metasploit" element={<Metasploit />} />
        <Route path="awareness" element={<Awareness />} />
        <Route path="history" element={<History />} />
      </Route>
    </Routes>
  );
}
