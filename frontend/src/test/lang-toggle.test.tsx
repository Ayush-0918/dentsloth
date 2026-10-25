import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import { AppProvider } from '../context/AppContext'
import { Nav } from '../components/Nav'

const wrap = (ui: React.ReactElement) => render(
  <BrowserRouter><AppProvider>{ui}</AppProvider></BrowserRouter>
)

describe('Language toggle', () => {
  it('renders in English by default', () => {
    wrap(<Nav />)
    // Nav link text should be English (desktop + mobile tabs)
    expect(screen.getAllByText(/browse/i)[0]).toBeInTheDocument()
  })

  it('toggles to Hindi when lang button clicked', () => {
    wrap(<Nav />)
    const btn = screen.getByRole('button', { name: /switch to hindi/i })
    fireEvent.click(btn)
    // After toggle, should show Hindi text for browse (desktop + mobile tabs)
    expect(screen.getAllByText(/मार्केटप्लेस/i)[0]).toBeInTheDocument()
  })
})
