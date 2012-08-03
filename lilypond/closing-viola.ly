%{

 $Header: /u/yuanc/testbed/lilypond/RCS/closing-viola.ly,v 1.4 2012/08/01 19:43:54 yuanc Exp $

%}

\version "2.14.1"

\header {
  title = "No. 6 Closing"
  subtitle = "from Glassworks"
  composer = "Philip Glass"
  piece = "Viola"
}

\relative c' {
  \clef alto

  % Page 1 (56)
  \repeat volta 4 {
    aes8\mp( c) aes( c) aes( c) aes( c) |
    aes( c) aes( c) aes( c) aes( c) |
    g( bes) g( bes) g( bes) g( bes)
  } \alternative {
    { g( bes) g( bes) g( bes) g( bes) }
    { g( bes) g( bes) g( bes) g( bes) }
  }
  \bar "||"
  \break

  % Page 2 (57)
  \repeat volta 4 {
    \times 2/3 { c8\mp^\markup {"Last D.C., play twice only"}( f c) }
    \times 2/3 { f( c f) }
    \times 2/3 { c( f c) }
    \times 2/3 { f( c f) } |

    \times 2/3 { d( f d) } \times 2/3 { f( d f) }
    \times 2/3 { d( f d) } \times 2/3 { f( d f) } |

    \times 2/3 { bes,( ees bes) } \times 2/3 { ees( bes ees) }
    \times 2/3 { bes( ees bes) } \times 2/3 { ees( bes ees) } |

  } \alternative {
    {
      \times 2/3 { c( ees c) } \times 2/3 { ees( c ees) }
      \times 2/3 { c( ees c) } \times 2/3 { ees( c ees) } |
    }
    {
      \times 2/3 { bes( ees bes) } \times 2/3 { ees( bes ees) }
      \times 2/3 { bes( ees bes) } \times 2/3 { ees( bes ees^\markup {"Fine"}) } |
    }
  }
  \bar "||"
  \break

  % Page 3 (58)
  \repeat volta 3 {
    bes8( d) bes( d) bes( d) bes( d) |
    bes( d) bes( d) bes( d) bes( d) |
    c( ees) c( ees) c\<( ees) c( ees) |
  } \alternative {
    { c\>( ees) c( ees) c( ees) c( ees\!) }
    { c\!( ees) c( ees) c( ees) c( ees) }
  }
  \bar "||"
  \break

  % Page 4 (59)
  bes-\markup { \italic sub \dynamic p }( d) bes( d) bes( d) bes( d) |
  bes( d) bes( d) bes( d) bes( d) |
  bes( d) bes( d) bes( d) bes( d) |
  bes( d) bes( d) bes( d) bes( d) |

  \once \override Score.RehearsalMark #'break-visibility = #end-of-line-visible
  \once \override Score.RehearsalMark #'self-alignment-X = #RIGHT
  \mark "D.C. Twice al Fine"
  \bar "||"
  \break
}
