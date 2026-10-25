import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { ErrorState } from '../components/ErrorState'
import { Banner } from '../components/Banner'

describe('Refusal / error states', () => {
  it('ErrorState renders message and retry button', () => {
    const retry = () => {}
    render(<ErrorState message="Model unreachable" onRetry={retry} />)
    expect(screen.getByText('Model unreachable')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
  })

  it('Banner renders reprocessing disclaimer', () => {
    render(<Banner variant="warn">Must sterilise before use</Banner>)
    expect(screen.getByText(/sterilise/i)).toBeInTheDocument()
  })
})
