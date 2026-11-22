"""
Inline SVG assets for Campus Helpdesk Assistant SaaS UI redesign.
Provides original geometric logo mark, friendly robot mascot, connector arrows,
cursor glyph, and floating card icons matching the Dribbble reference design language.
"""

# ==============================================================================
# 1. LOGO & BRANDING MARKS
# ==============================================================================
LOGO_GLYPH_SVG = '''<svg width="34" height="34" viewBox="0 0 34 34" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="17" cy="17" r="17" fill="url(#logo_grad_1)"/>
  <circle cx="17" cy="17" r="16.2" stroke="rgba(255,255,255,0.4)" stroke-width="1.6"/>
  <!-- Geometric abstract crest: interlocking academic diamond & chat loop -->
  <path d="M17 7.5L24.5 13L17 18.5L9.5 13L17 7.5Z" fill="#FFFFFF"/>
  <path d="M12.5 15.5L17 18.8L21.5 15.5V20.5C21.5 23 19.5 25 17 25C14.5 25 12.5 23 12.5 20.5V15.5Z" fill="#FFFFFF" fill-opacity="0.85"/>
  <circle cx="17" cy="13" r="2.2" fill="#2F5BEA"/>
  <defs>
    <linearGradient id="logo_grad_1" x1="0" y1="0" x2="34" y2="34" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#2F5BEA"/>
      <stop offset="60%" stop-color="#4F46E5"/>
      <stop offset="100%" stop-color="#7C3AED"/>
    </linearGradient>
  </defs>
</svg>'''

LOGO_FULL_SVG = f'''<div style="display:flex; align-items:center; gap:10px;">
  {LOGO_GLYPH_SVG}
  <div style="display:flex; flex-direction:column;">
    <span style="font-family:'Plus Jakarta Sans',sans-serif; font-size:16px; font-weight:800; color:#0D0F14; letter-spacing:-0.02em; line-height:1.15;">campus<span style="color:#2F5BEA;">helpdesk</span></span>
    <span style="font-size:10px; font-weight:600; color:#667085; letter-spacing:0.02em; text-transform:uppercase;">Official Assistant</span>
  </div>
</div>'''


# ==============================================================================
# 2. HERO CURSOR GLYPH (ANIMATED HAND POINTER)
# ==============================================================================
CURSOR_GLYPH_SVG = '''<span class="animated-cursor-glyph" style="display:inline-block; vertical-align:middle; margin-left:6px; position:relative; top:-2px;">
<svg width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Click ripple rings -->
  <circle class="cursor-ripple" cx="20" cy="18" r="9" stroke="#2F5BEA" stroke-width="1.8" stroke-dasharray="3 3" opacity="0.65"/>
  <circle class="cursor-ripple-2" cx="20" cy="18" r="14" stroke="#818CF8" stroke-width="1.2" opacity="0.4"/>
  <!-- Stylized hand pointer with soft warm gradient -->
  <path d="M20.2 6.5C19.3 6.5 18.5 7.3 18.5 8.2V19.8L16.2 18.5C15.4 18.0 14.3 18.2 13.8 19.1C13.3 20.0 13.5 21.1 14.4 21.6L20.8 26.6C22.0 27.5 23.5 28.0 25.0 28.0H27.5C30.3 28.0 32.5 25.8 32.5 23.0V16.8C32.5 15.9 31.7 15.1 30.8 15.1C30.6 15.1 30.4 15.2 30.2 15.3C29.9 14.4 29.1 13.8 28.1 13.8C27.9 13.8 27.6 13.9 27.4 14.0C27.0 13.2 26.1 12.6 25.1 12.6C24.8 12.6 24.5 12.7 24.2 12.8V8.2C24.2 7.3 23.4 6.5 22.5 6.5H20.2Z" 
        fill="#FFFFFF" stroke="#0D0F14" stroke-width="2.2" stroke-linejoin="round"/>
  <path d="M22.5 12.8V8.2C22.5 7.7 22.1 7.3 21.6 7.3C21.1 7.3 20.7 7.7 20.7 8.2V17.5" stroke="#0D0F14" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M24.2 15.5V13.8C24.2 13.3 24.6 12.9 25.1 12.9C25.6 12.9 26.0 13.3 26.0 13.8V17.5" stroke="#0D0F14" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M27.4 16.5V15.0C27.4 14.5 27.8 14.1 28.3 14.1C28.8 14.1 29.2 14.5 29.2 15.0V18.0" stroke="#0D0F14" stroke-width="1.8" stroke-linecap="round"/>
</svg>
</span>'''


# ==============================================================================
# 3. FLOATING HERO CARDS ICONS
# ==============================================================================
ICON_AI_HELPER_SVG = '''<svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect x="3" y="4" width="18" height="15" rx="4" fill="#EEF2FF" stroke="#4F46E5" stroke-width="1.8"/>
  <circle cx="8.5" cy="11.5" r="1.8" fill="#2F5BEA"/>
  <circle cx="15.5" cy="11.5" r="1.8" fill="#2F5BEA"/>
  <path d="M10.5 15C11.3 15.8 12.7 15.8 13.5 15" stroke="#2F5BEA" stroke-width="1.8" stroke-linecap="round"/>
  <path d="M12 2V4" stroke="#4F46E5" stroke-width="1.8" stroke-linecap="round"/>
  <circle cx="12" cy="2" r="1" fill="#4F46E5"/>
</svg>'''

ICON_GRAPH_SVG = '''<svg width="26" height="26" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="28" height="28" rx="8" fill="#0D0F14"/>
  <path d="M7 19.5L12 14.5L16 17.5L21 11" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="21" cy="11" r="2" fill="#2F5BEA" stroke="#FFFFFF" stroke-width="1.5"/>
</svg>'''


# ==============================================================================
# 4. ORIGINAL ROBOT MASCOT (SOFT PERIWINKLE & BLUE)
# ==============================================================================
ROBOT_MASCOT_SVG = '''<svg class="mascot-robot" width="170" height="170" viewBox="0 0 170 170" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <radialGradient id="robot_head_glow" cx="50%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#E0E7FF"/>
      <stop offset="70%" stop-color="#C7D2FE"/>
      <stop offset="100%" stop-color="#A5B4FC"/>
    </radialGradient>
    <linearGradient id="robot_torso_grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#E0E7FF"/>
      <stop offset="100%" stop-color="#B9CCF5"/>
    </linearGradient>
    <linearGradient id="visor_grad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1E293B"/>
      <stop offset="100%" stop-color="#0F172A"/>
    </linearGradient>
    <filter id="eye_glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="1.5" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <!-- Antenna -->
  <path d="M85 32V18" stroke="#4F46E5" stroke-width="3" stroke-linecap="round"/>
  <circle cx="85" cy="16" r="6" fill="#2F5BEA"/>
  <circle cx="85" cy="16" r="3" fill="#67E8F9"/>

  <!-- Ears / Headphone nubs -->
  <rect x="28" y="52" width="8" height="24" rx="4" fill="#3B82F6"/>
  <rect x="134" y="52" width="8" height="24" rx="4" fill="#3B82F6"/>

  <!-- Robot Head -->
  <rect x="34" y="32" width="102" height="64" rx="28" fill="url(#robot_head_glow)" stroke="#FFFFFF" stroke-width="2"/>

  <!-- Visor Screen -->
  <rect x="44" y="42" width="82" height="44" rx="16" fill="url(#visor_grad)"/>

  <!-- Happy Curved Eyes (Friendly Expression) -->
  <path d="M56 64C56 59 62 55 68 60" stroke="#38BDF8" stroke-width="3.5" stroke-linecap="round" filter="url(#eye_glow)"/>
  <path d="M102 64C102 59 108 55 114 60" stroke="#38BDF8" stroke-width="3.5" stroke-linecap="round" filter="url(#eye_glow)"/>

  <!-- Cute Rosy Cheek Dots -->
  <circle cx="53" cy="74" r="3" fill="#F472B6" fill-opacity="0.6"/>
  <circle cx="117" cy="74" r="3" fill="#F472B6" fill-opacity="0.6"/>

  <!-- Neck Joint -->
  <rect x="75" y="96" width="20" height="8" rx="3" fill="#64748B"/>

  <!-- Torso -->
  <rect x="52" y="104" width="66" height="52" rx="20" fill="url(#robot_torso_grad)" stroke="#FFFFFF" stroke-width="1.5"/>
  <circle cx="85" cy="126" r="10" fill="#2F5BEA"/>
  <circle cx="85" cy="126" r="4" fill="#A5B4FC"/>

  <!-- Left Arm (Resting on side) -->
  <path d="M48 112C36 120 34 136 38 148" stroke="#A5B4FC" stroke-width="6" stroke-linecap="round"/>
  <circle cx="38" cy="150" r="5" fill="#3B82F6"/>

  <!-- Right Arm (Gesturing towards chat card) -->
  <path d="M122 112C134 116 144 118 152 110" stroke="#A5B4FC" stroke-width="6" stroke-linecap="round"/>
  <circle cx="154" cy="108" r="5" fill="#3B82F6"/>

  <!-- Little Document in Hand -->
  <g transform="translate(142, 90) rotate(12)">
    <rect width="18" height="24" rx="3" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.2"/>
    <line x1="4" y1="6" x2="14" y2="6" stroke="#2F5BEA" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="4" y1="10" x2="12" y2="10" stroke="#94A3B8" stroke-width="1.2" stroke-linecap="round"/>
    <line x1="4" y1="14" x2="10" y2="14" stroke="#94A3B8" stroke-width="1.2" stroke-linecap="round"/>
  </g>
</svg>'''


# ==============================================================================
# 5. CHAT PREVIEW CARD ILLUSTRATION
# ==============================================================================
CHAT_CARD_ILLUSTRATION_SVG = '''<div class="hero-chat-card" style="background:#FFFFFF; border-radius:18px; padding:18px 20px; box-shadow:0 12px 32px rgba(15,23,42,0.08); border:1px solid rgba(255,255,255,0.9); width:100%; max-width:280px;">
  <!-- Turn 1: Student Question -->
  <div style="display:flex; align-items:flex-start; gap:10px; margin-bottom:12px;">
    <div style="width:28px; height:28px; border-radius:50%; background:linear-gradient(135deg, #FDE68A 0%, #F59E0B 100%); display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:700; color:#78350F; flex-shrink:0;">
      🎓
    </div>
    <div style="flex:1;">
      <div style="height:10px; width:88%; background:#EEF2FF; border-radius:6px; margin-bottom:6px;"></div>
      <div style="height:10px; width:64%; background:#EEF2FF; border-radius:6px;"></div>
    </div>
  </div>

  <!-- Turn 2: Assistant Verified Answer -->
  <div style="display:flex; align-items:flex-start; gap:10px; margin-bottom:10px;">
    <div style="width:28px; height:28px; border-radius:50%; background:linear-gradient(135deg, #3B82F6 0%, #2F5BEA 100%); display:flex; align-items:center; justify-content:center; color:#FFFFFF; font-size:11px; flex-shrink:0;">
      🤖
    </div>
    <div style="flex:1;">
      <div style="height:10px; width:94%; background:#DBEAFE; border-radius:6px; margin-bottom:6px;"></div>
      <div style="height:10px; width:78%; background:#DBEAFE; border-radius:6px; margin-bottom:8px;"></div>
      <!-- Verified Citation Pill -->
      <div style="display:inline-flex; align-items:center; gap:5px; background:#F1F5F9; border:1px solid #E2E8F0; border-radius:6px; padding:2px 8px; font-size:9.5px; font-weight:600; color:#475569;">
        <span style="color:#2F5BEA;">📄</span> handbook.pdf (p. 3)
      </div>
    </div>
  </div>
</div>'''


# ==============================================================================
# 6. CURVED CONNECTOR ARROWS (ANIMATED FLOWING DASHES)
# ==============================================================================
CONNECTOR_ARROW_LEFT_SVG = '''<svg class="connector-arrow connector-arrow-left" width="80" height="50" viewBox="0 0 80 50" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path class="arrow-dash-flow" d="M8 25C28 10 52 38 72 25" stroke="#94A3B8" stroke-width="1.8" stroke-dasharray="4 4" stroke-linecap="round"/>
  <path d="M72 25L63 20M72 25L64 29" stroke="#64748B" stroke-width="1.8" stroke-linecap="round"/>
</svg>'''

CONNECTOR_ARROW_RIGHT_SVG = '''<svg class="connector-arrow connector-arrow-right" width="80" height="50" viewBox="0 0 80 50" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path class="arrow-dash-flow" d="M8 25C28 38 52 10 72 25" stroke="#94A3B8" stroke-width="1.8" stroke-dasharray="4 4" stroke-linecap="round"/>
  <path d="M72 25L63 20M72 25L64 29" stroke="#64748B" stroke-width="1.8" stroke-linecap="round"/>
</svg>'''
