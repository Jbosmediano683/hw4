import { Route, Routes, useLocation } from 'react-router-dom'
import NavBar from './components/NavBar'
import CampusBackdrop from './components/CampusBackdrop'
import ChatWidget from './components/ChatWidget'
import Footer from './components/Footer'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import About from './pages/About'
import Login from './pages/Login'
import Signup from './pages/Signup'
import NotFound from './pages/NotFound'
import { useReveal } from './useReveal'

export default function App() {
  const location = useLocation()
  useReveal()
  return (
    <div className="app">
      <CampusBackdrop />
      <NavBar />
      {/* key on the path: each page fades in (Problem 10) */}
      <main className="main route-fade" key={location.pathname}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
      <ChatWidget />
    </div>
  )
}
