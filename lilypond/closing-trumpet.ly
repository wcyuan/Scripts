%{
  Closing
  Trumpet Part
%}

\version "2.14.1"

\header {
  title = "No. 6 Closing"
  subtitle = "from Glassworks"
  composer = "Philip Glass"
  piece = "Bb Trumpet (transcribed from Horn)"
}

\relative c'' {
  % Page 1 (56)
  \repeat volta 4 {
    r2 bes\<\p~ | bes1\> | r2\! a\< |
  } \alternative {
    { bes2.\> r4\! }
    { a1 }
  }
  \break

  % Page 2 (57)
  \repeat volta 4 {
    d,1\mp^\markup {"Last D.C., play twice only"} | e |
  } \alternative {
    { f  | a }
    { f~ | f }
  }
  \once \override Score.RehearsalMark #'break-visibility = #end-of-line-visible
  \once \override Score.RehearsalMark #'self-alignment-X = #RIGHT
  \mark "Fine"
  \break

  % Page 3 (58)
  % cresc to mp and back in last two bars
  % mf on alternate ending
  \repeat volta 3 {
    r2 bes~ | bes1 | bes\< |
  } \alternative {
    { c\mp\> }
    { c2\mf bes }
  }
  \break

  % Page 4 (59)
  % sub p
  a1-\markup { \italic sub \dynamic p }~ | a1 | bes | c | \bar "||"

  \once \override Score.RehearsalMark #'break-visibility = #end-of-line-visible
  \once \override Score.RehearsalMark #'self-alignment-X = #RIGHT
  \mark "D.C. Twice al Fine"
  \break
}
