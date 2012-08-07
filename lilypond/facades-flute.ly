%{

Facades
Flute Part

%}

\version "2.14.1"
%\include "english.ly"
#(set-default-paper-size "letter")

\header {
  title = "No. 5 Facades"
  subtitle = "from Glassworks"
  composer = "Philip Glass"
  piece = "Flute 1 & 2 (Transcribed from the Soprano Sax part)"
}

\layout {
  \context {
    \Staff \RemoveEmptyStaves
  }
}


\score {
  \new StaffGroup \relative c'' {
    <<
      \new Staff \with { instrumentName = #"Flute 1" } {
        \clef treble
        \time 12/8
        \set Staff.midiInstrument = #"flute"
        \tempo 4=89

        % Page 1 (49)
        r1. | r |

        % -----------------------------------------
        % Repetition 1 & 2
        % XXX note: tacit first time
        \mark \default
        e | e |
        \repeat volta 2 {
          r2. f~| f~ f4 f-_ f-_ |
          e1.~ | e2. r |
        }
        \repeat volta 2 {
          r d~ | d4. r d2. |
          e1.~ | e2. r|
        }
        r2. r4. d~ | d2.~ d4 d d |
        \once \override Score.RehearsalMark #'break-visibility = #end-of-line-visible
        \once \override Score.RehearsalMark #'self-alignment-X = #RIGHT
        \mark "D.C."
        \break
        % Page 2 (50)
        c2.~ c4. c4.~ | c2. r |

        % -----------------------------------------
        % Repetition 3
        \mark \default
        r2. e~ | e r8 a,( b c d e |
        \repeat volta 2 {
          f1.~)  | f2. r8 aes,( bes c d ees |
          e!1.~) | e2. r8 a,( b c d e |
        }
        \repeat volta 2 {
          d1.~)  | d2. r8 aes( bes c d ees |
          e!1.~) | e2.~ e4. r |
        }
        % Page 3 (51)
        d1. | d2. r8 aes( bes c d ees |
        e!2.~) e4. c~ | c2.~ c4. r |

        % -----------------------------------------
        % Repetition 4
        \mark \default
        c8( a c) e( dis e) c( a  c) e( dis e) |
        c(  a c) e( dis e) c  a( b  c  d   e) |
        \repeat volta 2 {
          c( aes c) f( e   f) c( aes  c)  f( e   f)   |
          c( aes c) f( e   f) c  aes( bes c  d   ees) |
          c( a   c) e( dis e) c( a    c)  e( dis e)   |
          c( a   c) e( dis e) c  a(   b   c  d   e)   |
        }
        % Page 4 (52)
        \repeat volta 2 {
          d( bes d) f( e   f) d( bes d) f( e   f) |
          d( bes d) f( e   f) d( bes d) f( e   f) |
          c( a   c) e( dis e) c( a   c) e( dis e) |
          c( a   c) e( dis e) c  a(  b  c  d   e) |
        }
        d( bes d) f( e f) d( bes  d)  f( e f)   |
        d( bes d) f( e f) d  aes( bes c  d ees) |
        c( a   c) e( dis e) c( a   c) e( dis e) |
        c( a   c) e( dis e) c( a   c) e( dis e) |

        % -----------------------------------------
        % Repetition 5
        % Page 5 (53)
        \mark \default
        e1.~ | e2. r8 a,( b c d e |
        \repeat volta 2 {
          f1.~) | f2.~ f4. r |
          e1.~  | e2. r8 a,( b c d e |
        }
        \repeat volta 2 {
          d1.~) | d2. r8 aes( bes c d ees |
          e2.~) e4. c~ | c1. |
        }
        % Page 6 (54)
        r2. d~ | d d4-_ d-_ d-_ |
        c1.~ | c2. r |

        % -----------------------------------------
        % Repetition 6
        \mark \default
        a1.~ | a2.~ a4. r |
        \repeat volta 2 {
          aes1.~ | aes2. bes4. aes |
          a!1.~ | a2.~ a4. r |
        }
        \repeat volta 2 {
          f1.~ | f4. r d' f, |
        % Page 7 (55)
          e1.~ | e2. r |
        }
        f1. | bes2. d |
        e1.~ | e |

        % -----------------------------------------
        % Coda
        \mark \default
        \repeat volta 2 {
          e~ | e |
          f~ | f |
        }
        \repeat volta 4 {
          e~^\markup { "Repeat 4 times" } | e |
        }
      }

      \new Staff \with { instrumentName = #"Flute 2" } {
        \clef treble
        \time 12/8
        \set Staff.midiInstrument = #"viola"
        \tempo 4=89

        r1. | r
        % Repetition 1 & 2
        \mark \default
        \repeat unfold 2 { r }
        \repeat volta 2 { \repeat unfold 4 { r } }
        \repeat volta 2 { \repeat unfold 4 { r } }
        \repeat unfold 4 { r }
        % Repetition 3
        \mark \default
        \repeat unfold 2 { r }
        \repeat volta 2 { \repeat unfold 4 { r } }
        \repeat volta 2 { \repeat unfold 4 { r } }
        % Page 3 (51)
        \repeat unfold 4 { r }

        % -----------------------------------------
        % Repetition 4
        \mark \default
        e,8( c e) a( e a) e( c e) a( c a) |
        e(   c e) a( e a) e a( b c b a) |
        \repeat volta 2 {
          f( c f) aes( f aes) f( c    f)  aes( f   aes) |
          f( c f) aes( f aes) f  aes( bes c    bes aes) |
          e( c e) a( e a) e( c  e) a( c a) |
          e( c e) a( e a) e  a( b  c  b a) |
        }
        % Page 4 (52)
        \repeat volta 2 {
          f( d f) bes( f bes) f( d f) bes( f bes) |
          f( d f) bes( f bes) f( d f) bes( f bes) |
          e,( c e) a( e a) e( c e) a( c a) |
          e(  c e) a( e a) e a( b c b a) |
        }
        f( d f) bes( f bes) f( d f) bes( f bes) |
        f( d f) bes( f bes) f aes( bes c bes aes) |
        e( c e) a( e a) e( c e) a( c a) |
        e(  c e) a( e a) e a( b c b a) |

        % -----------------------------------------
        % Repetition 5
        % Page 5 (53)
        \mark \default
        e( c e) a( gis a) e( c  e) a( gis a) |
        e( c e) a( gis a) e  a( b  c  b   a) |
        \repeat volta 2 {
          f( c f) aes( f aes) f( c f) aes( f aes) |
          f( c f) aes( f aes) f( c f) aes( f aes) |
          e( c e) a( gis a) e( c  e) a( gis a) |
          e( c e) a( gis a) e  a( b  c  b   a) |
        }
        \repeat volta 2 {
          f( d f) bes( a bes) f( d f) bes( a bes) |
          f( d f) bes( a bes) f aes( bes c bes aes) |
          e( c e) a( gis a) e( c  e) a( gis a) |
          e( c e) a( gis a) e( c  e) a( gis a) |
        }
        r2. d,~ | d d4-_ d-_ d-_ |
        % Page 6 (54)
        c1.~ | c2. r |

        % Repetition 6
        \mark \default
        \repeat unfold 2 { r1. }
        \repeat volta 2 { \repeat unfold 4 { r } }
        \repeat volta 2 { \repeat unfold 4 { r } }
        \repeat unfold 4 { r }
        % Coda
        \mark \default
        \repeat volta 2 { \repeat unfold 4 { r } }
        \repeat volta 4 { \repeat unfold 2 { r } }
      }
    >>
  }

  \layout { }
  \midi { }
}

