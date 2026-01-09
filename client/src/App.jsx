import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Inventory from "./pages/Inventory";
import BulkUpload from "./pages/BulkUpload";
import "./App.css";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Inventory />} />
        <Route path="/bulk-upload" element={<BulkUpload />} />
      </Routes>
    </Router>
  );
}

export default App;
