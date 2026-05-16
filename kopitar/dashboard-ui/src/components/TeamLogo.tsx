import { useState } from 'react'
import { TEAM_COLORS } from '../utils'

interface TeamLogoProps {
  team: string
  size?: number
  style?: React.CSSProperties
}

export function TeamLogo({ team, size = 28, style }: TeamLogoProps) {
  const [failed, setFailed] = useState(false)
  const color = TEAM_COLORS[team] ?? '#555c70'

  if (failed) {
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: size,
          height: size,
          borderRadius: '50%',
          background: color,
          color: '#fff',
          fontSize: Math.max(8, size * 0.32),
          fontWeight: 700,
          letterSpacing: '-0.03em',
          flexShrink: 0,
          ...style,
        }}
      >
        {team}
      </span>
    )
  }

  return (
    <img
      src={`https://assets.nhle.com/logos/nhl/svg/${team}_light.svg`}
      alt={team}
      width={size}
      height={size}
      onError={() => setFailed(true)}
      style={{ objectFit: 'contain', flexShrink: 0, ...style }}
    />
  )
}
