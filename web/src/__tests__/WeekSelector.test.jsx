import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import WeekSelector from '../components/WeekSelector'

const WEEKS = [
  { date: '2026-0426', count: 4 },
  { date: '2026-0418', count: 10 },
  { date: '2026-0109', count: 9 },
]

describe('WeekSelector', () => {
  it('renders nothing when weeks is empty', () => {
    const { container } = render(
      <WeekSelector weeks={[]} toDate={null} fromDate={null} onToChange={() => {}} onFromChange={() => {}} />
    )
    expect(container.querySelectorAll('select')).toHaveLength(0)
  })

  it('renders two selects when weeks provided', () => {
    const { container } = render(
      <WeekSelector weeks={WEEKS} toDate="2026-0426" fromDate={null} onToChange={() => {}} onFromChange={() => {}} />
    )
    expect(container.querySelectorAll('select')).toHaveLength(2)
  })

  it('calls onToChange when to-date select changes', () => {
    const onToChange = vi.fn()
    render(
      <WeekSelector weeks={WEEKS} toDate="2026-0426" fromDate={null} onToChange={onToChange} onFromChange={() => {}} />
    )
    const selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[1], { target: { value: '2026-0418' } })
    expect(onToChange).toHaveBeenCalledWith('2026-0418')
  })

  it('calls onFromChange when from-date select changes', () => {
    const onFromChange = vi.fn()
    render(
      <WeekSelector weeks={WEEKS} toDate="2026-0426" fromDate={null} onToChange={() => {}} onFromChange={onFromChange} />
    )
    const selects = screen.getAllByRole('combobox')
    fireEvent.change(selects[0], { target: { value: '2026-0109' } })
    expect(onFromChange).toHaveBeenCalledWith('2026-0109')
  })

  it('renders 全期間 option in from-date select', () => {
    render(
      <WeekSelector weeks={WEEKS} toDate="2026-0426" fromDate={null} onToChange={() => {}} onFromChange={() => {}} />
    )
    expect(screen.getByText('全期間')).toBeInTheDocument()
  })
})
