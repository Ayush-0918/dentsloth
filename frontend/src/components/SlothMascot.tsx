
import './SlothMascot.css'
type State = 'resting' | 'thinking' | 'happy'
interface Props { state?: State; size?: number }

export function SlothMascot({ state = 'resting', size = 120 }: Props) {
  return (
    <div className={`sloth sloth--${state}`} aria-hidden="true" style={{ width: size, height: size }}>
      <svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" width={size} height={size}>
        {/* Body */}
        <ellipse cx="60" cy="72" rx="30" ry="28" fill="#3A0F34"/>
        {/* Head */}
        <circle cx="60" cy="46" r="22" fill="#3A0F34"/>
        {/* Face plate */}
        <ellipse cx="60" cy="49" rx="15" ry="13" fill="#DDE3E8" opacity=".9"/>
        {/* Ears */}
        <circle cx="38" cy="34" r="8" fill="#DDE3E8" opacity=".8"/>
        <circle cx="82" cy="34" r="8" fill="#DDE3E8" opacity=".8"/>
        <circle cx="38" cy="34" r="4" fill="#3A0F34" opacity=".4"/>
        <circle cx="82" cy="34" r="4" fill="#3A0F34" opacity=".4"/>
        {/* Eyes */}
        {state === 'thinking' ? (
          <>
            <ellipse cx="54" cy="46" rx="3.5" ry="2" fill="#3A0F34" className="eye-blink"/>
            <ellipse cx="66" cy="46" rx="3.5" ry="2" fill="#3A0F34" className="eye-blink"/>
          </>
        ) : state === 'happy' ? (
          <>
            <path d="M51 46 Q54 43 57 46" stroke="#3A0F34" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
            <path d="M63 46 Q66 43 69 46" stroke="#3A0F34" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
          </>
        ) : (
          <>
            <circle cx="54" cy="46" r="3.5" fill="#3A0F34"/>
            <circle cx="66" cy="46" r="3.5" fill="#3A0F34"/>
            <circle cx="55.2" cy="45" r="1" fill="white"/>
            <circle cx="67.2" cy="45" r="1" fill="white"/>
          </>
        )}
        {/* Nose */}
        <ellipse cx="60" cy="52" rx="3" ry="2" fill="#3A0F34" opacity=".5"/>
        {/* Smile */}
        {state !== 'thinking' && (
          <path d="M55 56 Q60 60 65 56" stroke="#3A0F34" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
        )}
        {/* Arms */}
        <ellipse cx="34" cy="72" rx="7" ry="18" fill="#3A0F34" transform="rotate(-20 34 72)"/>
        <ellipse cx="86" cy="72" rx="7" ry="18" fill="#3A0F34" transform="rotate(20 86 72)"/>
        {/* Claws */}
        <path d="M22 84 Q24 90 26 84" stroke="#DDE3E8" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
        <path d="M26 86 Q28 92 30 86" stroke="#DDE3E8" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
        <path d="M98 84 Q96 90 94 84" stroke="#DDE3E8" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
        <path d="M94 86 Q92 92 90 86" stroke="#DDE3E8" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
        {/* Marigold accent – small leaf/scarf */}
        {state === 'happy' ? (
          <path d="M48 64 Q60 58 72 64 Q60 62 48 64Z" fill="#EAAA00"/>
        ) : (
          <circle cx="78" cy="60" r="5" fill="#EAAA00" opacity=".85"/>
        )}
        {/* Tummy stripe */}
        <ellipse cx="60" cy="76" rx="12" ry="10" fill="#DDE3E8" opacity=".18"/>
      </svg>
    </div>
  )
}
